from celery.decorators import task
from celery import task
from celery.result import AsyncResult
from billiard.exceptions import Terminated

from models import *
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher
import time
from datetime import datetime

from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

import views
import redis
import json
import pickle

@task()
def iniciarTesteTask(atleta,teste):
    keyTesteObjeto   = teste.keyTesteObjeto + str(teste.id)
    keyMonitoraTeste = teste.keyMonitoraTeste
    keyIniciaColeta  = teste.keyIniciaColeta
    keyObservador    = teste.keyObservador

    #Zerar objetos no Redis
    print 'Zerando objetos no Redis'
    Redis.conexao().set(keyTesteObjeto,'')

    #Inicializa o objeto teste
    print 'Reinicializar o teste'
    views.resetTeste(None,atleta.id,teste.id);

    #Iniciar
    print 'Iniciando teste...'
    result = iniciaTeste.delay(teste,atleta)
    Redis.conexao().set(keyIniciaColeta,result.id) #Armazena no Redis o ID da task

    #Monitorar
    print 'Iniciando monitoramento...'
    result = monitoraTeste.delay(teste)
    Redis.conexao().set(keyMonitoraTeste,result.id) #Armazena no Redis o ID da task

    print 'Finalizou chamada de TASKs'

@task(bind=True)
def iniciaTeste(self,teste,atleta):

    #Recupera o objeto Atleta + Teste
    atletaTeste = AtletaTeste.objects.filter(teste=teste,atleta=atleta).first()

    #Inicia coleta BPM
    #coletaBPM.run(teste)

    #Temperatura e umidade
    coletaTemperaturaUmidade.delay(teste)

    #Inicia
    atletaTeste.iniciaTeste()
    atletaTeste.teste.save()

@task(bind=True)
def monitoraTeste(self,teste):
    #Monitoramento do teste
    #Observar as mudancas no objeto TESTE armazenados no REDIS.
    #As mudancas atualizadas do objeto sao encaminhadas para varios sockets com objetivo de atualizar
    #a camada de visualizacao nos clientes conectados aos respectivos sockets# .
    totalDeteccoes = 0

    #Atualiza view:cabecalho do monitoramento
    cabecalho = json.dumps({"testeSituacao":True,"testeStatus": "Inicializando..."})
    RedisPublisher(facility='wsTesteCabecalho', broadcast=True).publish_message(cabecalho)

    # Monitorar
    print 'Monitorando teste ' + str(teste.id)

    iniciou = False
    totalDeteccoes = 0

    while True:
        #Recuperar objeto TESTE aramazenado armazenado no REDIS
        testeKeyRedis = "teste:" + str(teste.id)
        testePickle =  Redis.conexao().get(testeKeyRedis) # recarrega objeto atualizado do redis



        #Existe instancia de teste no Redis?
        if testePickle != None and testePickle != '':
            teste = pickle.loads(testePickle) #converte objeto formato pickle para django

            if teste.testeFinalizado:
                jsonDoTeste = monitoraTesteConstruirJSONDoTeste(teste)
                #Atualiza detalhes do teste
                RedisPublisher(facility='wsTeste', broadcast=True).publish_message(json.dumps(jsonDoTeste))

                break

            #Teste iniciado?
            if teste.tempo > 0 and iniciou == False:
                iniciou = True

            if iniciou == True:
                jsonDoTeste = monitoraTesteConstruirJSONDoTeste(teste)

                totalDeteccoesGravadas = monitoraTesteTotalDeteccoes(teste)
                deteccao = False
                if totalDeteccoes != totalDeteccoesGravadas:
                    totalDeteccoes = totalDeteccoesGravadas
                    deteccao = True
                else:
                    deteccao = False

                #Atualiza cabecalho do teste
                cabecalho = json.dumps({"testeSituacao":False, "testeStatus":teste.status, "testeDeteccao":deteccao})
                RedisPublisher(facility='wsTesteCabecalho', broadcast=True).publish_message(cabecalho)

                #Atualiza detalhes do teste
                RedisPublisher(facility='wsTeste', broadcast=True).publish_message(json.dumps(jsonDoTeste))


            #Atualiza cabecalho do teste
            cabecalho = json.dumps({"testeSituacao":False, "testeStatus":teste.status})
            RedisPublisher(facility='wsTesteCabecalho', broadcast=True).publish_message(cabecalho)


    #Apos finalizacao do teste
    cabecalho = json.dumps({"testeSituacao":False, "testeStatus":teste.status})
    RedisPublisher(facility='wsTesteCabecalho', broadcast=True).publish_message(cabecalho)

    print 'Finalizou monitoramento teste ' + str(teste.id)

