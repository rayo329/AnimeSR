#encoding:utf-8

from django.urls import path
from django.contrib import admin
from main import views

urlpatterns = [
    path('carga/',views.carga),
    path('animes/', views.lista_animes),
    path('similarAnimes/', views.similarAnimes),
    path('', views.index),
    path('populate/', views.populateDB),
    path('loadRS/', views.loadRS),
    path('busqueda/', views.busqueda_anime),
    path('busquedaGenero/', views.busqueda_anime_genero),
    path('admin/', admin.site.urls),
]