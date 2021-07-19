#Código de prueba para suscribirse usando la librería paho.mqtt.client
import ssl, sys, socket, threading
from control import Control
import paho.mqtt.client as mqtt
from crear_broker import Broker
from time import time
#Inicialiazo Variables para controlar la velocidad
Nd, Ni, stop = 0, 0, 0
#Inicializar broker de mqtt
broker = Broker()
broker.crear()
keep_going = True
def manejador_de_senal(signum, frame):
    global keep_going
    # Si entramos en el manejador por una llamada CTRL-C, ponemos el flag a False
    keep_going = False

#Ejecuta cuando se ha conectado con éxito
def on_connect(client, userdata, flags, rc):
	print('connected (%s)' % client._client_id)
	client.subscribe(topic = 'prueba', qos = 2) #qos = 0 para que no se produzca mucho lag

#Ejecuta cuando recibe el mensaje
def on_message(client, userdata, message):
    global Nd, Ni, stop #Valores de velocidad 
    info = str(message.payload)
    info = info.split("'")
    info = info[1]
    Nd, Ni, stop = info.split(",")
    Nd = float(Nd)
    Ni = float(Ni)
    stop = int(stop)
#Inicializo el controlador
control = Control()
#Inicializa el MQTT
client = mqtt.Client(client_id='Car_control', clean_session=False)
client.on_connect = on_connect
client.on_message = on_message
client.connect(host = socket.gethostbyname(socket.gethostname()+'.local'), port=1883)
#Escucha la recepción en MQTT, este bucle se ejecutará en paralelo al control creando un hilo
def escucha():
    while Keep_going:
        client.loop()
#Inicializamos el hilo de escucha
escuchar = threading.Thread(target = escucha)
#escuchar.start() #Se crea el hilo de escucha
client.loop_start()
t2 = time()
while keep_going:
    #Recibo mensaje
    #tl = time()
    #client.loop()
    t1 = time()
    try:
        control.ref(Nd, Ni)
        if (t1 - t2) > 0.2:
            t2 = t1
            #control.ref(Nd, Ni)
            print('{}|{}  {}|{}'.format(Nd,Ni,control.N_d,control.N_i))
            #print(t1 - tl)
        if stop == 1:
            break
    except:
        print('Fallo {}|{}'.format(Nd,Ni))
control.close()
broker.terminar()
