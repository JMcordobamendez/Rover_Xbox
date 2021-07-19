#Código de prueba para publicar usando la librería paho.mqtt.client
import ssl, sys, socket
import paho.mqtt.client as mqtt
import xbox
from time import time
#Inicializo mando xbox
joy = xbox.Joystick()
#Velocidad máxima
Nmax = 100
k_giro = 0.4
#Que solo tenga 2 decimales los valores del joystick
#def fmtFloat(n):
#    return '{:6.2f}'.format(n)

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
def on_publish(client,userdata,result):             #create function for callback
    print(Nd,Ni,B)
    pass
Host_raspberry = '192.168.43.84' #Puede ser otro, cambiar de forma manual
#Inicializo el publicador de MQTT
client = mqtt.Client(client_id='Josemi_pub', clean_session=False)
client.on_connect = on_connect
#client.on_message = on_message
client.on_publish = on_publish 
client.connect(host = Host_raspberry, port=1883)
t2 = time()
cont = 0
#Bucle infinito de envio de mensajes
while keep_going:
    #Código:
    t1 = time()
    if (t1 - t2) > 0.2:
        N_recto = joy.rightY()
        N_giro = joy.rightX()
        Nd = round(Nmax*(N_recto - k_giro*N_giro), 2)
        Ni = round(Nmax*(N_recto + k_giro*N_giro), 2)
        B = joy.Back()
        dato_envio = '{},{},{}'.format(Nd, Ni, B)
        #dato_envio = 'ON'
        client.publish('prueba', dato_envio)
        #print(Nd,Ni)
        t2 = t1
        if B == 1:
            cont = cont + 1
            if cont == 4:
                break
#Terminamos cerrando el mando
client.loop_stop()
joy.close()
