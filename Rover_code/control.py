import RPi.GPIO as GPIO
from time import time

#Creamos una clase para controlar los motores de las ruedas

class Control():
    def __init__(self, encoder_d = 14, encoder_i = 15, pwm_d = 18, pwm_i = 12, dir_da =26,dir_db = 19, dir_ia =13, dir_ib = 6, T_muestreo = 0.03, N_muerto = 5):
        #Inicializamos la nomenclatura de los pines y evitamos el error por posible uso de los pines
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #Inicializamos los pines como entradas o salidas
        GPIO.setup(encoder_d, GPIO.IN)
        GPIO.setup(encoder_i, GPIO.IN)
        GPIO.setup(pwm_d, GPIO.OUT)
        GPIO.setup(pwm_i, GPIO.OUT)
        GPIO.setup(dir_da, GPIO.OUT)
        GPIO.setup(dir_db, GPIO.OUT)
        GPIO.setup(dir_ia, GPIO.OUT)
        GPIO.setup(dir_ib, GPIO.OUT)
        #Entrada digital del encoder óptico con PULL_DOWN
        self.encoder_d = encoder_d
        self.encoder_i = encoder_i
        #Salida PWM para controlar la tensión en los motores [0 - 100] %
        self.pwm_d =  GPIO.PWM(pwm_d, 1000)# f = 1 KHz 
        self.pwm_i = GPIO.PWM(pwm_i, 1000)
        self.pwm_d.start(0)
        self.pwm_i.start(0)
        #Salidas digitales para controlar el sentido de giro "L293D"
        self.dir_da = dir_da
        self.dir_db = dir_db
        self.dir_ia = dir_ia
        self.dir_ib = dir_ib
        #Inicializar Estados encoder
        self.estf_d = GPIO.input(self.encoder_d)
        self.est0_d = self.estf_d
        self.cmb_d = 0
        self.estf_i = GPIO.input(self.encoder_i)
        self.est0_i = self.estf_i
        self.cmb_i = 0
        #Inicializar velocidades
        self.N_d = 0
        self.N_i = 0
        self.N_muerto = N_muerto #rev/min
        self.T_muerto = ((1/20)/(N_muerto))*60 #no detecta nada inferior a ese tiempo
        #Inicializo sentido de giro
        self.g_d = True #Sentido positivo
        self.g_i = True
        #Inicializamos filtro digital
        self.tau = 0.019894 #Frecuencia de corte = 8 Hz
        self.N_d_digital = 0 #Velocidad filtrada
        self.N_i_digital = 0
        self.N_d_ans = 0 #Velocidad sin filtrar anterior
        self.N_i_ans = 0
        #Inicializa el controlador
        self.err_d = 0 #Error
        self.err_d_ans = 0 #Error anterior
        self.err_i = 0
        self.err_i_ans = 0
        self.KP = 0.015*0.2 #0.015*0.25
        self.Ti = 0.025 #0.025
        self.U_d = 0 #Salida de control (Voltios)
        self.U_i = 0
        self.U_sat = 8.4 #Tensión de saturación
        #Inicializar tiempos
        self.T = T_muestreo
        self.tf = None
        self.t0_d = time() #Tiempo en segundos
        self.t0_i = self.t0_d
        self.t_c = self.t0_d #Tiempo que se actualizará cuando se supere el tiempo de muestreo, es el tiempo del controlador
        
    #Realiza una actualización sobre el valor de la velocidad en las ruedas
    def leer(self):
        #Comprobamos el estado del encoder
        self.estf_d = GPIO.input(self.encoder_d)
        self.estf_i = GPIO.input(self.encoder_i)
        self.tf = time()
        #Si las ruedas están paradas
        #Rueda derecha
        if (self.tf - self.t0_d) >= self.T_muerto:
            self.t0_d = self.tf
            self.N_d = 0 #rev/min
        #Rueda izquierda
        if (self.tf - self.t0_i) >= self.T_muerto:
            self.t0_i = self.tf
            self.N_i = 0 #rev/min
        #Si las ruedas están en movimiento
        #Se produce cambio de estado Luz/Sombra
        #Rueda derecha
        if self.estf_d != self.est0_d and self.cmb_d == 0:
            self.cmb_d = 1 #Se ha producido cambio de estado
        #Rueda Izquierda
        if self.estf_i != self.est0_i and self.cmb_i == 0:
            self.cmb_i = 1 #Se ha producido cambio de estado
        #Sombra/Luz
        #Rueda derecha
        if self.estf_d == self.est0_d and self.cmb_d == 1:
            #Cada transición es 1/20 rev
            self.N_d = ((1/20)/(self.tf - self.t0_d))*60 # rev/min
            self.cmb_d = 0 #Volvemos a estado inicial
            self.t0_d = self.tf # actualizamos el tiempo
        #Rueda izquierda
        if self.estf_i == self.est0_i and self.cmb_i == 1:
            #Cada transición es 1/20 rev
            self.N_i = ((1/20)/(self.tf - self.t0_i))*60 # rev/min
            self.cmb_i = 0 #Volvemos a estado inicial
            self.t0_i = self.tf # actualizamos el tiempo
    
    #Filtro digital paso de bajas de primer orden "Tustin"
    def filtro(self, Y_out_ans, Y_in, Y_in_ans):
        Y_out = (1/(self.T + 2*self.tau))*(- Y_out_ans*(self.T - 2*self.tau) + self.T*Y_in + self.T*Y_in_ans)
        return Y_out, Y_in
    
    #Controlador PI digital "Tustin"
    def PI(self, U_ans, err, err_ans):
        U = (1/(2*self.Ti))*(2*self.Ti*U_ans + self.KP*(2*self.Ti + self.T)*err + self.KP*(self.T - 2*self.Ti)*err_ans)
        return U, err
        
    
    #Fija la referencia en velocidad de ambos motores
    def ref(self, ref_N_d, ref_N_i):
        #Primero Conocer la Velocidad de los Motores
        self.leer()
        #Si el giro es negativo invertir el valor de la velocidad (el encoder óptico no detecta la dirección de giro)
        if ref_N_d < 0 and self.N_d > 0:
            self.N_d = - self.N_d
        if ref_N_i < 0 and self.N_i > 0:
            self.N_i = - self.N_i
        #Si el giro es positivo y la velocidad negativa, invertir el valor de la velocidad
        if ref_N_d > 0 and self.N_d < 0:
            self.N_d = - self.N_d
        if ref_N_i > 0 and self.N_i < 0:
            self.N_i = - self.N_i
        #Comprobar que el controlador ha superado el tiempo de muestro
        if (self.tf - self.t_c) >= self.T:
            self.t_c = self.tf #Actualiza el tiempo del último muestreo
            #Filtramos Las velocidades
            #Motor derecho
            self.N_d_digital, self.N_d_ans = self.filtro(self.N_d_digital, self.N_d, self.N_d_ans)
            #Motor izquierdo
            self.N_i_digital, self.N_i_ans = self.filtro(self.N_i_digital, self.N_i, self.N_i_ans)
            #print(self.N_d_digital,'||', self.N_i_digital,'#',self.tf)
            #Error respecto a la referencia (Velocidad)
            self.err_d = ref_N_d - self.N_d_digital #Error motor derecho
            self.err_i = ref_N_i - self.N_i_digital #Error motor izquierdo
            #Introducimos el error al controlador
            self.U_d, self.err_d_ans = self.PI(self.U_d, self.err_d, self.err_d_ans) #Motor derecho
            self.U_i, self.err_i_ans = self.PI(self.U_i, self.err_i, self.err_i_ans) #Motor izquierdo
            #Si la tensión es negativa hay que invertir el sentido de giro
            #Sentido Positivo
            if self.U_d >= 0:
                GPIO.output(self.dir_da, GPIO.HIGH) #Pon a 1
                GPIO.output(self.dir_db, GPIO.LOW) #Pon a 0
                if self.U_d > self.U_sat:
                    self.U_d = self.U_sat #Si la tensión es mayor que la batería sature
                self.pwm_d.ChangeDutyCycle(round( (self.U_d/self.U_sat)*100 ))
                self.g_d = True #Sentido positivo
            #Sentido negativo
            elif self.U_d < 0:
                self.U_d = - self.U_d #Cambiar signo a positivo
                GPIO.output(self.dir_da, GPIO.LOW) #Pon a 0
                GPIO.output(self.dir_db, GPIO.HIGH) #Pon a 1
                if self.U_d > self.U_sat:
                    self.U_d = self.U_sat #Si la tensión es mayor que la batería sature
                self.pwm_d.ChangeDutyCycle(round( (self.U_d/self.U_sat)*100 ))
                self.U_d = - self.U_d #Cambiar a signo negativo (el controlador necesita la magnitud negativa)
                self.g_d = False #Sentido negativo
            #Sentido Positivo
            if self.U_i >= 0:
                GPIO.output(self.dir_ia, GPIO.HIGH) #Pon a 1
                GPIO.output(self.dir_ib, GPIO.LOW) #Pon a 0
                if self.U_i > self.U_sat:
                    self.U_i = self.U_sat #Si la tensión es mayor que la batería sature
                self.pwm_i.ChangeDutyCycle(round( (self.U_i/self.U_sat)*100 ))
                self.g_i = True #Sentido positivo
            #Sentido negativo
            elif self.U_i < 0:
                self.U_i = - self.U_i #Cambiar a signo positivo
                GPIO.output(self.dir_ia, GPIO.LOW) #Pon a 0
                GPIO.output(self.dir_ib, GPIO.HIGH) #Pon a 1
                if self.U_i > self.U_sat:
                    self.U_i = self.U_sat #Si la tensión es mayor que la batería sature
                self.pwm_i.ChangeDutyCycle(round( (self.U_i/self.U_sat)*100 ))
                self.U_i = - self.U_i #Cambiar a signo negativo (el controlador necesita la magnitud negativa)
                self.g_i = False #Sentido negativo
                #Algo
    def close(self):
        #Ponemos a 0 todos los pines para evitar posibles cortos
        self.pwm_d.stop() #PWM 0
        self.pwm_i.stop() #PWM 0
        GPIO.output(self.dir_da, GPIO.LOW) #Pon a 0
        GPIO.output(self.dir_db, GPIO.LOW) #Pon a 0
        GPIO.output(self.dir_ia, GPIO.LOW) #Pon a 0
        GPIO.output(self.dir_ib, GPIO.LOW) #Pon a 0
        print('Pines puestos a 0')
        
            
