#encoding:utf-8
from django.db import models
from django.db.models.fields.related import ManyToManyField
    
#prueba [anime][generos]=rating; Eso deber�a devolverte g�neros pero luego puedes buscar con woosh animes de los nuevos que tengan esos g�neros.



class UserInformation(models.Model):
    username = models.CharField(max_length=20, verbose_name='Usuario')
    def __str__(self):
        return self.username
  
class Genero(models.Model):
    genero = models.CharField(max_length=20)
    def __str__(self):
        return self.genero


class Rating(models.Model):
    generoRated = models.ForeignKey(Genero, on_delete=models.CASCADE)
    puntuado = models.FloatField()
    def __str__(self):
        return str(self.puntuado)


class Anime(models.Model):
    titulo = models.CharField(max_length=200)
    imagen = models.CharField(max_length=200)
    episodios = models.PositiveIntegerField()
    #generos = models.ManyToManyField(Genero)
    generos = models.TextField()
    sinopsis = models.TextField()
    puntuacion_usuario = models.PositiveIntegerField(blank=True, null=True)
    puntuacion_BD= models.FloatField()
    ratings=ManyToManyField(Rating)
    nuevo=models.BooleanField()
    def __str__(self):
        return self.titulo

    
