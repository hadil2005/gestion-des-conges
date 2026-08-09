from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decoraters import role_required
from .forms import DemandeCongeForm
from .models import DemandeConge

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
            demande.name_employee = request.user.employe
            if request.POST.get('action') == 'brouillon':
             demande.statue = 'BR'
            else:
             demande.statue = 'EN ATT'
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