from django.db import models 
from django.contrib.auth.models import User 
from datetime import timedelta
    
class Role(models.Model):
        ROLE_CHOICES = [
        ('ES', 'Employé Simple'),
        ('CG', 'Chef de Groupe'),
        ('CD', 'Chef de Département'),
        ('DIR', 'Directeur'),
        ('DRH', 'DRH'),
    ] 
        name=models.CharField(max_length=20,choices=ROLE_CHOICES, unique =True)
        def __str__(self):
          return self.get_name_display()
     
class Employe(models.Model):
    
    nom=models.CharField(max_length=40)
    fonction=models.CharField(max_length=40)
    user=models.OneToOneField(
      User,
      on_delete=models.CASCADE,
      null=True,
      blank=True,
      related_name='employe',   
    )
    
    def meme_equipe(self, autre_employe):
     moi = self.role.first()
     lui = autre_employe.role.first()
     if not moi or not lui:
        return False
     if moi.role.name == 'CG':
        return moi.groupe == lui.groupe
     if moi.role.name == 'CD':
        return moi.dep == lui.dep
     if moi.role.name == 'DIR':
        return moi.direction == lui.direction
     return False
 
    def get_hierarchie(self):
        employe_role = self.role.first()
        if not employe_role:
            return None

        groupe = employe_role.groupe
        departement = employe_role.dep or (groupe.depratement if groupe else None)
        direction = employe_role.direction or (departement.direction if departement else None)

        chef_groupe = None
        if groupe:
            cg_role = EmployeRole.objects.filter(role__name='CG', groupe=groupe).first()
            chef_groupe = cg_role.employe if cg_role else None

        chef_departement = None
        if departement:
            cd_role = EmployeRole.objects.filter(role__name='CD', dep=departement).first()
            chef_departement = cd_role.employe if cd_role else None

        chef_direction = None
        if direction:
            dir_role = EmployeRole.objects.filter(role__name='DIR', direction=direction).first()
            chef_direction = dir_role.employe if dir_role else None

        return {
            'groupe': groupe,
            'chef_groupe': chef_groupe,
            'departement': departement,
            'chef_departement': chef_departement,
            'direction': direction,
            'chef_direction': chef_direction,
        }

    def get_role(self):
        employe_role=self.role.first()
        return employe_role.role.name if employe_role else None
    
    def __str__(self):
        return f"{self.nom}, {self.fonction}"
    
class Direction(models.Model):
      nom_de_direction = models.CharField(max_length=30)
      directeur = models.ForeignKey(
        Employe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='directeur')
      def __str__(self):
        if self.directeur:
            return f"{self.nom_de_direction} - {self.directeur.nom}"
        return self.nom_de_direction

         
class Departement(models.Model):
    nom_de_departement= models.CharField(max_length=30)
    direction= models.ForeignKey(
     Direction,
     on_delete=models.CASCADE,
     related_name='dep'   
    )
    Chef_de_departement=  models.ForeignKey(
        Employe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chef_de_departemenet')
    def __str__(self):
        if self.Chef_de_departement:
            return f"{self.nom_de_departement} - {self.Chef_de_departement.nom}"
        return self.nom_de_departement
     

class Groupe(models.Model):
    nom_de_groupe = models.CharField(max_length=30)
    depratement= models.ForeignKey(
     Departement,
     on_delete=models.CASCADE,
     related_name='groupe'
    )
    Chef_de_groupe = models.ForeignKey(
        Employe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chef_de_groupe')
    def __str__(self):
     chef = self.Chef_de_groupe.nom if self.Chef_de_groupe else "Aucun chef"
     return f"{self.nom_de_groupe} - {chef}"
class EmployeRole(models.Model):
    employe = models.ForeignKey(
    Employe,
    on_delete=models.CASCADE,
    related_name='role'  
    )
    
    role= models.ForeignKey(
     Role,
     on_delete=models.CASCADE,
    related_name='employe_role'  
    )
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employe_roles'
    )
    dep = models.ForeignKey(
        Departement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employe_roles'
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employe_roles'
    )
    def __str__(self):
        return f"{self.employe} - {self.role}"
    
    
class Solde(models.Model):
        employe=models.OneToOneField(
          Employe,  
          on_delete=models.CASCADE,
          related_name='solde'
        )
        solde_annuel = models.DecimalField(max_digits=10, decimal_places=2)
        solde_recuperation = models.DecimalField(max_digits=10,decimal_places=2)
        solde_consomme = models.DecimalField(max_digits=10, decimal_places=2)
        jours_consommes = models.DecimalField(max_digits=6, decimal_places=0, default=0)
        @property
        def solde_actuel(self):
           return self.solde_annuel + self.solde_recuperation - self.solde_consomme
        
        def __str__(self): 
         return f"Solde de {self.employe}"
  


        
class Notification(models.Model):
    dateCreation = models.DateTimeField(auto_now_add=True)
    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='notification'
    )
    demande = models.ForeignKey(
        DemandeConge,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    TYPE_NOTIF_CHOICES = [
        ('UPD', 'Update'),
        ('DMD', 'Demande')
    ]
    type_notif = models.CharField(max_length=10, choices=TYPE_NOTIF_CHOICES)
    message = models.CharField(max_length=255)
    lu = models.BooleanField(default=False)


    def __str__(self):
        return f"Notification pour {self.employe} ({self.get_type_notif_display()})"
            
class Historique(models.Model):
    ACTION_CHOICES = [
        ('VALIDATION', 'Validation de congé'),
        ('REMPLACEMENT', 'Remplacement'),
    ]
    DECISION_CHOICES = [
        ('ACCEPTE', 'Accepté'),
        ('REFUSE', 'Refusé'),
    ]

    demande = models.ForeignKey(
        DemandeConge,
        on_delete=models.CASCADE,
        related_name='historiques'
    )
    employe = models.ForeignKey(
        Employe,
        on_delete=models.CASCADE,
        related_name='historiques'
    )
    type_action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    commentaire = models.CharField(max_length=255, blank=True)
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Historique de {self.demande} par {self.employe}"
     


class Mission(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='missions')
    dateDebut = models.DateField()
    dateFin = models.DateField()
    motif = models.CharField(max_length=255, blank=True)
    jours_recuperation = models.IntegerField(default=0, blank=True)

    def calculer_jours_recuperation(self):
        jours = 0
        date = self.dateDebut
        while date <= self.dateFin:
            if date.weekday() in (4, 5): # counting ybda m tnin so 4= ljm3a, 5=sbt
                jours += 1
            date += timedelta(days=1)
        return jours

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        ancien_jours = None
        if not is_new:
            ancien_jours = Mission.objects.filter(pk=self.pk).values_list('jours_recuperation', flat=True).first()

        if not self.jours_recuperation:
            self.jours_recuperation = self.calculer_jours_recuperation()

        super().save(*args, **kwargs)

        solde = getattr(self.employe, 'solde', None)
        if solde:
            if is_new:
                solde.solde_recuperation += self.jours_recuperation * 1000
                solde.save()
            elif ancien_jours is not None and ancien_jours != self.jours_recuperation:
                delta = (self.jours_recuperation - ancien_jours) * 1000
                solde.solde_recuperation += delta
                solde.save()

    def delete(self, *args, **kwargs):
         solde = getattr(self.employe, 'solde', None)
         if solde:
            solde.solde_recuperation -= self.jours_recuperation * 1000
            solde.save()
         super().delete(*args, **kwargs)