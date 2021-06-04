#encoding:utf-8
import shelve
from main.models import UserInformation, Anime, Rating, Genero
from django.shortcuts import render, redirect, get_object_or_404
from main.recommendations import  transformPrefs, getRecommendations, topMatches, getRecommendedItems, calculateSimilarItems
from bs4 import BeautifulSoup
import urllib.request
import lxml
from datetime import datetime
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from main.forms import UserForm, AnimeForm, GeneroForm, SearchForm
import re, os, shutil
from _ast import If
from numpy import delete

# Funcion que carga en el diccionario Prefs todas las puntuaciones de usuarios a animes. Tambien carga el diccionario inverso
# Serializa los resultados en dataRS.dat
def loadDict():
    Prefs={}   # matriz de usuarios y puntuaciones
    shelf = shelve.open("dataRS.dat")
    animes = Anime.objects.all()
    for a in animes:

        itemid = int(a.id)
        notas = a.ratings.all()

        for nota in notas:
            generoId = int(nota.generoRated.id)#genero.genero.id
            Prefs.setdefault(generoId, {})
            Prefs[generoId][itemid] = nota.puntuado
            shelf['SimItems']=calculateSimilarItems(Prefs, n=10)

    shelf['Prefs']=Prefs
    shelf['ItemsPrefs']=transformPrefs(Prefs)
    print(shelf['Prefs'])
    shelf.close()
    


    
#  CONJUNTO DE VISTAS
def index(request):
    num_animes = Anime.objects.all().count()
    return render(request,'index.html', {'num_animes':num_animes})

