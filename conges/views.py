from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decoraters import role_required
from .forms import DemandeCongeForm
from .models import DemandeConge
from .models import Departement, Direction
from django.shortcuts import get_object_or_404
from django.contrib import messages 


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
            demande=form.save(commit=False) # hadi it saves things temprorally berk
            employe = getattr(request.user, 'employe', None)
            if not employe:
              messages.error(request, "Aucun profil employé associé à ce compte.")
              return redirect('home')
          
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
        return redirect('mes_demandes') # after the save it gets added to mes demandes w kda
    else :  
       form = DemandeCongeForm()  
    return render(request, 'conges/nouvelle_demande.html', {'form': form})  # if the person just visiting the form ( GET method )  

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