from django.db import models 
    
class Role(models.Model):
        ROLE_CHOICES = [
        ('ES', 'Employé Simple'),
        ('CG', 'Chef de Groupe'),
        ('CD', 'Chef de Département'),
        ('DIR', 'Directeur'),
    ] 
        name=models.CharField(max_length=20,choices=ROLE_CHOICES, unique =True)
        def __str__(self):
         return self.get_name_display()

class Direction(models.Model):
    Directeur=models.CharField(max_length=40)
    
class Employe(models.Model):
    nom=models.CharField(max_length=40)
    fonction=models.CharField(max_length=40)
        
class Depratement(models.Model):
    direction= models.ForeignKey(
     Direction,
     on_delete=models.CASCADE,
     related_name=dep   
    )
    Chef_de_departement= models.CharField(max_length=20)

class Groupe(models.Model):
    depratement= models.ForeignKey(
     Depratement,
     on_delete=models.CASCADE,
     related_name=groupe
    )
    Chef_de_groupe= models.CharField(max_length=20)
        
class EmployeRole(models.Model):
    employe = models.ForeignKey(
    Employe,
    on_delete=models.CASCADE,
    related_name=roles  
    )
    
    role= models.ForeignKey(
     Role,
     on_delete=models.CASCADE,
    related_name=employe_role  
    )
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employe_roles'
    )
    dep = models.ForeignKey(
        Dep,
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
    class solde(models.Model):
        employe=models.OneToOneField(
          Employe,  
          on_delete=models.CASCADE,
          related_name='solde'
        )
        solde_annuel = models.DecimalField(max_digits=6)
        solde_recuperation = models.DecimalField(max_digits=6)
        solde_consomme = models.DecimalField(max_digits=6)
    