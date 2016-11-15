from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django import forms
from django.forms import modelform_factory
from .forms import *
from .tasks import *
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher
from celery.result import AsyncResult
from celery import task
import redis
import time
import copy
import datetime
import json

def index(request):
    return render(request,"speedapp/index.html")

# Create your views here.
def formSensores(request):
    sensores = Sensor.objects.all()

    res = AsyncResult("monitoraSensores")

    r = Redis.conexao();

    taskMonitoraSensores = r.get('task:monitoraSensores')

    if taskMonitoraSensores != 'true':
        r.set('task:monitoraSensores','true')
        monitoraSensores.delay(sensores)
    else:
        r.set('task:monitoraSensores','false') #marca falso para parar a task atual
        time.sleep(1)#tempo para que a task em execucao saia do seu loop
        r.set('task:monitoraSensores','true') #marca true para iniciar a nova task
        monitoraSensores.delay(sensores)

    return render(request,"speedapp/monitoraSensores.html",{"sensores": sensores})

def formArestas(request):
    pass

#News
def novoTeste(request):
    teste = Teste()
    teste.descricao = ''
    form = TesteForm(instance=teste)
    return render(request, "speedapp/testeDetail.html", {"form":form})

def novoAresta(request,id_teste):
    teste = Teste.objects.get(pk=id_teste)
    aresta = Aresta()
    aresta.teste = teste
    aresta.id = ''
    form = ArestaForm()
    return render(request, "speedapp/arestaDetail.html", {"form":form,
                                                          "aresta":aresta})

def novoAtletaTeste(request,id_atleta):
    atleta = Atleta.objects.get(pk=id_atleta)
    atletaTeste = AtletaTeste()
    atletaTeste.atleta = atleta

    formAtletaTeste = AtletaTesteForm(instance=atletaTeste)

    return render(request,"speedapp/atletaTesteDetail.html",{"atletaTeste" : atletaTeste,
                                                             "atleta": atleta,
                                                             "formAtletaTeste": formAtletaTeste,
                                                             "novo": True})

def novoAtleta(request):
    atleta = Atleta()
    formAtletaInfo = AtletaForm(instance=atleta)
    novo = True

    return render(request,"speedapp/atletaDetailInformacoes.html",{"formAtletaInfo":formAtletaInfo,
                                                                   "novo":novo})

#Lists
def arestas(request, id_teste):
    teste = Teste.objects.get(pk =id_teste)
    atletaTeste = AtletaTeste.objects.filter(teste=teste).first()
    arestas = Aresta.objects.filter(teste = teste)

    if atletaTeste:
        atleta = atletaTeste.atleta

        return render(request,"speedapp/arestasAtletaTeste.html",{"arestas":arestas,
                                                                  "atleta": atleta,
                                                                  "teste":teste})
    else:
        atleta = ''

        return render(request,"speedapp/arestasTeste.html",{"arestas":arestas,
                                                            "atleta": atleta,
                                                            "teste":teste})

def testes(request):
    testes = Teste.objects.filter(origem='0')
    return render(request,"speedapp/testes.html",{"testes": testes})

def atletas(request):
    atletas = Atleta.objects.all()
    return render(request,"speedapp/atletas.html",{"atletas":atletas})

#Details
def arestaDetail(request,id_teste,id_aresta):
    teste = Teste.objects.get(pk=id_teste)
    aresta = Aresta.objects.get(pk = id_aresta)
    form = ArestaForm(instance = aresta)

    return render(request,"speedapp/arestaDetail.html",
                  {"aresta":aresta,
                   "teste":teste,
                   "form": form})

def testeDetail(request,id):
    teste = Teste.objects.get(pk=id)
    form = TesteForm(instance=teste)

    arestas = Aresta.objects.filter(teste=id)
    voltas = Volta.objects.filter(teste=id)
    return render(request,"speedapp/testeDetail.html",
                  {"teste": teste,
                   "form":form,
                   "arestas" : arestas,
                   "voltas" : voltas})

def AtletaDetail(request,id_atleta):
    atleta = Atleta.objects.get(pk=id_atleta)
    form = AtletaForm(instance=atleta)

    #Teste do atleta
    testes = AtletaTeste.objects.filter(atleta=atleta.id)

    #Atributos do atleta
    atributos = AtletaAtributos.objects.filter(atleta=atleta.id)

    return render(request,"speedapp/atletaDetail.html",
                  {"form":form,
                   "atleta":atleta,
                   "testes":testes,
                   "atributos":atributos})

