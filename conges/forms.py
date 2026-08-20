from django import forms
from .models import DemandeConge, Mission, Role, Groupe, Departement, Direction, Solde, Employe
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class DemandeCongeForm(forms.ModelForm):
    class Meta:
        model = DemandeConge
        fields = ['name_remplacent', 'dateDebut', 'dateFin', 'motif', 'type_conge', 'piece_Joine']
        widgets = {
            'dateDebut': forms.DateInput(attrs={'type': 'date'}),
            'dateFin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, employe=None, **kwargs):
        super().__init__(*args, **kwargs)
        if employe:
            self.fields['name_remplacent'].queryset = self.get_remplacent_queryset(employe)
            
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})

    def get_remplacent_queryset(self, employe):
        employe_role = employe.role.first()
        role = employe.get_role()

        if not employe_role:
            return Employe.objects.none()

        if role == 'ES':
            if not employe_role.groupe:
                return Employe.objects.none()
            dep = employe_role.groupe.depratement
            return Employe.objects.filter(
                role__groupe__depratement=dep
            ).exclude(role__role__name='CD').exclude(id=employe.id)

        elif role == 'CG':
            if not employe_role.groupe:
                return Employe.objects.none()
            dep = employe_role.groupe.depratement
            return Employe.objects.filter(
                role__groupe__depratement=dep
            ).exclude(id=employe.id)

        elif role == 'CD':
          if not employe_role.dep:
            return Employe.objects.none()
          direction = employe_role.dep.direction
          return Employe.objects.filter(
           role__role__name__in=['CG', 'DIR'],
           role__dep__direction=direction
          ).exclude(id=employe.id)

        elif role == 'DIR':
          if not employe_role.direction:
            return Employe.objects.none()
        return Employe.objects.filter(
          role__role__name='CD',
          role__dep__direction=employe_role.direction
    )
       
        return Employe.objects.none()
    
class NouvelEmployeForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    nom = forms.CharField(max_length=40)
    fonction = forms.CharField(max_length=60)
    role = forms.ChoiceField(choices=Role.ROLE_CHOICES)
    groupe = forms.ModelChoiceField(queryset=Groupe.objects.all(), required=False)
    departement = forms.ModelChoiceField(queryset=Departement.objects.all(), required=False)
    direction = forms.ModelChoiceField(queryset=Direction.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})
    
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
    
class DirectionForm(forms.ModelForm):
    class Meta:
        model = Direction
        fields = ['nom_de_direction', 'directeur']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['directeur'].required = False
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field in self.fields.values():
            field.widget.attrs.update({'class': input_classes})


class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['nom_de_departement', 'direction', 'Chef_de_departement']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Chef_de_departement'].required = False
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field in self.fields.values():
            field.widget.attrs.update({'class': input_classes})


class GroupeForm(forms.ModelForm):
    class Meta:
        model = Groupe
        fields = ['nom_de_groupe', 'depratement', 'Chef_de_groupe']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Chef_de_groupe'].required = False
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field in self.fields.values():
            field.widget.attrs.update({'class': input_classes})
            
class SoldeForm(forms.ModelForm):
    class Meta:
        model = Solde
        fields = ['employe', 'solde_annuel', 'solde_recuperation', 'solde_consomme']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        input_classes = 'w-full border border-neutral-200 rounded px-3 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary'
        for field in self.fields.values():
            field.widget.attrs.update({'class': input_classes})