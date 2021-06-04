# -*- encoding: utf-8 -*-
from django import forms
from main.models import UserInformation, Anime, Rating, Genero
class UserForm(forms.Form):
    id = forms.CharField(label='User ID')
    
class GeneroForm(forms.Form):
    genero = forms.ModelChoiceField(queryset=Genero.objects.all())
    
class AnimeForm(forms.Form):
    id = forms.CharField(label='Anime ID')
    
class SearchForm(forms.Form):
    en = forms.CharField(label='Busqueda') 