#Scraping y woosh
def populateDB():
    
    #woosh
    #define el esquema de la información
    schem = Schema(titulo=TEXT(stored=True), imagen=TEXT(stored=True), puntuacionUsuario=KEYWORD(stored=True), puntuacionBD=KEYWORD(stored=True), episodios=KEYWORD(stored=True), sinopsis=TEXT(stored=True), generos=TEXT(stored=True))
    
    #eliminamos el directorio del índice, si existe
    if os.path.exists("Index"):
        shutil.rmtree("Index")
    os.mkdir("Index")
    
    #creamos el índice
    ix = create_in("Index", schema=schem)
    #creamos un writer para poder añadir documentos al indice
    writer = ix.writer()
    
    #Contamos animes almacenados para asegurarnos de que se guardan todos
    numeroAnimes = 0

    #Borramos la BD
    Anime.objects.all().delete()
    Genero.objects.all().delete()
    UserInformation.objects.all().delete()
    Rating.objects.all().delete()
    

    #Extraemos con beautifulsoup
    lista_animes=[]
    lista_animes1=[]
    usuario="Leodbz"
    userInformation = UserInformation.objects.get_or_create(username=usuario)
    f = urllib.request.urlopen("https://myanimelist.net/animelist/"+ usuario +"?status=2&tag=")
    s = BeautifulSoup(f, "lxml")
    lista_animetitle = s.find_all("a", class_="animetitle")
    lista_link_animes = []
    lista_puntuacion_usuario = s.find_all("span", class_="score-label")
    for anime in lista_animetitle:
        lista_link_animes.append("https://myanimelist.net" + str(anime).split('"')[3])
    
    i=0
    for link_anime in lista_link_animes:
        #Obtenemos las puntuaciones del usuario
        if(lista_puntuacion_usuario[i].getText()=="-"):
            puntuacion_usuario1=0
        else:
            puntuacion_usuario1=lista_puntuacion_usuario[i].getText()
        i=i+1

        f = urllib.request.urlopen(link_anime.encode("ascii", "ignore").decode("ascii", "ignore"))
        s = BeautifulSoup(f, "lxml")
        
        #Obtenemos las puntuaciones de la BD
        puntuacion_BD1= s.find("div", class_="fl-l score").div.getText()
        
        #Obtenemos los titulos
        titulo1 = s.find("h1", class_="title-name h1_bold_none").contents[0].getText()
        print(titulo1.encode("ascii", "ignore").decode("ascii", "ignore"))
        #Obtenemos las imagenes
        imagen1 = str(s.find("td", class_="borderClass").find("img", itemprop="image")).split('"')[-4]
        #Obtenemos los episodios
        aux=s.find("span", id="curEps").getText()
        if((aux == "?") or (aux == "Unknown")):
            episodios1 = 0
        else:
            episodios1 = aux
            
        #Obtenemos los generos
        generosAux= s.find_all("span", itemprop="genre")
        generos1 = []
        lista_ratings=[]
        #Guardamos en BD
        for generoz in generosAux:
            generos1.append(generoz.getText())
            G, created=Genero.objects.get_or_create(genero=generoz.getText())
            R=Rating.objects.create(generoRated=G,
                                    puntuado=puntuacion_usuario1)
            lista_ratings.append(R)
        #Obtenemos las sinopsis
        sinopsis1 = s.find("p", itemprop="description").getText()
        #Guardamos en BD
        A = Anime.objects.create(titulo = titulo1,
                                imagen = imagen1,
                                episodios = episodios1,                               
                                generos = generos1,
                                sinopsis = sinopsis1,
                                puntuacion_BD = puntuacion_BD1,
                                puntuacion_usuario = puntuacion_usuario1,
                                nuevo=bool(False)
                                )
        
        for rat in lista_ratings:
                A.ratings.add(rat)
        
        numeroAnimes = numeroAnimes + 1
        print(numeroAnimes)
        
    
        #woosh
    
        #añade cada anime de la lista al índice
        lista_animes.append((titulo1,imagen1, puntuacion_usuario1, puntuacion_BD1, episodios1, sinopsis1, generos1))
    for anime in lista_animes:
        writer.add_document(titulo=str(anime[0]), imagen=str(anime[1]), puntuacionUsuario=str(anime[2]), puntuacionBD=str(anime[3]), episodios=str(anime[4]), sinopsis=str(anime[5]), generos=str(anime[6]).replace("[", "").replace("]", "").replace("'",""))    
    
        
    #De paso obtenemos los animes a estrenar
        
    f = urllib.request.urlopen("https://myanimelist.net/anime/season")
    s = BeautifulSoup(f, "lxml")
    
    lista_etiquetas = s.find_all("div", class_="title")
    
    lista_links_season=[]
    
    for etiqueta in lista_etiquetas:
        lista_links_season.append(str(etiqueta).split('"')[-2])
    for link_season in lista_links_season[:50]:
        
        f = urllib.request.urlopen(link_season.encode("ascii", "ignore").decode("ascii", "ignore"))
        s = BeautifulSoup(f, "lxml")
        
        #Obtenemos las puntuaciones de la BD
        puntuacion_BD1= s.find("div", class_="fl-l score").div.getText()
        if(puntuacion_BD1=="N/A"):
            puntuacion_BD1=0
        
        #Obtenemos los titulos
        titulo1 = s.find("h1", class_="title-name h1_bold_none").contents[0].getText()
        print(titulo1.encode("ascii", "ignore").decode("ascii", "ignore"))
        #Obtenemos las imagenes
        imagen1 = str(s.find("td", class_="borderClass").find("img", itemprop="image")).split('"')[-4]
        #Obtenemos los episodios
        aux=s.find("span", id="curEps").getText()
        if((aux == "?") or (aux == "Unknown")):
            episodios1 = 0
        else:
            episodios1 = aux
            
        #Obtenemos los generos
        generosAux= s.find_all("span", itemprop="genre")
        generos1 = []
        lista_ratings=[]
        for generoz in generosAux:
            generos1.append(generoz.getText())
            G, created=Genero.objects.get_or_create(genero=generoz.getText())
            R=Rating.objects.create(generoRated=G,
                                    puntuado=puntuacion_BD1)
            lista_ratings.append(R)
        #Obtenemos las sinopsis
        sinopsis1 = s.find("p", itemprop="description").getText()
        
        
        lista_animes1.append((titulo1,imagen1, puntuacion_BD1, episodios1, sinopsis1, generos1))
        

        A = Anime.objects.create(titulo = titulo1,
                                imagen = imagen1,
                                episodios = episodios1,                               
                                generos = generos1,
                                sinopsis = sinopsis1,
                                puntuacion_BD = puntuacion_BD1,
                                puntuacion_usuario = 0,
                                nuevo=bool(True)
                                )
        
        for rat in lista_ratings:
                A.ratings.add(rat)
        
        numeroAnimes = numeroAnimes + 1
    for anime in lista_animes1:
        writer.add_document(titulo=str(anime[0]), imagen=str(anime[1]), puntuacionUsuario=str(0), puntuacionBD=str(anime[2]), episodios=str(anime[3]), sinopsis=str(anime[4]), generos=str(anime[5]).replace("[", "").replace("]", "").replace("'",""))    
        
    writer.commit()
    return numeroAnimes
        