def atletaDetailInformacoes(request,id_atleta):

    if id_atleta:
        novo = False
    else:
        novo = True

    atleta = Atleta.objects.get(pk=id_atleta)
    formAtletaInfo = AtletaForm(instance=atleta)

    return render(request,"speedapp/atletaDetailInformacoes.html",{"formAtletaInfo": formAtletaInfo,
                                                                   "atleta":atleta,
                                                                   "novo": novo})

def AtletaTesteDetail(request,id_atleta,id_teste):
    atleta = Atleta.objects.get(pk=id_atleta)
    teste = Teste.objects.get(pk=id_teste)

    atletaTeste = AtletaTeste.objects.filter(teste=teste,atleta=atleta).first()

    formAletaTeste = AtletaTesteForm(instance=atletaTeste)
    formTeste = TesteForm(instance=atletaTeste.teste)

    return render(request,"speedapp/atletaTesteDetail.html",{"formAtletaTeste":formAletaTeste,
                                                             "formTeste":formTeste,
                                                             "atletaTeste":atletaTeste,
                                                             "teste": atletaTeste.teste})

def atletaTesteResultados(request,id_atleta,id_teste):

    atleta = Atleta.objects.get(pk=id_atleta)
    teste = Teste.objects.get(pk=id_teste)

    atletaTeste = AtletaTeste.objects.filter(teste=teste,atleta=atleta).first()

    temposPorVolta = []


    for v in teste.volta_set.all().extra(order_by=["-id"]):
        tempoVolta = {}
        tempoVolta["volta"] = v.numero
        tempoVolta["tempo"] = v.tempoTotal
        temposPorVolta.append(tempoVolta)

    return render(request,"speedapp/atletaTesteResultados.html",{"atletaTeste": atletaTeste,
                                                                 "temposPorVolta": json.dumps(temposPorVolta)})

#Sevices
def temposTotaisPorVolta(resquest,id_teste):

    teste = Teste.objects.get(pk=id_teste)
    temposPorVolta = {}

    for v in teste.volta_set.all().extra(order_by=["-id"]):
        tempoVolta = {}
        tempoVolta["volta"] = v.numero
        tempoVolta["tempo"] = v.tempoTotal
        temposPorVolta[v.numero] = tempoVolta

    return JsonResponse(temposPorVolta)

def velocidadePorVolta(resquest,id_teste):

    teste = Teste.objects.get(pk=id_teste)
    velocidadesPorVolta = {}

    for v in teste.volta_set.all().extra(order_by=["-id"]):
        velocidade = {}
        velocidade["volta"] = v.numero
        velocidade["velocidadeGeral"] = v.velocidadeGeral
        velocidade["velocidadeMedia"] = v.velocidadeMedia
        velocidadesPorVolta[v.numero] = velocidade

    return JsonResponse(velocidadesPorVolta)

def velocidadeDasVoltasPorAresta(request,id_teste):

    teste = Teste.objects.get(pk=id_teste)
    velocidadesPorVolta = {}
    tempos = []
    temposCheios = []
    tempo = 0
    index = 0

    json = {}
    json["voltas"] = []

    #Busque todas as deteccoes em order decrescente de ID
    for v in teste.volta_set.all().extra(order_by=["id"]):
        volta = {}
        volta["arestas"] = []
        volta["numero"] = v.numero

        for d in v.deteccao_set.all().extra(order_by=["-id"]):

            if len(temposCheios) > 0:
                t = temposCheios[index] - d.tempo
                tempos.append(t)
                temposCheios.append(d.tempo)
                index+=1
            else:
                temposCheios.append(d.tempo)


        print "Volta: %s" % (v.numero)

        index = len(tempos) - 1

        for a in teste.aresta_set.all().extra(order_by=["id"]):
            print "Aresta: %s / Tempo: %s" % (a.descricao.encode('utf-8'), tempos[index])
            aresta = {}
            aresta["descricao"] = a.descricao
            aresta["velocidade"] = a.distancia / tempos[index]

            volta["arestas"].append(aresta)
            index-=1

        print("-----")
        tempos = []
        temposCheios = []
        index = 0

        json["voltas"].append(volta)


    return JsonResponse(json)



