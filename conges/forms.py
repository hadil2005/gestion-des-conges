from django import forms
from .models import DemandeConge, Mission
from django.contrib.auth.models import User


class DemandeCongeForm(forms.ModelForm):
    class Meta:
        model = DemandeConge
        fields = ['name_remplacent','dateDebut','dateFin','motif','piece_Joine','type_conge']
        widgets = { 
                   'dateDebut':forms.DateInput(attrs={'type':'date'}),
                   'dateFin':forms.DateInput(attrs={'type':'date'})
                   }

class NouvelEmployeForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    nom = forms.CharField(max_length=40)
    fonction = forms.CharField(max_length=40)
    
class MissionCreateForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['employe', 'dateDebut', 'dateFin', 'motif']
        widgets = {
            'dateDebut': forms.DateInput(attrs={'type': 'date'}),
            'dateFin': forms.DateInput(attrs={'type': 'date'}),
        }

class MissionCorrectionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['jours_recuperation']
    