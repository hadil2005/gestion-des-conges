from django import forms
from .models import DemandeConge

class DemandeCongeForm(forms.ModelForm):
    class Meta:
        model = DemandeConge
        fields = ['name_remplacent','dateDebut','dateFin','motif','piece_Joine','type_conge']
        widgets = { 
                   'dateDebut':forms.DateInput(attrs={'type':'date'}),
                   'dateFin':forms.DateInput(attrs={'type':'date'})
                   }