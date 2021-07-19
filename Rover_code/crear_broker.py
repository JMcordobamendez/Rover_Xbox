# Escribe tu código aquí :-)
#Prueba mqtt
import subprocess # necesito iniciar un subproceso para crear el broker de mqtt
import socket # queremos obtener el host

#Creamos clase para iniciar el mqtt
class Broker():
    def __init__(self, my_IP = 0, p = 0, p2 = 0, conf = 0):
        self.my_IP = my_IP
        self.p = p
        self.p2 = p2
        self.conf = conf
    def crear(self):
        #creamos el archivo de configuración
        self.my_IP = socket.gethostbyname(socket.gethostname()+'.local')
        self.conf = open('mosquitto.conf','w')
        self.conf.write('listener 1883 {}\n'.format(self.my_IP)) #Host del broker
        self.conf.write('allow_anonymous true') #Permitir que se conecte cualquiera
        self.conf.close() #Guardamos la configuración
        self.p = subprocess.Popen(["mosquitto -c mosquitto.conf"], stdout=subprocess.PIPE, shell = True)
    def terminar(self):
        subprocess.run(["rm mosquitto.conf"], shell = True)
        subprocess.run(["pkill mosquitto "], shell = True)
        subprocess.run(["sudo systemctl stop mosquitto"], shell = True)