#carga los datos desde la web en la BD
def carga(request):
 
    if request.method=='POST':
        if 'Confirmar' in request.POST:      
            numeroAnimes = populateDB()
            aviso=str(numeroAnimes) + " guardados."
            return render(request, 'cargaBaseDatos.html', {'aviso':aviso})
        else:
            return redirect("/")
           
    return render(request, 'confirmacion.html')

def loadRS(request):
    loadDict()
    return render(request,'loadRS.html')

def similarAnimes(request):
    if request.method=='GET':
        form = GeneroForm(request.GET, request.FILES)
        if form.is_valid():
            genero = form.cleaned_data['genero']
            generoId = genero.id
            shelf = shelve.open("dataRS.dat")
            Prefs = shelf['Prefs']
            SimItems = shelf['SimItems']
            shelf.close()
            rankings = getRecommendedItems(Prefs, SimItems, int(generoId))
            recommended = rankings
            animes = []
            scores = []
            for re in recommended:
                anime=Anime.objects.get(pk=re[1])
                if(anime.nuevo):
                    if(genero.genero in anime.generos):
                        animes.append(Anime.objects.get(pk=re[1]))
                        scores.append(re[0])
            items= zip(animes,scores)
            if(animes.__len__()==0):
                mensaje = "No hay series nuevas con este genero"
                return render(request,'similarAnimes.html', {'animes': animes, 'items': items, 'mensaje': mensaje})
            return render(request,'similarAnimes.html', {'animes': animes, 'items': items})

    form = GeneroForm()
    return render(request,'search_anime.html', {'form': form})

def lista_animes(request):
    animes=Anime.objects.all()
    return render(request,'animes.html', {'animes':animes})

def busqueda_anime(request):
    if request.method=='GET':
        form = SearchForm(request.GET, request.FILES)
        if form.is_valid():
            search = form.cleaned_data['en']
            print(search)
            #abrimos el índice
            ix=open_dir("Index")
            #creamos un searcher en el índice    
            with ix.searcher() as searcher:
                #se crea la consulta: buscamos en los campos "titulo" o "sinopsis" alguna de las palabras
                #se usa la opción OrGroup para que use el operador OR por defecto entre palabras, en lugar de AND
                query = MultifieldParser(["titulo","sinopsis"], ix.schema, group=OrGroup).parse(str(search))
                
                #llamamos a la función search del searcher, pasándole como parámetro la consulta creada
                results = searcher.search(query)
                animes=[]
                for r in results:
                    animeEncontrado =Anime.objects.get(titulo=r['titulo'])
                    animeEncontrado.titulo = animeEncontrado.titulo.encode("ascii", "ignore").decode("ascii", "ignore")
                    animes.append(animeEncontrado)
                print(animes)
                return render(request,'animesSearched.html', {'animes': animes})
    form = SearchForm()
    return render(request,'search_anime.html', {'form': form})

def busqueda_anime_genero(request):
    if request.method=='GET':
        form = GeneroForm(request.GET, request.FILES)
        if form.is_valid():
            search = form.cleaned_data['genero']
            print(search)
            #abrimos el índice
            ix=open_dir("Index")
            #creamos un searcher en el índice    
            with ix.searcher() as searcher:
                #se crea la consulta: buscamos en los campos "titulo" o "sinopsis" alguna de las palabras
                #se usa la opción OrGroup para que use el operador OR por defecto entre palabras, en lugar de AND
                query = QueryParser("generos", ix.schema).parse(str(search))
                
                #llamamos a la función search del searcher, pasándole como parámetro la consulta creada
                results = searcher.search(query)
                animes=[]
                for r in results:
                    animeEncontrado =Anime.objects.get(titulo=r['titulo'])
                    animeEncontrado.titulo = animeEncontrado.titulo.encode("ascii", "ignore").decode("ascii", "ignore")
                    animes.append(animeEncontrado)
                print(animes)
                return render(request,'animesSearched.html', {'animes': animes})
    form = GeneroForm()
    return render(request,'search_anime.html', {'form': form})