#Saves
def saveTeste(request):
    id = request.POST['id']

    if id != '':
        teste = Teste.objects.get(pk=id)
        if request.method == "POST":
            form = TesteForm(request.POST,instance=teste)
            if form.is_valid():
                form.save()
                arestas = Aresta.objects.filter(teste=teste.id)
                voltas = Volta.objects.filter(teste=teste.id)
    else:
        teste = Teste()
        teste.testeFinalizado = False
        teste.status = ''
        teste.origem = '0'
        teste.dataHora = datetime.datetime.now()

        form = TesteForm(request.POST,instance=teste)

        if form.errors:
            return render(request,"speedapp/testeDetail.html",{"form":form,
                                                               "errors":form.errors})
        teste = form.save()

    return HttpResponseRedirect(teste.id)

def saveAresta(request,id_teste):

    id = request.POST['id']
    id_teste = request.POST['teste']

    if id != None and id != '':
        aresta = Aresta.objects.get(pk=id)
        if request.method == "POST":
            form = ArestaForm(request.POST, instance=aresta)
            form.fields['descricao'].required = False
            if form.is_valid():
                if aresta.descricao == None:
                    aresta.descricao = ''
                form.save()
            else:
                erro = "Dados invalidos!"
                return render(request,"speedapp/arestaDetail.html",{"form": form,
                                                                    "aresta": aresta,
                                                                    "erro": erro})
    else:
        aresta = Aresta()
        aresta.teste = Teste.objects.get(pk = id_teste)

        form = ArestaForm(request.POST, instance = aresta)
        form.fields['descricao'].required = False

        if form.errors:
            #Retornar o form com id vazia
            aresta.id = ''
            erro = "Verifique os campos obrigatorios marcados com *"
            return render(request,"speedapp/arestaDetail.html",{"form": ArestaForm(),
                                                                "aresta": aresta,
                                                                "erro": erro})
        #Salvar com id = None
        aresta.id = None
        if aresta.descricao == None:
            aresta.descricao = ''
        form.save()

    return render(request,"speedapp/arestaDetail.html",{"form": form,
                                                        "aresta": aresta,
                                                        "sucesso": True})

def saveAtletaTeste(request,id_atleta):
    atleta = Atleta.objects.get(pk=id_atleta)

    id = request.POST.get('id')

    if request.POST.get('id'):
        print 'Editando um teste'
        id_teste = request.POST.get('testeAplicacao',False)
    else:
        print 'Inserindo um novo teste'
        id_teste = request.POST.get('testesModelos',False)


    teste = Teste.objects.get(pk=id_teste)

    if id:
        atletaTeste = AtletaTeste.objects.get(pk=id)
        testeDoAtleta = atletaTeste.teste
        if request.method == "POST":
            formTeste = TesteForm(request.POST,instance=testeDoAtleta)
            if formTeste.is_valid():
                formTeste.save()
            else:
                return render("speedapp/atletaTesteDetail.html",{"formTeste":formTeste})


    else:
        #Copiar teste modelo para NOVO teste
        testeDoAtleta = copy.copy(teste)
        testeDoAtleta.id = None
        testeDoAtleta.origem = '1'
        testeDoAtleta.dataHora = datetime.datetime.now()
        testeDoAtleta.save()

        #Busca as arestas do teste de model
        arestasDoTesteDoAtleta = Aresta.objects.filter(teste=teste)

        #Relaciona as novas arestas com o novo teste
        for a in arestasDoTesteDoAtleta:
            arestaDoNovoTeste = copy.copy(a)

            arestaDoNovoTeste.id = None
            arestaDoNovoTeste.teste = testeDoAtleta
            arestaDoNovoTeste.save()
            print 'Aresta ' + str(a.id) + ' relacionada a teste ' + str(a.teste.id)

        atletaTeste = AtletaTeste()
        atletaTeste.atleta = atleta
        atletaTeste.teste = copy.copy(testeDoAtleta)
        atletaTeste.save()


    return HttpResponseRedirect("/speedapp/atletas/" + str(atletaTeste.atleta.id) + "/testes/" + str(atletaTeste.teste.id) + "/atletaTesteDetail")

