from django import forms
from .models import DemandeConge, Mission
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class DemandeCongeForm(forms.ModelForm):
    class Meta:
        model = DemandeConge
        fields = ['name_remplacent','dateDebut','dateFin','motif','piece_Joine','type_conge']
        widgets = { 
                   'dateDebut':forms.DateInput(attrs={'type':'date'}),
                   'dateFin':forms.DateInput(attrs={'type':'date'})
                   } 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 pr-2 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})
            
            
class MissionCorrectionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['jours_recuperation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})
            
class StyledLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'placeholder': 'prenom.nom@entreprise.com',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'placeholder': '••••••••',
        })
    