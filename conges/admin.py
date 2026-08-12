from django.contrib import admin
from .models import Role, Employe, Direction, Departement, Groupe, EmployeRole, Solde, DemandeConge, Notification, Historique,Mission

admin.site.register(Role)
admin.site.register(Employe)
admin.site.register(Direction)
admin.site.register(Departement)
admin.site.register(Groupe)
admin.site.register(EmployeRole)
admin.site.register(Solde)
admin.site.register(DemandeConge)
admin.site.register(Notification)
admin.site.register(Historique)
admin.site.register(Mission)