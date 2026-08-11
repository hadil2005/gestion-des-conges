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
      path('recherche-demandes/', views.recherche_demandes, name='recherche_demandes')
]