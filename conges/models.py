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
     
class Employe(models.Model):
    nom=models.CharField(max_length=40)
    fonction=models.CharField(max_length=40)
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
         return f"Direction - {self.directeur}"
         
class Depratement(models.Model):
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
        return f"Depratement - {self.Chef_de_departement}"
    

class Groupe(models.Model):
    nom_de_groupe = models.CharField(max_length=30)
    depratement= models.ForeignKey(
     Depratement,
     on_delete=models.CASCADE,
     related_name='groupe'
    )
    Chef_de_groupe=  models.ForeignKey(
        Employe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chef_de_groupe')
    def __str__(self):
        return f"Groupe - {self.Chef_de_groupe}"
    
        
class EmployeRole(models.Model):
    employe = models.ForeignKey(
    Employe,
    on_delete=models.CASCADE,
    related_name='roles'  
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
        Depratement,
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
        solde_annuel = models.DecimalField(max_digits=6, decimal_places=2)
        solde_recuperation = models.DecimalField(max_digits=6,decimal_places=2)
        solde_consomme = models.DecimalField(max_digits=6, decimal_places=2)
        @property
        def solde_actuel(self):
         return self.solde_annuel + self.solde_recuperation - self.solde_consomme
     
        def __str__(self): 
         return f"Solde de {self.employe}"
  
class DemandeConge(models.Model):
        name_employee=models.ForeignKey(
          Employe,
          on_delete=models.CASCADE,
          related_name='employe' 
        )
        name_remplacent=models.ForeignKey(
            Employe,
            on_delete=models.CASCADE,
            related_name='remplacent'
        )
        dateCreation = models.DateField(auto_now_add=True)
        dateDebut = models.DateField()
        dateFin = models.DateField()
        Numbrejours= models.DecimalField(max_digits=2, decimal_places=0)
        piece_Joine=models.FileField(upload_to='justificatifs/', null=True, blank=True)
        commentaire=models.TextField(blank=True)
        TYPE_STATUE = [
            ('VA', 'Validé'),
            ('REF', 'Refusé'),
            ('EN ATT', 'En attente'),
            ('BR', 'Brouillon'),
        ]
        statue=models.CharField(max_length=10, choices=TYPE_STATUE)
        motif = models.CharField(max_length=255, blank=True)
        TYPE_CONGE_CHOICES = [
         ('1', 'Congé xxx'),
         ('2', 'Congé maladie'),
         ('3', 'Congé xx'),
         ('AU', 'Autre'),
]
        type_conge = models.CharField(max_length=10, choices=TYPE_CONGE_CHOICES)
        def __str__(self):
         return f"Demande de {self.name_employee} ({self.get_statue_display()})"

        
class Notification(models.Model):
    dateCreation=models.DateField(auto_now_add=True)
    employe=models.ForeignKey(
    Employe,
    on_delete=models.CASCADE,
    related_name='notification'    
            )
    TYPE_NOTIF_CHOICES =  [
        ('UPD', 'Update'),
        ('DMD', 'Demande')
            ]
    type_notif=models.CharField(max_length=10, choices=TYPE_NOTIF_CHOICES)     
    def __str__(self):
     return f"Notification pour {self.employe} ({self.get_type_notif_display()})"   
            
class Historique(models.Model):
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
        date_creation = models.DateField(auto_now_add=True)
        def __str__(self):
         return f"Historique de {self.demande} par {self.employe}"