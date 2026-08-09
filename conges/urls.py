from django.urls import path
from . import views


urlpatterns = [
      path('', views.home, name='home'),
      path('test_chef/', views.test_chef, name='test_chef'),
      path('nouvelle_demande/', views.nouvelle_demande, name='nouvelle_demande'),
      path('mes_demandes/', views.mes_demandes, name='mes_demandes' )
      
]