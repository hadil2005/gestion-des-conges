from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decoraters import role_required
from .forms import DemandeCongeForm, NouvelEmployeForm,MissionCreateForm, MissionCorrectionForm, DirectionForm, DepartementForm, GroupeForm, SoldeForm
from .models import DemandeConge, Employe, Mission, Solde, Notification, Role, EmployeRole, Groupe
from .models import Departement, Direction
from django.shortcuts import get_object_or_404
from django.contrib import messages 
from django.contrib.auth.models import User
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.db.models import Q
import json


def get_validateur(employe, niveau):
    """Resolve the actual chef Employe for a given employee's team at a given niveau."""
    role_obj = employe.role.first()
    if not role_obj:
        return None

    if niveau == 'CG':
        return role_obj.groupe.Chef_de_groupe if role_obj.groupe else None
    elif niveau == 'CD':
        dep = role_obj.groupe.depratement if role_obj.groupe else role_obj.dep
        return dep.Chef_de_departement if dep else None
    elif niveau == 'DIR':
        direction = None
        if role_obj.groupe:
            direction = role_obj.groupe.depratement.direction
        elif role_obj.dep:
            direction = role_obj.dep.direction
        return direction.directeur if direction else None
    return None

def sync_chef_role(employe, role_code, groupe=None, departement=None, direction=None):
    """Create or update this employee's EmployeRole to match a chef assignment."""
    role_obj, _ = Role.objects.get_or_create(name=role_code)
    existing = employe.role.first()
    if existing:
        existing.role = role_obj
        existing.groupe = groupe
        existing.dep = departement
        existing.direction = direction
        existing.save()
    else:
        EmployeRole.objects.create(
            employe=employe, role=role_obj,
            groupe=groupe, dep=departement, direction=direction
        )