def monitoraTesteConstruirJSONDoTeste(teste):
    json = {}

    voltas = monitoraTesteConstruirJSONDasVoltas(teste)

    json["voltas"] = voltas
    json["testeFinalizado"] = False
    if teste.testeFinalizado:
        json["testeFinalizado"] = True
        json["tempoTotalTeste"] = teste.tempo - teste.tempoInicial
    else:
        json["tempoTotalTeste"] = time.time() - teste.tempoInicial

    json["qtdVoltas"] = teste.qtdVoltas
    json["voltasRealizadas"] = teste.voltas_realizadas
    json["bpm"] = teste.bpm
    json["temperatura"] = teste.temperatura
    json["umidade"] = teste.umidade

    return json

def monitoraTesteConstruirJSONDasVoltas(teste):
    voltas = []
    #Atualizar tempo apenas da volta em andamento
    for v in teste.volta_set.all().extra(order_by = ['-numero']):
        voltaJSON = {}
        if v.numero == teste.voltas_realizadas:
            if teste.testeFinalizado:
                v.tempoDecorrido = v.tempoTotal
            else:
                v.tempoDecorrido = time.time() - v.tempoInicial
        else:
            v.tempoDecorrido = v.tempoTotal

        voltaJSON["numero"]         = v.numero
        voltaJSON["tempoDecorrido"] = v.tempoDecorrido
        voltaJSON["velocidadeMedia"]= v.velocidadeMedia
        voltaJSON["velocidadeGeral"]= v.velocidadeGeral
        voltas.append(voltaJSON)

    return voltas

def monitoraTesteTotalDeteccoes(teste):
    #Total de detecoes de todas as voltas ate o momento
    deteccoes = 0

    #Atualizar tempo apenas da volta em andamento
    for v in teste.volta_set.all().extra(order_by = ['-numero']):
        #Todas as deteccoes da volta
        for d in v.deteccao_set.all():
            deteccoes += 1
    return deteccoes

@task(bind=True)
def monitoraSensores(self, sensores):

    #Iniciliza interface dos pinos
    RaspIO.setWarnings(False)
    RaspIO.setOperationMode('BCM')
    for s in sensores:
        RaspIO.setInterfacePinInput(s.pinoFisico)


    Redis.conexao().set('task:monitoraSensores','false')
    time.sleep(1)
    Redis.conexao().set('task:monitoraSensores','true')

    #Enquanto a chave nao for alterada no redis
    print '###########   Iniciou monitoramento de sensores  ############'

    while Redis.conexao().get('task:monitoraSensores') == 'true':

        sensoresJSON = []

        for s in sensores:

            if RaspIO.getInput(s.pinoFisico):
                #print 'Reconhecido pino ' + str(s.pinoFisico)
                #marca sensor como ativo
                s.ativo = True

                #Salvar
                s.dataUltimoReconhecimento = timezone.now()
                s.save()
            else:
                s.ativo = False

            sensorJSON = {}
            sensorJSON["numero"] = str(s.numero)
            sensorJSON["ativo"] = str(s.ativo)
            sensorJSON["dataUltimoReconhecimento"] = s.dataUltimoReconhecimento.strftime("%d/%m/%Y %H:%M:%S")

            sensoresJSON.append(sensorJSON)

        RedisPublisher(facility='monitoraSensores', broadcast=True).publish_message(json.dumps(sensoresJSON))


        # #Envia view com sensores atualizados
        # sensoresView = render(None,"speedapp/sensores.html",{"sensores":sensores})

    print 'Finalizou monitoramento de sensores'

@task(bind=True)
def coletaBPM(self,teste):

    #Processa BPM enquanto o teste estiver sendo executado
    #As informacoes coletadas devem ser gravadas no REDIS

    print "Iniciou TASK coleta BPM..."

    #Inicia o processo de calculo de BPM
    pulseSensor = hardware.PulseSensor()
    pulseSensor.monitorarPulseSensor()

    while True:
        #Recuperar objeto TESTE aramazenado armazenado no REDIS
        testeKeyRedis= 'teste:' + str(teste.id) + ''
        testePickle = Redis.conexao().get(testeKeyRedis) # recarrega objeto atualizado do redis

        #Existe instancia de teste no Redis?
        if testePickle != None and testePickle != '':
            teste = pickle.loads(testePickle) #converte objeto formato pickle para django

            if teste.testeFinalizado:
                #Finalizar processando do BPM
                pulseSensor.finalizar = True
                break

            #So comeca medir depois da largada
            if teste.largadaRealizada:
                Redis.conexao().set("BPM",pulseSensor.BPM)

    print "Finalizou TASK coleta BPM!"

@task(bind=True)
def coletaTemperaturaUmidade(self,teste):

    print "Iniciou TASK coleta temperatura e umidade..."

    sensorDHT22 = hardware.SensorDHT22()
    sensorDHT22.getValues()
    Redis.conexao().set("Temperatura",sensorDHT22.getTemperatura())
    Redis.conexao().set("Umidade",sensorDHT22.getUmidade())

    print "Finalizou TASK coleta temperatura e umidade!"


