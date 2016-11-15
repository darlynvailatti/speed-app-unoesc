from __future__ import unicode_literals
from django.db import models
from django.core.files import File
from django.utils import timezone
from django.core import serializers
from celery.decorators import task
from celery import task
from collections import deque


#SpeedProjetct
import hardware

#Gerais
import RPi.GPIO as GPIO
import time
import datetime
import redis
import pickle
import os

#Especificas
from threading import Thread
from multiprocessing import Process
from pygame import mixer


class Desporto(models.Model):
    descricao = models.CharField(max_length=100,null=False)

    def __str__(self):
        return self.descricao

class AtletaManager(models.Manager):
    def create_atleta(self,nome,sobreNome,dataNascimento,desporto):
        atleta = self.create(nome = nome,
                             sobreNome  = sobreNome,
                             dataNascimento  = dataNascimento,
                             desporto = desporto,
                             )
        return atleta

class Atleta(models.Model):
    nome = models.CharField(max_length=120,null=False)
    sobreNome = models.CharField(max_length=50,null=True)
    dataNascimento = models.DateTimeField(null=False)
    desporto = models.ForeignKey(Desporto, on_delete=models.CASCADE)

    #Manager
    objects = AtletaManager()

    def getIdade(self):
        return True

class AtletaAtributos(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    dataHora = models.DateTimeField(null=False)
    pesoEmKg = models.FloatField(null=False)

class TesteObservador():

    tempoDetecao   = 0
    totalDeteccoes = 0

    @task(bind=True)
    def observar(self,teste):

        '''
        Processo responsavel por observar as deteccoes nos sensores e entao atualizar
        no REDIS o objeto TESTE, para serem consumidos pelo "Processer".
        O "Processer" tambem atualiza o objeto TESTE no REDIS, em determinados
        momento ambos os lados (observer & processor) compartilham atributos de controle
        do mesmo objeto (TESTE).
        '''

        print "Iniciou observador do Teste..."

        #Inicia parametros GPIO
        teste.iniciaParametrosGPIOParaOsPinosDasArestas()

        tempoDetecao   = 0
        totalDeteccoes = 0

        while not teste.testeFinalizado:

            for s in teste.getSequenciaDeSensoresASeremObservados():

                #Observar
                tempoDetecao = 0
                while not s.detectou():

                    if teste.consideraTimeout():
                        if teste.ultrapassouTempoLimite():
                            tempoDetecao = time.time()
                            teste.testeTimeout()
                            teste.atualizaObjetoNoRedis()
                            break

                    #MUITO IMPORTANTE
                    # - Verificar se teste ja foi finalizado
                    # - Verificar se largada ja foi realizada
                    # - Verificar o tempo inicial do teste (que soh acontece no processo de largada)
                    testeAtualizadoNoRedis = teste.getTesteFromRedis()

                    if testeAtualizadoNoRedis != None:

                        #Atualiza o status
                        teste.status           = testeAtualizadoNoRedis.status

                        #Verifica se o teste no Redis esta finalizado
                        if testeAtualizadoNoRedis.testeFinalizado:
                            teste.testeFinalizado = True #Garantir a saida do While
                            break

                        #Atualiza atributos de controle do Teste
                        teste.tempoInicial     = testeAtualizadoNoRedis.tempoInicial
                        teste.largadaRealizada = testeAtualizadoNoRedis.largadaRealizada


                    pass

                print "DETECTOU"
                #Aqui onde acontece a magica
                if tempoDetecao == 0:
                    tempoDetecao = time.time()

                totalDeteccoes += 1

                #Criar deteccao
                deteccao = Deteccao()
                deteccao.tempo = tempoDetecao
                deteccao.sensor = s

                #Para cada iteracao de sensor, busca o teste atualizado do Redis
                testeAtualizadoNoRedis = teste.getTesteFromRedis()

                if testeAtualizadoNoRedis != None:
                    if not testeAtualizadoNoRedis.testeFinalizado:
                        #Atualizar ultimo tempo do teste
                        teste.tempo = deteccao.tempo

                    if testeAtualizadoNoRedis != None:
                        #Adicionar deteccao a fila
                        testeAtualizadoNoRedis.filaDeDeteccoes.append(deteccao)
                        testeAtualizadoNoRedis.testeFinalizado = teste.testeFinalizado
                        testeAtualizadoNoRedis.tempo           = teste.tempo

                        if not testeAtualizadoNoRedis.testeFinalizado:
                            testeAtualizadoNoRedis.status          = teste.status

                        #Atualiza objeto no redis
                        testeAtualizadoNoRedis.atualizaObjetoNoRedis()

                        #Espera para proxima deteccao,
                        #pois o sensor pode ficar em HIGH por tempo maior
                        #do que o tempo de loop para vrificar deteccao.
                        #Isso garante que uma unica deteccao nao seja identificada
                        #como completo de todo o trajeto
                        time.sleep(0.2)
                    else:
                        print "Observador: foi perdida uma deteccao!!"


                    #Sair do for de arestas
                    if teste.testeFinalizado:
                        break

class TesteManager(models.Manager):
    def create_teste(self,descricao,origem):
        teste = self.create(descricao         = descricao,
                            origem            = origem,
                            dataHora          = datetime.datetime.today(),
                            voltas_realizadas = 0,
                            temperatura       = 0,
                            umidade           = 0,
                            tempo             = 0,
                            tempoInicial      = 0,
                            qtdVoltas         = 0,
                            testeFinalizado   = False,)
        return teste

class Teste(models.Model):
    ORIGEM_TESTE = (
        ('0', 'modelo'),
        ('1', 'aplicacao'),
    )

    TIPO_TESTE = (
        ('0','Voltas realizadas'),
        ('1','Tempo decorrido')
    )

    origem            = models.CharField(max_length=1, choices=ORIGEM_TESTE)
    tipo              = models.CharField(max_length=1, choices=TIPO_TESTE)
    descricao         = models.CharField(max_length=130,null=True)
    dataHora          = models.DateTimeField(null=True)
    dataHoraExecucao  = models.DateTimeField(null=True)
    temperatura       = models.FloatField(null=True)
    umidade           = models.FloatField(null=True)

    #Atributos de controle
    tempoTotalMax     = models.FloatField(null=True)
    voltas_realizadas = models.IntegerField(null=True)
    tempo             = models.FloatField(null=True)
    tempoInicial      = models.FloatField(null=True)
    qtdVoltas         = models.IntegerField(null=True)
    testeFinalizado   = models.BooleanField()
    status            = models.CharField(max_length=130,null=True)
    largadaRealizada  = False
    bpm               = 0
    filaDeDeteccoes   = deque()
    observador        = TesteObservador()

    #Constantes
    keyObservador    = "taskObservador"
    keyTesteObjeto   = 'teste:'
    keyMonitoraTeste = 'taskMonitora'
    keyIniciaColeta  = 'taskIniciaColeta'

    #Manager
    objects = TesteManager()

    def __str__(self):
        return str(self.descricao)

    def iniciarProcessoDeTeste(self):

        if not self.testeFinalizado:
            #Log
            print "Iniciando coleta..."

            self.testeFinalizado  = False
            self.dataHoraExecucao = timezone.now()
            self.status           = 'Iniciando processo de coleta...'

            #Manter o REDIS informado
            self.atualizaObjetoNoRedis()

            #Chama o processo de coleta
            self.processar()

    def processar(self):
        print "Coleta iniciada!"
        sensor = Sensor(0,0)

        self.largadaRealizada = False

        #Verificar qual o tipo de trajeto
        if self.getTestePontoAPonto():
            #Ponto inicio e fim
            print 'Realizando um teste PONTO-A-PONTO'
            testePontoAPonto = True
            pass
        else:
            #Circuito
            print 'Realizando um teste CIRCUITO'
            testePontoAPonto = False
            pass

        #Inicia observador de sensores
        result = self.observador.observar.delay(self)
        time.sleep(0.5)
        Redis.conexao().set(self.keyObservador,result.id) #Armazena no Redis o ID da task

        #Fila de deteccoes
        self.filaDeDeteccoes = deque()

        #Inicio processo de coleta
        self.tempo = 0

        # ----------------------------------- #
        # INICIO DO TESTE                     #
        # ----------------------------------- #
        while not self.testeFinalizado:

            #Loop de arestas
            for aresta in self.aresta_set.all():

                print "Iterando na aresta: " + str(aresta.sensor_a.numero) + " -> " + str(aresta.sensor_b.numero)

                #Largada
                if self.largadaRealizada == False:

                    self.status = "Esperando largada"
                    self.atualizaObjetoNoRedis()
                    print self.status

                    sensor = aresta.sensor_a

                    #Fica observando o sensor ate identificar uma deteccao ou ate atingir tempo limite
                    self.observaDeteccao()

                    #Remove primeira deteccao presente na fila de deteccoes
                    deteccao = self.filaDeDeteccoes.popleft()

                    #Comecou no tempo = deteccao.tempo
                    self.tempo = deteccao.tempo # Tempo inicio da volta
                    self.tempoInicial = self.tempo #Tempo inicio do teste

                    #Cria volta
                    self.voltas_realizadas = 1
                    teste = self
                    volta = Volta.objects.create_volta(teste, #Teste q esta se realizando
                                                       self.voltas_realizadas, #Numero da volta
                                                       self.tempo
                            )
                    self.volta_set.add(volta)

                    #Medida
                    deteccao = Deteccao.objects.create_deteccao(sensor,
                                                                self.tempo,
                                                                volta)
                    self.volta_set.latest('id').gravaDeteccao(deteccao)
                    self.largadaRealizada = True

                    #Atualiza temperatura e umidade do teste
                    self.temperatura = self.getTemperaturaFromRedis()
                    self.umidade = self.getUmidadeFromRedis()

                    #Vai para proxima aresta se existir mais de uma ou nao for um testePontoAPonto
                    #Se existe apenas uma aresta entao prossegue
                    if len(self.aresta_set.all()) > 1 or not testePontoAPonto:
                        continue


                #Voltas & Chegada
                #Teste finalizado?
                if self.testeFinalizado:
                    break

                '''
                Quando teste PONTO-A-PONTO e for a ultima aresta, esperar tambem uma deteccao no sensor_b da
                respectiva aresta pois nesse modo, a ultima aresta nao conecta-se com nenhuma outra aresta,
                portanto para finalizar o loop do teste eh necessario esperar pela deteccao do sensor_b.

                Exemplo:
                sA:1 -> sB:2
                sA:2 -> sB:3

                Esperar deteccao no sensor sB:3
                '''
                #CHEGADA (Ultima aresta)
                if testePontoAPonto and self.getUltimaAresta().id == aresta.id:
                    #Existe mais de uma aresta?
                    if len(self.aresta_set.all()) > 1:
                        self.status = 'Aguardando deteccao sensor: ' + str(aresta.sensor_a.numero)
                        print self.status
                        self.atualizaObjetoNoRedis()

                        self.observaDeteccao()
                        self.processaDeteccao(aresta.sensor_a)

                    self.status = 'Aguardando deteccao sensor: ' + str(aresta.sensor_b.numero)
                    print self.status
                    self.atualizaObjetoNoRedis()

                    self.observaDeteccao()
                    self.processaDeteccao(aresta.sensor_b)
                else:
                #VOLTAS
                    self.status = 'Aguardando deteccao sensor: ' + str(aresta.sensor_a.numero)
                    print self.status
                    self.atualizaObjetoNoRedis()

                    #Fica observando o sensor ate identificar uma deteccao na fila
                    self.observaDeteccao()
                    self.processaDeteccao(aresta.sensor_a)


                #Atualiza objeto no REDIS
                self.atualizaObjetoNoRedis()


                if self.completouVolta():

                    self.status = 'Completou volta'
                    self.atualizaObjetoNoRedis()
                    print self.status

                    #Atualiza tempo com o tempo da ultima deteccao que foi onde a volta foi completada
                    ultimaDeteccao = Deteccao.objects.latest("id")
                    self.tempo = ultimaDeteccao.tempo

                    #Volta finalizada: Atualiza atributos
                    voltaFinalizada                 = self.volta_set.latest('id')
                    voltaFinalizada.tempoFinal      = self.tempo #Tempo da ultima deteccao
                    voltaFinalizada.tempoTotal      = voltaFinalizada.tempoFinal - voltaFinalizada.tempoInicial

                    #Atualiza dados da volta finalizada
                    voltaNumero = self.voltas_realizadas
                    velocidadeMediaVolta = self.calcularVelocidadeMediaVolta(voltaFinalizada)
                    velocidadeGeralVolta = self.calcularVelocidadeGeralVolta(voltaFinalizada)

                    voltaFinalizada.numero          = voltaNumero
                    voltaFinalizada.velocidadeMedia = velocidadeMediaVolta
                    voltaFinalizada.velocidadeGeral = velocidadeGeralVolta

                    #Persistir
                    voltaFinalizada.save()

                    #atualiza total de voltas
                    print "Voltas realizadas %s" % self.voltas_realizadas
                    self.voltas_realizadas += 1

                    if self.voltas_realizadas <= self.qtdVoltas:
                        #Cria nova volta
                        volta = Volta.objects.create_volta(self, #Teste q se esta realizando
                                                           self.voltas_realizadas,
                                                           self.tempo) #Numero da volta
                        self.volta_set.add(volta)

                        #Ultimo sensor do circuito?
                        if sensor.numero == self.getPrimeiroSensor().numero:
                            #Cria uma detectacao de largada
                            deteccao = Deteccao.objects.create_deteccao(sensor,self.tempo,volta)
                            self.volta_set.latest('id').gravaDeteccao(deteccao)

                        sensor = self.aresta_set.all()[len(self.aresta_set.all()) -1].sensor_b
                    else:
                        self.voltas_realizadas -= 1
                        self.finaliza()

                    #Atualiza objeto no REDIS
                    self.atualizaObjetoNoRedis()

        self.exibirResultadosConsole()

    def getTestePontoAPonto(self):
        return self.getPrimeiroSensor().numero != self.getUltimoSensor().numero

    def completouVolta(self):
        ultimaVolta = self.volta_set.latest('numero')
        ultimaDeteccaoDaUltimaVolta = ultimaVolta.deteccao_set.latest('id')
        ultimaAresta = self.aresta_set.all().latest('id')

        totalVoltasRealizadas             = self.voltas_realizadas
        ultimoSensorDetecadoDaUltimaVolta = ultimaDeteccaoDaUltimaVolta.sensor
        ultimoSensorDoPercurso            = ultimaAresta.sensor_b

        if totalVoltasRealizadas >= 1:
            if ultimoSensorDetecadoDaUltimaVolta.numero == ultimoSensorDoPercurso.numero:
                return True

        return False

    def calcularVelocidadeMediaVolta(self,volta):
        print("Calculando velocidade media da volta: %s" % (volta.numero))
        tempos = []
        temposCheios = []
        tempo = 0
        index = 0

        #Busque todas as deteccoes em order decrescente de ID
        for d in volta.deteccao_set.all().extra(order_by=["-id"]):
            if len(temposCheios) > 0:

                t = temposCheios[index] - d.tempo
                tempos.append(t)
                temposCheios.append(d.tempo)
                index+=1
                print("Tempo calculado: %s (s)" %(t))
            else:
                temposCheios.append(d.tempo)

        #Media
        index = 0
        somaVelocidadeEmMetrosPorSegundo = 0
        for a in self.aresta_set.all().extra(order_by=["-id"]):
            if(index <= len(tempos) - 1):
                somaVelocidadeEmMetrosPorSegundo += (a.distancia / tempos[index])
                index+=1

        mediaVelocidadeDaVolta = somaVelocidadeEmMetrosPorSegundo / len(tempos)
        print("Media calculada: %s (m/s)" %(mediaVelocidadeDaVolta))
        return mediaVelocidadeDaVolta

    def calcularVelocidadeGeralVolta(self,volta):
        print("Calculando velocidade geral da volta: %s" %(volta.numero))
        print("Tempo total: %s | Tempo incial: %s | Tempo final: %s" %(volta.tempoTotal,volta.tempoInicial,volta.tempoFinal))

        if volta.tempoTotal > 0:
            velocidadeGeralDaVolta = self.getDistanciaTotal() / volta.tempoTotal
            print("Velocidade geral calculada: %s (m/s)" %(velocidadeGeralDaVolta))
            return velocidadeGeralDaVolta
        else:
            return 0

    def calcularVelocidadeMedia(self):
        for v in self.volta_set.all():
            pass

    def getTempoCorrenteVolta(self):
        return time.time() - self.tempo

    def getTempoCorrenteTeste(self):
        return time.time() - self.tempoInicial

    def observaDeteccao(self):

        #Enquanto a fila de deteccoes a serem processadas estiver vazia E o teste ainda nao
        #estiver finalizado, buscar objeto atualizado no REDIS
        while len(self.filaDeDeteccoes) == 0 and not self.testeFinalizado:

            #Obtem teste atualizado do redis
            testeAtualizadoNoRedis = self.getTesteFromRedis()

            if testeAtualizadoNoRedis != None:
                #Atualiza atributos de controle comuns entre Observer & Processor
                self.filaDeDeteccoes = testeAtualizadoNoRedis.filaDeDeteccoes
                self.status          = testeAtualizadoNoRedis.status
                self.testeFinalizado = testeAtualizadoNoRedis.testeFinalizado
                self.tempo           = testeAtualizadoNoRedis.tempo

            #Atualizar variaveis externas somente se houve largada
            if self.largadaRealizada:
                self.atualizaVariaveisExternas()

    def processaDeteccao(self,sensor):
        #Remove primeira deteccao presente na fila de deteccoes
        #Aqui pode acontecer que a fila nao possua nenhuma deteccao. Isso ocorre quando
        #o teste tipo = 1 eh iniciado porem nenhum deteccao eh inferida, por isso
        #antes de remover da fila, verificar se existe
        deteccaoTempo = 0
        if len(self.filaDeDeteccoes) > 0:
            deteccao = self.filaDeDeteccoes.popleft()
            deteccaoTempo = deteccao.tempo

        volta = self.volta_set.latest('id')
        deteccao = Deteccao.objects.create_deteccao(sensor,
                                                    deteccaoTempo,
                                                    volta)
        volta.gravaDeteccao(deteccao)

    def consideraTimeout(self):
        #usar TIMEOUT quando teste finalizador = Tempo
        return self.tipo == "1" and self.largadaRealizada

    def testeTimeout(self):
        #Processo de timeout do teste
        self.finaliza()
        self.tempo           = time.time()
        self.status          = "Atingiu tempo limite"

    def ultrapassouTempoLimite(self):
        return self.getTempoCorrenteTeste() > self.tempoTotalMax

    def getDistanciaTotal(self):
        totalDistancia = 0
        for a in self.aresta_set.all():
            totalDistancia += a.distancia

        return totalDistancia

    def exibirResultadosConsole(self):

        print "T.I: %s / T: %s" % (self.tempoInicial, self.tempo)
        print "VOLTAS:"
        for v in self.volta_set.all():
            print "V: %s / T.I: %s" % (v.numero, v.tempoInicial)

            #Detecoes da volta
            for d in v.deteccao_set.all():
                print "Detecao sensor: %s / tempo: %s / volta: %s" % (d.sensor.numero, d.tempo, d.volta.numero)

    def atualizaObjetoNoRedis(self):
        #Gravar teste no redis
        testeKeyRedis = self.getKeyTesteNoRedis()
        Redis.conexao().delete(testeKeyRedis)
        Redis.conexao().set(testeKeyRedis,pickle.dumps(self))

    def finaliza(self):
        self.testeFinalizado = True
        self.status = "Finalizado"

    def getKeyTesteNoRedis(self):
        return 'teste:' + str(self.id)

    def getTesteFromRedis(self):
        testeKeyRedis = self.getKeyTesteNoRedis()
        testePickle = Redis.conexao().get(testeKeyRedis)

        if testePickle != None and testePickle != '':
            return pickle.loads(testePickle)

        return None

    def getBPMFromRedis(self):
        bpm = float(str(Redis.conexao().get("BPM")))

        fMax = 250
        fMin = 40
        if bpm >= fMin and bpm <= fMax:
            #Retorna o BPM armazenado no Redis
            return bpm

        return 0

    def getTemperaturaFromRedis(self):
        return Redis.conexao().get("Temperatura")

    def getUmidadeFromRedis(self):
        return Redis.conexao().get("Umidade")

    def atualizaVariaveisExternas(self):

        #Atualiza BPM para cada iterecao
        #bpmValor = self.getBPMFromRedis()
        #if bpmValor != 0:
            #bpm = Bpm.objects.create_bpm(self,bpmValor,self.getTempoCorrenteTeste())
            #self.bpm_set.add(bpm)

        #Temperatura e umidade atual
        self.temperatura = self.getTemperaturaFromRedis()
        self.umidade = self.getUmidadeFromRedis()

    def iniciaParametrosGPIOParaOsPinosDasArestas(self):
        #Paramns rasp board
        RaspIO.setWarnings(False)
        RaspIO.setOperationMode('BCM')

        #Iniciliaza pinos
        for aresta in self.aresta_set.all():
            RaspIO.setInterfacePinInput(aresta.sensor_a.pinoFisico)
            RaspIO.setInterfacePinInput(aresta.sensor_b.pinoFisico)

    def getSequenciaDeSensoresASeremObservados(self):
        sequenciaSensores = []
        for a in self.aresta_set.all():
            sequenciaSensores.append(a.sensor_a)

        if self.getTestePontoAPonto():
            sequenciaSensores.append(self.getUltimoSensor())

        return sequenciaSensores

    def getUltimaAresta(self):
        return self.aresta_set.latest('id')

    def getPrimeiraAresta(self):
        return self.aresta_set.all()[0]

    def getPrimeiroSensor(self):
        return self.getPrimeiraAresta().sensor_a

    def getUltimoSensor(self):
        return self.getUltimaAresta().sensor_b

    def getPenultimoSensor(self):
        return self.getUltimaAresta().sensor_a


class BpmManager(models.Manager):
    def create_bpm(self,teste,bpm,tempo):
        bpmObj = self.create(teste = teste,
                          bpm   = bpm,
                          tempo = tempo)
        return bpmObj

class Bpm(models.Model):
    teste           = models.ForeignKey(Teste, on_delete=models.CASCADE)
    bpm             = models.IntegerField()
    tempo           = models.FloatField()

    #Manager
    objects = BpmManager()

class AtletaTeste(models.Model):
    atleta            = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    teste             = models.ForeignKey(Teste, on_delete=models.CASCADE)

    #Processa requisicao para inicio de um teste com atleta
    def iniciaTeste(self):

        #O teste do atleta sera processado
        self.teste.iniciarProcessoDeTeste()


class RaspIO:

    @classmethod
    def getInput(self,pino):
        return not GPIO.input(pino)


    @classmethod
    def setWarnings(self,value):
        GPIO.setwarnings(value)


    @classmethod
    def setOperationMode(self,value):
        if value == 'BCM':
            GPIO.setmode(GPIO.BCM)

    @classmethod
    def setInterfacePinInput(self,pinoFisico):
        GPIO.setup(pinoFisico,GPIO.IN,GPIO.PUD_DOWN)

class SensorManager(models.Manager):
    def create_sensor(self,numero,pinoFisico):
        sensor = self.create(numero = numero,
                             pinoFisico = pinoFisico,
                             ativo      = False,)
        sensor.inicializaInterface()
        return sensor

class Sensor(models.Model):
    numero = models.IntegerField()
    pinoFisico = models.IntegerField()
    ativo = models.BooleanField()
    dataUltimoReconhecimento = models.DateTimeField()

    #Manager
    objects = SensorManager()

    def __str__(self):
        return str(self.numero)

    def default(self):
        return self.__dict__

    def sensorEstaAtivo(self):
        return self.ativo

    def inicializaInterface(self):
        RaspIO.setOperationMode('BCM');
        RaspIO.setInterfacePinInput(self.pinoFisico)

    def detectou(self):
        time.sleep(0.01)
        d = RaspIO.getInput(self.pinoFisico)
        print "d = " + str(d)
        return d

class ArestaManager(models.Manager):
    def create_aresta(self,teste,sensor_a,sensor_b,distancia):
        aresta = self.create(teste     = teste,
                             sensor_a  = sensor_a,
                             sensor_b  = sensor_b,
                             distancia = distancia)
        return aresta

class Aresta(models.Model):
    teste     = models.ForeignKey(Teste, on_delete=models.CASCADE)
    sensor_a  = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name="sensor_a",
    )
    sensor_b = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name="sensor_b",
    )
    descricao = models.CharField(max_length=130,null=True)
    distancia = models.FloatField()
    objects   = ArestaManager()

