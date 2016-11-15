import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
from threading import Thread


# Interface de comunicacao com o conversor analogico
class ConversorADC:
    SPICLK = 18
    SPIMISO = 23
    SPIMOSI = 24
    SPICS = 25

    def __init__(self):
        self.configuraADC();

    def configuraADC(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # set up the SPI interface pins
        GPIO.setup(self.SPIMOSI, GPIO.OUT)
        GPIO.setup(self.SPIMISO, GPIO.IN)
        GPIO.setup(self.SPICLK, GPIO.OUT)
        GPIO.setup(self.SPICS, GPIO.OUT)

    def lerADC(self, canal):
        mcp = Adafruit_MCP3008.MCP3008(clk=self.SPICLK,
                                       cs=self.SPICS,
                                       miso=self.SPIMISO,
                                       mosi=self.SPIMOSI)
        return mcp.read_adc(canal)  # Ler valor no canal zero


class PulseSensor:
    BPM = 0
    pulsePin = 0
    Signal = 0
    IBI = 600
    Pulse = False
    QS = False

    # Uteis
    conversorADC = None
    finalizar = False

    def __init__(self):
        self.conversorADC = ConversorADC()

    def lerSinal(self):
        return self.conversorADC.lerADC(self.pulsePin)

    def monitorarPulseSensor(self):
        # Iniciar a leitura
        th = Thread(target=self.interrupt)
        th.start()
        print "Iniciou BPM..."

    def interrupt(self):
        rate = []  # array to hold last ten IBI values
        sampleCounter = 0  # used to determine pulse timing
        lastBeatTime = 0  # ultimo tempo da batida
        P = 512  # utilizado para identificar um pedaco do padrao de onda da batida
        T = 512  # utilizado para identificar o padrao de onda da batida
        thresh = 525  # utilizado para identificar o exato momento da batida
        amp = 100  # used to hold amplitude of pulse waveform, seeded
        firstBeat = True  # used to seed rate array so we startup with reasonable BPM
        secondBeat = False  # used to seed rate array so we startup with reasonable BPM

        # Inicializa lista
        for i in range(0, 10):
            rate.append(0)

        runningTotal = 0

        while not self.finalizar:

            time.sleep(0.25)

            #Ler o sinal do sesnor
            self.Signal = self.lerSinal()

            sampleCounter += 250  # Trajetoria do tempo em mS
            N = sampleCounter - lastBeatTime  # monitorar o tempo desde a ultima batida

            # Encontrar o pico da batida
            if self.Signal < thresh and N > (self.IBI / 5) * 3:
                if self.Signal < T:
                    T = self.Signal

            if self.Signal > thresh and self.Signal > P:
                P = self.Signal

            if N > 250:
                if self.Signal > thresh and self.Pulse == False and N > (self.IBI / 5) * 3:
                    self.Pulse = True
                    self.IBI = sampleCounter - lastBeatTime
                    lastBeatTime = sampleCounter

                    if secondBeat:
                        secondBeat = False
                        for i in range(0, 9):
                            rate[i] = self.IBI

                    if firstBeat:
                        firstBeat = False
                        secondBeat = True

                    runningTotal = 0

                    for i in range(0, 8):
                        rate[i] = rate[i + 1]
                        runningTotal += rate[i]

                    rate[9] = self.IBI
                    runningTotal += rate[9]
                    runningTotal /= 10
                    self.BPM = 60000 / runningTotal
                    self.QS = True

            if self.Signal < thresh and self.Pulse:
                self.Pulse = False  # reset the Pulse flag so we can do it again
                amp = P - T  # get amplitude of the pulse wave
                thresh = amp / 2 + T  # set thresh at 50% of the amplitude
                P = thresh  # reset these for next time
                T = thresh

            if N > 2500:  # if 2.5 seconds go by without a beat
                thresh = 512  # set thresh default
                P = 512  # set P default
                T = 512  # set T default
                lastBeatTime = sampleCounter  # bring the lastBeatTime up to date
                firstBeat = True  # set these to avoid noise
                secondBeat = False  # when we get the heartbeat back
                self.BPM = 0

        print "Finalizou BPM"


class SensorDHT22():
    pino = 17
    temperatura = 0
    umidade = 0
    sensor = None

    def __init__(self):
        self.sensor = Adafruit_DHT.DHT22

    def read(self):
        self.umidade, self.temperatura = \
            Adafruit_DHT.read_retry(self.sensor,
                                    self.pino)

    def getValues(self):
        self.temperatura = 0
        self.umidade = 0

        comecouEm = time.time()
        while self.temperatura == 0 and self.umidade == 0:
            self.read()

            # Tempo maximo de dois segundos pra identificar os valores
            if time.time() - comecouEm >= 2:
                break

    def getUmidade(self):
        return self.umidade

    def getTemperatura(self):
        return self.temperatura
