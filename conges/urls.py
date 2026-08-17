from django.urls import path
from . import views


urlpatterns = [
      path('', views.home, name='home'),
      path('test_chef/', views.test_chef, name='test_chef'),
      path('nouvelle_demande/', views.nouvelle_demande, name='nouvelle_demande'),
      path('mes_demandes/', views.mes_demandes, name='mes_demandes' ),
      path('demandes_a_valider/', views.demandes_a_valider, name='demandes_a_valider' ),
      path('valider_demande/<int:demande_id>/', views.valider_demande, name='valider_demande'),
      path('demandes_remplacent/', views.demandes_remplacent, name='demandes_remplacent'),
      path('accepter_remplacent/<int:demande_id>/', views.accepter_remplacent, name='accepter_remplacent'),
      path('mon_solde/', views.mon_solde, name='mon_solde'),
      path('detail_demande/<int:demande_id>/', views.detail_demande, name='detail_demande'),
      path('recherche_demandes/', views.recherche_demandes, name='recherche_demandes'),
      path('gerer_employes/', views.gerer_employes, name='gerer_employes'),
      path('rapport_solde_historique/', views.rapport_solde_historique, name='rapport_solde_historique'),
      path('rapport_absences/', views.rapport_absences_form, name='rapport_absences_form'),
      path('rapport_absences_pdf/', views.rapport_absences_departement, name='rapport_absences_departement'),
      path('missions/', views.mission_liste, name='mission_liste'),
      path('missions/creer/', views.mission_creer, name='mission_creer'),
      path('missions/<int:mission_id>/corriger/', views.mission_corriger, name='mission_corriger'),
      path('dashboard/', views.dashboard, name='dashboard'),
      path('mes_notifications/', views.mes_notifications, name='mes_notifications'),
      path('missions/<int:mission_id>/supprimer/', views.mission_supprimer, name='mission_supprimer'),
]