class VoltaManager(models.Manager):
    def create_volta(self,teste,numero,tempoInicial):
        volta = self.create(teste           = teste,
                            numero          = numero,
                            tempoTotal      = 0,
                            velocidadeGeral = 0,
                            velocidadeMedia = 0,
                            tempoInicial    = tempoInicial,
                            tempoFinal   = 0,)
        return volta

class Volta(models.Model):
    teste           = models.ForeignKey(Teste, on_delete=models.CASCADE)
    numero          = models.IntegerField()
    tempoTotal      = models.FloatField()
    velocidadeMedia = models.FloatField()
    velocidadeGeral = models.FloatField()
    tempoInicial    = models.FloatField()
    tempoFinal      = models.FloatField()

    #Manager
    objects = VoltaManager()

    def gravaDeteccao(self,deteccao):
        self.deteccao_set.add(deteccao)

    def getNumero(self):
        return self.numero

class DeteccaoManager(models.Manager):
    def create_deteccao(self,sensor,tempo,volta):
        deteccao = self.create(sensor = sensor,
                               tempo  = tempo,
                               volta  = volta,)
        deteccao.beep()
        return deteccao

class Deteccao(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    tempo = models.FloatField()
    volta = models.ForeignKey(Volta, on_delete=models.CASCADE)

    #Objects
    objects = DeteccaoManager()

    def beep(self):
        #mixer.init()
        #alert = mixer.Sound('/speedapp/static/audio/beep.wav')

        #f = open('/home/pi/Documents/speed_project/speed/speedapp/static/audio/beep.wav', 'w')
        #myfile = File(f)

        #if myfile:
        #    print 'EXISTE'
        #alert.play(loops=100)
        #os.system("aplay /home/pi/Documents/speed_project/speed/speedapp/static/audio/bleep.wav -d 1")
        pass

class Redis():
    host = 'localhost'
    porta = 6379
    senha = ''

    @classmethod
    def conexao(self):
        conexao = redis.Redis(
                    host=self.host,
                    port=self.porta,
                    password=self.senha)
        return conexao