@login_required
def home(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('login')

    solde = getattr(employe, 'solde', None)

    demande_courante = DemandeConge.objects.filter(
        name_employee=employe,
        statue__in=['EN_ATT_RMP', 'EN_ATT_VA']
    ).order_by('-dateCreation').first()

    remplacements_en_attente = DemandeConge.objects.filter(
        name_remplacent=employe,
        statue='EN_ATT_RMP'
    ).order_by('-dateCreation')

    notifications_recentes = Notification.objects.filter(
        employe=employe
    ).order_by('-dateCreation', '-id')[:5]

    demandes_a_valider = []
    role = employe.get_role()
    if role in ['CG', 'CD', 'DIR']:
        demandes_a_valider = [
            d for d in DemandeConge.objects.filter(niveau_validation=role, statue='EN_ATT_VA')
            if employe.meme_equipe(d.name_employee)       
        ]
    notifications_recentes = Notification.objects.filter(
    employe=employe 
    ).order_by('-dateCreation', '-id')[:5]

    demandes_a_valider = []
    role = employe.get_role()
    if role in ['CG', 'CD', 'DIR']:
     demandes_a_valider = [
        d for d in DemandeConge.objects.filter(niveau_validation=role, statue='EN_ATT_VA')
        if employe.meme_equipe(d.name_employee)
    ]
    notifications_non_lues = Notification.objects.filter(employe=employe, lu=False).count()

    return render(request, 'conges/home.html', {
    'solde': solde,
    'demande_courante': demande_courante,
    'remplacements_en_attente': remplacements_en_attente,
    'notifications_recentes': notifications_recentes,
    'demandes_a_valider': demandes_a_valider,
    'notifications_non_lues': notifications_non_lues,
})
@login_required
def nouvelle_demande(request, demande_id=None):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    instance = None
    if demande_id:
        instance = get_object_or_404(DemandeConge, id=demande_id, name_employee=employe, statue='BR')

    if request.method == 'POST':
        form = DemandeCongeForm(request.POST, request.FILES, instance=instance, employe=employe)
        if form.is_valid():
            demande = form.save(commit=False)

            conflits_remplacement = DemandeConge.objects.filter(
                name_remplacent=employe,
                statue__in=['VA', 'EN_ATT_VA', 'EN_ATT_RMP'],
                dateDebut__lte=demande.dateFin,
                dateFin__gte=demande.dateDebut
            ).exclude(id=demande.id if instance else None)
            if conflits_remplacement.exists():
                messages.error(request, "Vous êtes déjà remplaçant sur cette période.")
                return render(request, 'conges/nouvelle_demande.html', {'form': form})

            is_brouillon = request.POST.get('action') == 'brouillon'

            if not is_brouillon:
                demande_en_attente = DemandeConge.objects.filter(
                    name_employee=employe,
                    statue__in=['EN_ATT_RMP', 'EN_ATT_VA'],
                ).exclude(id=demande.id if instance else None).exists()

                if demande_en_attente:
                    messages.error(request, "Vous avez déjà une demande de congé en attente.")
                    return render(request, 'conges/nouvelle_demande.html', {'form': form})

            demande.name_employee = employe
            demande.statue = 'BR' if is_brouillon else 'EN_ATT_RMP'
            jours = (demande.dateFin - demande.dateDebut).days
            demande.Numbrejours = jours
            demande.save()

            if not is_brouillon:
                Notification.objects.create(
                    employe=demande.name_remplacent,
                    demande=demande,
                    type_notif='DMD',
                    message=f"{employe.nom} vous a proposé comme remplaçant pour sa demande de congé.",
                )

            return redirect('mes_demandes')
    else:
        form = DemandeCongeForm(instance=instance, employe=employe)

    return render(request, 'conges/nouvelle_demande.html', {'form': form})

@login_required
def mes_demandes(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    demandes = DemandeConge.objects.filter(name_employee=employe).order_by('-dateCreation')
    return render(request, 'conges/mes_demandes.html', {'demandes': demandes})


@login_required
@role_required('CD')
def test_chef(request):
    return render(request,'conges/home.html')

@login_required
def demandes_remplacent(request):
  demandes=DemandeConge.objects.filter(
      name_remplacent=request.user.employe,
      statue='EN_ATT_RMP'
      ).order_by('dateCreation')
  return render (request,'conges/demandes_remplacent.html', {'demandes': demandes})

@login_required
def accepter_remplacent(request, demande_id):
    demande = get_object_or_404(DemandeConge, id=demande_id, name_remplacent=request.user.employe)
    if request.method == 'POST' :
        action = request.POST.get('action')
        
        if action == 'accepter':
            conflits = DemandeConge.objects.filter(
                name_employee=request.user.employe,
                statue__in=['VA', 'EN_ATT_VA', 'EN_ATT_RMP'],
                dateDebut__lte=demande.dateFin,
                dateFin__gte=demande.dateDebut
            )
            if conflits.exists():
             messages.error(request, "Vous n'êtes pas disponible sur cette période.")
             return redirect('home')

            demande.statue = 'EN_ATT_VA'
            demandeur_role = demande.name_employee.get_role()

            if demandeur_role == 'CG':
                demande.niveau_validation = 'CD'
            elif demandeur_role == 'CD':
                demande.niveau_validation = 'DIR'
            elif demandeur_role == 'DIR' or demandeur_role == 'DRH':
                demande.statue = 'VA'
            else:
                demande.niveau_validation = 'CG'

            demande.save()

            Notification.objects.create(
                employe=demande.name_employee,
                demande=demande,
                type_notif='UPD',
                message=f"{demande.name_remplacent.nom} a accepté d'être votre remplaçant.",
            )

            if demande.statue == 'EN_ATT_VA':
                validateur = get_validateur(demande.name_employee, demande.niveau_validation)
                if validateur:
                    Notification.objects.create(
                        employe=validateur,
                        demande=demande,
                        type_notif='DMD',
                        message=f"Nouvelle demande de congé à valider pour {demande.name_employee.nom}.",
                    )

        elif action == 'refuser':
            demande.statue = 'REF'
            demande.save()
            Notification.objects.create(
                employe=demande.name_employee,
                demande=demande,
                type_notif='UPD',
                message=f"{demande.name_remplacent.nom} a refusé d'être votre remplaçant.",
            )
            
        demande.save()
        return redirect('home')
    return render(request, 'conges/accepter_remplacent.html', {'demande': demande})  
  

@login_required
@role_required('CG','CD','DIR')
def demandes_a_valider(request):
    chef = request.user.employe
    role = chef.get_role()
    demandes = DemandeConge.objects.filter(
        statue='EN_ATT_VA',
        niveau_validation=role
    ).order_by('dateCreation')
    demandes = [demande for demande in demandes if chef.meme_equipe(demande.name_employee)]
    return render(request, 'conges/demandes_a_valider.html', {'demandes': demandes}) 
    
@login_required
@role_required('CG', 'CD', 'DIR')
def valider_demande(request, demande_id):
    demande = get_object_or_404(DemandeConge, id=demande_id)
    chef = request.user.employe
    role = chef.get_role()

    if demande.niveau_validation != role or not chef.meme_equipe(demande.name_employee):
        messages.error(request, "Cette demande n'est pas à votre niveau.")
        return redirect('demandes_a_valider')

    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        demande.commentaire = commentaire

        if action == 'valider':
            if demande.niveau_validation == 'CG':
                demande.niveau_validation = 'CD'
            elif demande.niveau_validation == 'CD':
                demande.niveau_validation = 'DIR'
            elif demande.niveau_validation == 'DIR':
                demande.statue = 'VA'
                solde = demande.name_employee.solde
                solde.solde_consomme += demande.Numbrejours
                solde.save()

            demande.save()

            if demande.statue == 'VA':
                Notification.objects.create(
                    employe=demande.name_employee,
                    demande=demande,
                    type_notif='UPD',
                    message="Votre demande de congé a été validée.",
                )
            else:
                Notification.objects.create(
                    employe=demande.name_employee,
                    demande=demande,
                    type_notif='UPD',
                    message=f"Votre demande passe à l'étape de validation suivante ({demande.get_niveau_validation_display()}).",
                )
                validateur = get_validateur(demande.name_employee, demande.niveau_validation)
                if validateur:
                    Notification.objects.create(
                        employe=validateur,
                        demande=demande,
                        type_notif='DMD',
                        message=f"Nouvelle demande de congé à valider pour {demande.name_employee.nom}.",
                    )

        elif action == 'refuser':
            demande.statue = 'REF'
            demande.save()
            Notification.objects.create(
                employe=demande.name_employee,
                demande=demande,
                type_notif='UPD',
                message=f"Votre demande de congé a été refusée par {role.label}.",
            )

        return redirect('home')

    return render(request, 'conges/valider_demande.html', {'demande': demande})
@login_required
def mon_solde(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    solde = getattr(employe, 'solde', None)
    if not solde:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    solde_form = None
    if employe.get_role() == 'DRH':
        if request.method == 'POST':
            solde_form = SoldeForm(request.POST)
            if solde_form.is_valid():
                solde_form.save()
                messages.success(request, 'Solde assigné avec succès')
                return redirect('mon_solde')
        else:
            solde_form = SoldeForm()

    return render(request, 'conges/mon_solde.html', {
        'solde': solde,
        'solde_form': solde_form,
    })
@login_required
def detail_demande(request, demande_id):
    demande = get_object_or_404(DemandeConge, id=demande_id, name_employee=request.user.employe)
    return render(request, 'conges/detail_demande.html', {'demande': demande})

@login_required
@role_required('DRH')
def recherche_demandes(request):
    demandes = DemandeConge.objects.all().order_by('dateCreation')

    nom = request.GET.get('nom')
    departement = request.GET.get('departement')
    direction = request.GET.get('direction')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    statut = request.GET.get('statut')
    type_conge = request.GET.get('type_conge')

    if nom:
        demandes = demandes.filter(name_employee__nom__icontains=nom)

    if departement:
        demandes = demandes.filter(name_employee__role__dep__id=departement)

    if direction:
        demandes = demandes.filter(name_employee__role__direction__id=direction)

    if date_debut:
        demandes = demandes.filter(dateFin__gte=date_debut)

    if date_fin:
        demandes = demandes.filter(dateDebut__lte=date_fin)

    if statut:
        demandes = demandes.filter(statue=statut)

    if type_conge:
        demandes = demandes.filter(type_conge=type_conge)

    return render(request, 'conges/recherche_demandes.html', {
        'demandes': demandes,
        'departements': Departement.objects.all(),
        'directions': Direction.objects.all(),
        'statut_choices': DemandeConge.TYPE_STATUE,
        'nom': nom or '',
        'departement': departement or '',
        'direction': direction or '',
        'date_debut': date_debut or '',
        'date_fin': date_fin or '',
        'statut': statut or '',
        'type_conge': type_conge or '',
    
    })
 
@login_required
@role_required('DRH')
def gerer_employes(request):
    form = NouvelEmployeForm()
    direction_form = DirectionForm()
    departement_form = DepartementForm()
    groupe_form = GroupeForm()
 
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
 
        if form_type == 'employe':
            form = NouvelEmployeForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password']
                )
                employe = Employe.objects.create(
                    user=user,
                    nom=form.cleaned_data['nom'],
                    fonction=form.cleaned_data['fonction']
                )
                role_code = form.cleaned_data['role']
                role_obj, _ = Role.objects.get_or_create(name=role_code)
 
                groupe = form.cleaned_data.get('groupe')
                departement = form.cleaned_data.get('departement')
                direction = form.cleaned_data.get('direction')
 
                if role_code in ['ES', 'CG']:
                    departement = groupe.depratement if groupe else None
                    direction = departement.direction if departement else None
                elif role_code == 'CD':
                    groupe = None
                    direction = departement.direction if departement else None
                elif role_code == 'DIR':
                    groupe = None
                    departement = None
                elif role_code == 'DRH':
                    groupe = None
                    departement = None
                    direction = None
 
                EmployeRole.objects.create(
                    employe=employe,
                    role=role_obj,
                    groupe=groupe,
                    dep=departement,
                    direction=direction,
                )
                messages.success(request, 'Employé créé avec succès')
                return redirect('gerer_employes')
 
        elif form_type == 'direction':
            direction_form = DirectionForm(request.POST)
            if direction_form.is_valid():
                direction = direction_form.save()
                if direction.directeur:
                    sync_chef_role(direction.directeur, 'DIR', direction=direction)
                messages.success(request, 'Direction créée avec succès')
                return redirect('gerer_employes')
 
        elif form_type == 'departement':
            departement_form = DepartementForm(request.POST)
            if departement_form.is_valid():
                departement = departement_form.save()
                if departement.Chef_de_departement:
                    sync_chef_role(
                        departement.Chef_de_departement,
                        'CD',
                        departement=departement,
                        direction=departement.direction
                    )
                messages.success(request, 'Département créé avec succès')
                return redirect('gerer_employes')
 
        elif form_type == 'groupe':
            groupe_form = GroupeForm(request.POST)
            if groupe_form.is_valid():
                groupe = groupe_form.save()
                if groupe.Chef_de_groupe:
                    sync_chef_role(
                        groupe.Chef_de_groupe,
                        'CG',
                        groupe=groupe,
                        departement=groupe.depratement,
                        direction=groupe.depratement.direction
                    )
                messages.success(request, 'Groupe créé avec succès')
                return redirect('gerer_employes')
 
 
    return render(request, 'conges/gerer_employes.html', {
        'form': form,
        'direction_form': direction_form,
        'departement_form': departement_form,
        'groupe_form': groupe_form,
    })
@login_required
@role_required('DRH')
def liste_employes(request):
    employes = Employe.objects.all().order_by('nom')

    nom = request.GET.get('nom')
    direction_id = request.GET.get('direction')
    departement_id = request.GET.get('departement')

    if nom:
        employes = employes.filter(nom__icontains=nom)

    if direction_id:
        employes = employes.filter(
            Q(role__direction__id=direction_id) |
            Q(role__dep__direction__id=direction_id) |
            Q(role__groupe__depratement__direction__id=direction_id)
        ).distinct()

    if departement_id:
        employes = employes.filter(
            Q(role__dep__id=departement_id) |
            Q(role__groupe__depratement__id=departement_id)
        ).distinct()

    return render(request, 'conges/liste_employes.html', {
        'employes': employes,
        'nom': nom or '',
        'directions': Direction.objects.all(),
        'departements': Departement.objects.all(),
        'direction_id': direction_id or '',
        'departement_id': departement_id or '',
    })


@login_required
@role_required('DRH')
def modifier_employe_role(request, employe_id):
    employe = get_object_or_404(Employe, id=employe_id)
    existing_role = employe.role.first()

    if request.method == 'POST':
        role_code = request.POST.get('role')
        groupe_id = request.POST.get('groupe')
        departement_id = request.POST.get('departement')
        direction_id = request.POST.get('direction')

        groupe = Groupe.objects.filter(id=groupe_id).first() if groupe_id else None
        departement = Departement.objects.filter(id=departement_id).first() if departement_id else None
        direction = Direction.objects.filter(id=direction_id).first() if direction_id else None

        if role_code in ['ES', 'CG']:
            departement = groupe.depratement if groupe else None
            direction = departement.direction if departement else None
        elif role_code == 'CD':
            groupe = None
            direction = departement.direction if departement else None
        elif role_code == 'DIR':
            groupe = None
            departement = None
        elif role_code == 'DRH':
            groupe = None
            departement = None
            direction = None

        sync_chef_role(employe, role_code, groupe=groupe, departement=departement, direction=direction)
        sync_chef_role(employe, role_code, groupe=groupe, departement=departement, direction=direction)

        if role_code == 'CG' and groupe:
         groupe.Chef_de_groupe = employe
         groupe.save()
        elif role_code == 'CD' and departement:
         departement.Chef_de_departement = employe
         departement.save()
        elif role_code == 'DIR' and direction:
         direction.directeur = employe
         direction.save()
         messages.success(request, f"Rôle de {employe.nom} mis à jour.")
         return redirect('liste_employes')

    return render(request, 'conges/modifier_employe_role.html', {
        'employe': employe,
        'existing_role': existing_role,
        'role_choices': Role.ROLE_CHOICES,
        'groupes': Groupe.objects.all(),
        'departements': Departement.objects.all(),
        'directions': Direction.objects.all(),
    })


@login_required
@role_required('DRH')
def supprimer_employe(request, employe_id):
    employe = get_object_or_404(Employe, id=employe_id)
    if request.method == 'POST':
        nom = employe.nom
        if employe.user:
            employe.user.delete()
        employe.delete()
        messages.success(request, f"{nom} a été supprimé.")
        return redirect('liste_employes')
    return render(request, 'conges/supprimer_employe.html', {'employe': employe})

@login_required
def rapport_solde_historique(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    solde = getattr(employe, 'solde', None)
    demandes = DemandeConge.objects.filter(name_employee=employe).order_by('dateCreation')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_{employe.id}.pdf"'

    p = canvas.Canvas(response)
    y = 800

    p.drawString(100, y, f"Rapport de {employe.nom}")
    y -= 30

    if solde:
        p.drawString(100, y, f"Solde annuel: {solde.solde_annuel}")
        y -= 20
        p.drawString(100, y, f"Solde récupération: {solde.solde_recuperation}")
        y -= 20
        p.drawString(100, y, f"Solde consommé: {solde.solde_consomme}")
        y -= 20
        p.drawString(100, y, f"Solde actuel: {solde.solde_actuel}")
        y -= 40
    else:
        p.drawString(100, y, "Aucun solde défini.")
        y -= 40

    p.drawString(100, y, "Historique des demandes:")
    y -= 25

    if not demandes:
     p.drawString(100, y, "Aucune demande de congé enregistrée.")
     y -= 20
    else:
     for demande in demandes:
        ligne = f"{demande.dateDebut} au {demande.dateFin} - {demande.get_statue_display()}"
        p.drawString(100, y, ligne)
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    return response

@login_required
@role_required('DIR','DRH')
def rapport_absences_form(request):
    departements= Departement.objects.all()
    return  render (request, 'conges/rapport_absences_form.html', {'departements': departements})

@login_required
@role_required('DIR','DRH')
def rapport_absences_departement(request):
    departement_id = request.GET.get('departement')
    date_debut = request.GET.get('date_debut')
    date_fin =  request.GET.get('date_fin')
    
    demandes = DemandeConge.objects.filter(statue='VA')
    
    if departement_id:
        demandes = demandes.filter(name_employee__role__dep__id=departement_id)
    if date_debut:
        demandes = demandes.filter(dateFin__gte=date_debut)
    if date_fin:
        demandes = demandes.filter(dateDebut__lte=date_fin)
        
    demandes = demandes.order_by('dateDebut')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_absences_departement.pdf"'

    p = canvas.Canvas(response)
    y = 800
    p.drawString(100, y, "Rapport d'absences par département")
    y -= 40

    if not demandes:
        p.drawString(100, y, "Aucune absence pour cette période/département.")
        y -= 20
    else:
        for demande in demandes:
            ligne = f"{demande.name_employee} - {demande.dateDebut} au {demande.dateFin}"
            p.drawString(100, y, ligne)
            y -= 20
            if y < 50:
                p.showPage()
                y = 800

    p.showPage()
    p.save()
    return response
 
@login_required
@role_required('DRH')
def mission_liste(request):
    missions = Mission.objects.select_related('employe').order_by('-dateDebut')
    return render(request, 'conges/mission_liste.html', {'missions': missions})

@login_required
@role_required('DRH')
def mission_creer(request):
    if request.method == 'POST':
        form = MissionCreateForm(request.POST)
        if form.is_valid():
            form.save()  # jours_recuperation auto-calculated in Mission.save()
            return redirect('mission_liste')
    else:
        form = MissionCreateForm()
    return render(request, 'conges/mission_creer.html', {'form': form})

@login_required
@role_required('DRH')
def mission_supprimer(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)
    if request.method == 'POST':
        mission.delete()
        messages.success(request, "Mission supprimée.")
        return redirect('mission_liste')
    return render(request, 'conges/mission_supprimer.html', {'mission': mission})

@login_required
@role_required('DRH')
def mission_corriger(request, mission_id):
    mission = get_object_or_404(Mission, id=mission_id)

    if request.method == 'POST':
        if 'decline' in request.POST:
            return redirect('mission_liste')

        form = MissionCorrectionForm(request.POST, instance=mission)
        if form.is_valid():
            form.save()
            return redirect('mission_liste')
    else:
        form = MissionCorrectionForm(instance=mission)

    return render(request, 'conges/mission_corriger.html', {'form': form, 'mission': mission})
@login_required
@role_required('CD')
def chef_dashboard(request):
    chef = request.user.employe
    departement = Departement.objects.filter(Chef_de_departement=chef).first()

    if not departement:
        messages.error(request, "Aucun département associé à ce compte.")
        return redirect('home')

    employes = Employe.objects.filter(
        Q(role__groupe__depratement=departement) |
        Q(role__dep=departement)
    ).distinct()

    tri = request.GET.get('tri', 'alphabetique')
    if tri == 'groupe':
        employes = employes.order_by('role__groupe__nom_de_groupe', 'nom')
    else:
        employes = employes.order_by('nom')

    demandes_en_attente = [
        d for d in DemandeConge.objects.filter(niveau_validation='CD', statue='EN_ATT_VA')
        if chef.meme_equipe(d.name_employee)
    ]

    demandes_departement = DemandeConge.objects.filter(name_employee__in=employes)

    stats = {
        'effectif': employes.count(),
        'en_attente': len(demandes_en_attente),
        'validees': demandes_departement.filter(statue='VA').count(),
        'refusees': demandes_departement.filter(statue='REF').count(),
    }

    return render(request, 'conges/chef_dashboard.html', {
        'departement': departement,
        'employes': employes,
        'demandes_en_attente': demandes_en_attente,
        'stats': stats,
        'tri': tri,
    })
    

@login_required
@role_required('DIR')
def directeur_dashboard(request):
    directeur = request.user.employe
    direction = Direction.objects.filter(directeur=directeur).first()

    if not direction:
        messages.error(request, "Aucune direction associée à ce compte.")
        return redirect('home')

    employes = Employe.objects.filter(
    Q(role__groupe__depratement__direction=direction) |
    Q(role__dep__direction=direction) |
    Q(role__direction=direction)
    ).distinct()

    today = timezone.localdate()
    absents = DemandeConge.objects.filter(
        name_employee__in=employes,
        statue='VA',
        dateDebut__lte=today,
        dateFin__gte=today,
    ).values('name_employee').distinct()

    demandes_en_attente = [
        d for d in DemandeConge.objects.filter(niveau_validation='DIR', statue='EN_ATT_VA')
        if directeur.meme_equipe(d.name_employee)
    ]

    effectif = employes.count()
    nb_absents = absents.count()

    stats = {
        'effectif': effectif,
        'absents': nb_absents,
        'en_attente': len(demandes_en_attente),
        'taux_absence': round((nb_absents / effectif * 100), 1) if effectif else 0,
    }

    return render(request, 'conges/directeur_dashboard.html', {
        'direction': direction,
        'stats': stats,
        'demandes_en_attente': demandes_en_attente,
    })
    
import json

@login_required
@role_required('DRH')
def drh_dashboard(request):
    employes = Employe.objects.all()
    today = timezone.localdate()

    en_conge_aujourdhui = DemandeConge.objects.filter(
        statue='VA',
        dateDebut__lte=today,
        dateFin__gte=today,
    ).values('name_employee').distinct()

    demandes = DemandeConge.objects.all()

    soldes = Solde.objects.select_related('employe').all()
    jours_consommes_total = sum(s.solde_consomme for s in soldes)
    solde_global = sum(s.solde_actuel for s in soldes)

    conges_par_direction_raw = (
        demandes.filter(statue='VA')
        .values('name_employee__role__direction__nom_de_direction')
        .annotate(total=Count('id'))
    )
    direction_labels = [item['name_employee__role__direction__nom_de_direction'] or 'N/A' for item in conges_par_direction_raw]
    direction_values = [item['total'] for item in conges_par_direction_raw]

    conges_par_departement_raw = (
        demandes.filter(statue='VA')
        .values('name_employee__role__dep__nom_de_departement')
        .annotate(total=Count('id'))
    )
    departement_labels = [item['name_employee__role__dep__nom_de_departement'] or 'N/A' for item in conges_par_departement_raw]
    departement_values = [item['total'] for item in conges_par_departement_raw]

    type_conge_dict = dict(DemandeConge.TYPE_CONGE_CHOICES)
    conges_par_type_raw = (
        demandes.filter(statue='VA')
        .values('type_conge')
        .annotate(total=Count('id'))
    )
    type_labels = [type_conge_dict.get(item['type_conge'], item['type_conge']) for item in conges_par_type_raw]
    type_values = [item['total'] for item in conges_par_type_raw]

    conges_par_mois_raw = (
        demandes.filter(statue='VA')
        .annotate(mois=TruncMonth('dateDebut'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
    )
    mois_labels = [item['mois'].strftime('%b %Y') for item in conges_par_mois_raw]
    mois_values = [item['total'] for item in conges_par_mois_raw]
    effectif_total = employes.count()
    en_conge_count = en_conge_aujourdhui.count()
    taux_absence = round((en_conge_count / effectif_total) * 100, 1) if effectif_total else 0

    stats = {
        'effectif_total': employes.count(),
        'en_conge_aujourdhui': en_conge_aujourdhui.count(),
        'en_attente': demandes.filter(statue='EN_ATT_VA').count(),
        'validees': demandes.filter(statue='VA').count(),
        'refusees': demandes.filter(statue='REF').count(),
        'jours_consommes_total': jours_consommes_total,
        'solde_global': solde_global,
        'taux_absence': taux_absence,

    }

    return render(request, 'conges/drh_dashboard.html', {
        'stats': stats,
        'direction_labels': json.dumps(direction_labels),
        'direction_values': json.dumps(direction_values),
        'departement_labels': json.dumps(departement_labels),
        'departement_values': json.dumps(departement_values),
        'type_labels': json.dumps(type_labels),
        'type_values': json.dumps(type_values),
        'mois_labels': json.dumps(mois_labels),
        'mois_values': json.dumps(mois_values),
        
    })
    
@login_required
def dashboard(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    role = employe.get_role()

    if role == 'DRH':
        return drh_dashboard(request)
    elif role == 'DIR':
        return directeur_dashboard(request)
    elif role == 'CD':
        return chef_dashboard(request)
    else:
        messages.error(request, "Aucun tableau de bord disponible pour votre rôle.")
        return redirect('home')
    
@login_required
def mes_notifications(request):
    employe = getattr(request.user, 'employe', None)
    if not employe:
        messages.error(request, "Aucun profil employé associé à ce compte.")
        return redirect('home')

    notifications = Notification.objects.filter(employe=employe).order_by('-dateCreation', '-id')
    notifications.filter(lu=False).update(lu=True)
    return render(request, 'conges/mes_notifications.html', {'notifications': notifications})