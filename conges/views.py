from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decoraters import role_required
from .forms import DemandeCongeForm, NouvelEmployeForm,MissionCreateForm, MissionCorrectionForm
from .models import DemandeConge, Employe, Mission
from .models import Departement, Direction
from django.shortcuts import get_object_or_404
from django.contrib import messages 
from django.contrib.auth.models import User
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.utils import timezone


@login_required
def home(request): 
    return render(request,'conges/home.html')

@login_required
@role_required('CD')
def test_chef(request):
    return render(request,'conges/home.html')
@login_required
def nouvelle_demande(request):
    if request.method == 'POST':
        form = DemandeCongeForm(request.POST, request.FILES)
        if form.is_valid():
            demande = form.save(commit=False)
            employe = getattr(request.user, 'employe', None)
            if not employe:
                messages.error(request, "Aucun profil employé associé à ce compte.")
                return redirect('home')

            conflits_remplacement = DemandeConge.objects.filter(
                name_remplacent=employe,
                statue__in=['VA', 'EN_ATT_VA', 'EN_ATT_RMP'],
                dateDebut__lte=demande.dateFin,
                dateFin__gte=demande.dateDebut
            )
            if conflits_remplacement.exists():
                messages.error(request, "Vous êtes déjà remplaçant sur cette période.")
                return render(request, 'conges/nouvelle_demande.html', {'form': form})

            is_brouillon = request.POST.get('action') == 'brouillon'

            if not is_brouillon:
                demande_en_attente = DemandeConge.objects.filter(
                    name_employee=employe,
                    statue__in=['EN_ATT_RMP', 'EN_ATT_VA'],
                ).exists()

                if demande_en_attente:
                    messages.error(request, "Vous avez déjà une demande de congé en attente.")
                    return render(request, 'conges/nouvelle_demande.html', {'form': form})

            demande.name_employee = employe
            demande.statue = 'BR' if is_brouillon else 'EN_ATT_RMP'
            jours = (demande.dateFin - demande.dateDebut).days
            demande.Numbrejours = jours
            demande.save()
            return redirect('mes_demandes')
    else:
        form = DemandeCongeForm()
    return render(request, 'conges/nouvelle_demande.html', {'form': form})
@login_required
def mes_demandes(request):
    demandes = DemandeConge.objects.filter(name_employee=request.user.employe).order_by('dateCreation')
    return render(request, 'conges/mes_demandes.html', {'demandes' : demandes})  
 
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
                return redirect('demandes_remplacent')
            demande.statue = 'EN_ATT_VA'
            demandeur_role = demande.name_employee.get_role()
         
            if demandeur_role == 'CG' :
             demande.niveau_validation = 'CD'
            elif demandeur_role == 'CD' :
             demande.niveau_validation = 'DIR'   
            elif demandeur_role == 'DIR':
             demande.statue = 'VA'   # auto-validated, no niveau_validation needed
            else:
             demande.niveau_validation = 'CG'
          
        elif action == 'refuser' : 
            demande.statue = 'REF'
            
        demande.save()
        return redirect('demandes_remplacent')
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
        elif action == 'refuser':
            demande.statue = 'REF'

        demande.commentaire = commentaire
        demande.save()
        return redirect('demandes_a_valider')

    return render(request, 'conges/valider_demande.html', {'demande': demande})

@login_required
def mon_solde(request):
    employe =getattr(request.user, 'employe', None)
    if not employe :
     messages.error(request, "Aucun profil employé associé à ce compte.")
     return redirect('home')

    solde=getattr(employe, 'solde', None)
    if not solde :
      messages.error(request, "Aucun profil employé associé à ce compte.")
      return redirect('home')
 
    return render(request, 'conges/mon_solde.html', {'solde': solde})
 
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
    if request.method == 'POST':
        form = NouvelEmployeForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )

            Employe.objects.create(
                user=user,
                nom=form.cleaned_data['nom'],
                fonction=form.cleaned_data['fonction']
            )

            messages.success(request, 'employe créé avec success')
            return redirect('gerer_employes')
    else:
        form = NouvelEmployeForm()

    employes = Employe.objects.all().order_by('nom')
    return render(request, 'conges/gerer_employes.html', {'form': form, 'employes': employes})

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

    employes = Employe.objects.filter(role__groupe__depratement=departement).distinct()

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
    })
    
    from django.utils import timezone

@login_required
@role_required('DIR')
def directeur_dashboard(request):
    directeur = request.user.employe
    direction = Direction.objects.filter(directeur=directeur).first()

    if not direction:
        messages.error(request, "Aucune direction associée à ce compte.")
        return redirect('home')

    employes = Employe.objects.filter(
        role__groupe__depratement__direction=direction
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