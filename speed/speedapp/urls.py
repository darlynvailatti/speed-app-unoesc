"""speed URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^sensores/$', views.formSensores),

    #Aresta
    url(r'^testes/(?P<id_teste>\d+)/arestas/(?P<id_aresta>\d+)/deleteAresta$', views.deleteAresta),
    url(r'^testes/(?P<id_teste>\d+)/novoAresta$', views.novoAresta),
    url(r'^testes/(?P<id_teste>\d+)/arestas$', views.arestas),
    url(r'^testes/(?P<id_teste>\d+)/arestas/(?P<id_aresta>\d+)', views.arestaDetail),
    url(r'^testes/(?P<id_teste>\d+)/arestas/saveAresta$', views.saveAresta),


    #Teste
    url(r'^testes/(?P<id>\d+)', views.testeDetail, name='testeDetail'),
    url(r'^testes/novoTeste$', views.novoTeste),
    url(r'^testes/saveTeste$', views.saveTeste),
    url(r'^testes/deleteTeste/(?P<id>\d+)', views.deleteTeste),
    url(r'^testes/',views.testes),

    #AtletasTeste
    url(r'^atletas/(?P<id_atleta>\d+)/testes/(?P<id_teste>\d+)/resetTeste$', views.resetTeste),
    url(r'^atletas/(?P<id_atleta>\d+)/testes/(?P<id_teste>\d+)/monitorarTeste$', views.monitorarAtletaTeste),
    url(r'^atletas/(?P<id_atleta>\d+)/testes/(?P<id_teste>\d+)/atletaTesteDetail$',views.AtletaTesteDetail),
    url(r'^atletas/(?P<id_atleta>\d+)/testes/(?P<id_teste>\d+)/resultados$',views.atletaTesteResultados),
    url(r'^atletas/(?P<id_atleta>\d+)/saveAtletaTeste$',views.saveAtletaTeste),
    url(r'^atletas/(?P<id_atleta>\d+)/novoAtletaTeste$',views.novoAtletaTeste),

    #Services
    url(r'^services/testes/(?P<id_teste>\d+)/temposTotaisPorVolta$',views.temposTotaisPorVolta),
    url(r'^services/testes/(?P<id_teste>\d+)/velocidadePorVolta$',views.velocidadePorVolta),
    url(r'^services/testes/(?P<id_teste>\d+)/velocidadeDasVoltasPorAresta$',views.velocidadeDasVoltasPorAresta),

    #Atleta
    url(r'^atletas/(?P<id_atleta>\d+)/atletaDetailInformacoes$', views.atletaDetailInformacoes),
    url(r'^atletas/(?P<id_atleta>\d+)/saveAtletaInfo$', views.saveAtletaInfo),
    url(r'^atletas/(?P<id_atleta>\d+)/deleteAtleta$', views.deleteAtleta),
    url(r'^atletas/(?P<id_atleta>\d+)',views.AtletaDetail),
    url(r'^atletas/novoAtleta$', views.novoAtleta),
    url(r'^atletas/saveAtletaInfo$', views.saveNovoAtletaInfo),
    url(r'^atletas/',views.atletas),

    #Home
    url(r'^',views.index),

]