def saveAtletaInfo(request,id_atleta):

    print id_atleta

    #Editando
    if request.POST.get("id") or id_atleta != False:
        print 'Salvando edicao'
        id = request.POST.get("id")
        atleta = Atleta.objects.get(pk=id)
    #Inserindo
    else:
        print 'salvando novo registro'
        atleta = Atleta()

    formAtletaInfo = AtletaForm(request.POST,instance=atleta)

    if formAtletaInfo.errors:
        return render(request,"speedapp/atletaDetailInformacoes.html",{"formAtletaInfo":formAtletaInfo,
                                                                       "errros":formAtletaInfo.errors})
    else:
        formAtletaInfo.save()
        return HttpResponseRedirect("/speedapp/atletas/" + str(atleta.id))

def saveNovoAtletaInfo(request):
    return saveAtletaInfo(request,False)

#Deletes
def deleteTeste(request,id):
    Teste.objects.get(pk=id).delete()
    return HttpResponseRedirect("/speedapp/testes/")

def deleteAresta(request,id_teste,id_aresta):
    teste = Teste.objects.get(pk=id_teste)
    aresta = Aresta.objects.filter(teste=teste,id=id_aresta)
    aresta.delete()
    return HttpResponseRedirect("/speedapp/testes/" + str(id_teste) + "/arestas")

def deleteAtleta(request,id_atleta):

    if id_atleta:
        atleta = Atleta.objects.get(pk=id_atleta)

        #Eliminar todos os testes realizados pelo atleta
        for at in AtletaTeste.objects.filter(atleta=atleta):
            at.teste.delete()
            at.delete()

        atleta.delete()

    return HttpResponseRedirect("/speedapp/atletas/")

#Gerais
def resetTeste(request,id_atleta,id_teste):

    teste = Teste.objects.get(pk=id_teste)
    atleta = Atleta.objects.get(pk=id_atleta)

    if teste and atleta:
        #reset
        teste.volta_set.all().delete()
        teste.voltas_realizadas = 0
        teste.tempo = 0
        teste.testeFinalizado = False
        teste.save()
        #volta ao teste

    #Retorna pra detalhes do teste do atleta
    return redirect(views.AtletaTesteDetail,id_atleta=id_atleta,id_teste=id_teste)

def monitorarAtletaTeste(request,id_atleta,id_teste):
    teste = Teste.objects.get(pk=id_teste)
    atleta = Atleta.objects.get(pk=id_atleta)

    #Assasinar todas as tasks ja em execucao
    assasinoDeTasks(teste)

    iniciarTesteTask.delay(atleta,teste)
    return render(request,"speedapp/monitorarTeste.html",{'teste':teste,
                                                          'atleta':atleta})
    #return redirect(views.AtletaTesteDetail,id_atleta=id_atleta,id_teste=id_teste)

def assasinoDeTasks(teste):
    keyTesteObjeto   = teste.keyTesteObjeto + str(teste.id)
    keyMonitoraTeste = teste.keyMonitoraTeste
    keyIniciaColeta  = teste.keyIniciaColeta
    keyObservador    = teste.keyObservador

    #Busca tasks no Redis
    monitoraTesteTaskId = Redis.conexao().get(keyMonitoraTeste)
    iniciaColetaTaskId  = Redis.conexao().get(keyIniciaColeta)
    observadorTaskId = Redis.conexao().get(keyObservador)


    #Kill tasks existentes
    if monitoraTesteTaskId != '':
        taskResult = AsyncResult(monitoraTesteTaskId)
        #if not taskResult.ready():
        print 'Ja existia uma task de monitoramento: KILL'
        task.control.revoke(monitoraTesteTaskId, terminate=True, signal='SIGKILL')

    time.sleep(0.5)
    if iniciaColetaTaskId != '':
        taskResult = AsyncResult(iniciaColetaTaskId)
        #if not taskResult.ready():
        print 'Ja existia uma task de coleta: KILL'
        task.control.revoke(iniciaColetaTaskId,terminate=True, signal='SIGKILL')

    time.sleep(0.5)
    if observadorTaskId != '':
        taskResult = AsyncResult(observadorTaskId)
        #if not taskResult.ready():
        print 'Ja existia uma task de observacao: KILL'
        task.control.revoke(observadorTaskId,terminate=True, signal='SIGKILL')

    time.sleep(0.5)