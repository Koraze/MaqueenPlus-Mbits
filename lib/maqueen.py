# Librairies
from machine  import Pin, I2C, PWM, ADC
from time     import sleep
from neopixel import NeoPixel
import struct
from tools    import Thread


def __select_value(new, old):
    if new is None :
        return old
    return new


# Classe Maqueen Plus de base
#  -  motor         : Lecture / ecriture de la puissance moteurs
#  -  phares        : Lecture / ecriture des phares
#  -  ground_line   : Lecture du sol 
#  -  ground_analog : Lecture du sol 
#  -  stop          : Arrêt des moteurs
#  -  update        : Force la mise a jour de l'ensemble des paramètres
#


class MaqueenPlusBridge():
    def __init__(self, i2c, addr=0x10, debug=False):
        self.__masque     = bytearray([0x01, 0x02, 0x04, 0x08, 0x10, 0x20])
        self.__cmd        = []
        self.__i2c        = i2c
        self.__addr       = addr
        self.__debug      = debug
        self.__debug_msg  = ""
        
        # Valeurs ecrites / lues sur le maqueen plus
        self.__motors        = [False, 0, 0]
        self.__encoders      = [False, 0, 0]   # V1 uniquement
        self.__compensations = [False, 0, 0]   # V1 uniquement
        self.__pid           = [False, 0]      # V1 uniquement
        self.__line_logique  = [False] + [0]*6
        self.__line_analog   = [False] + [0]*6
        
        # Valeurs imposées
        self.__phares = [0, 0]
        
        # Valeurs max
        self.__max_phares = 7
        self.__max_motors = 255
        
        # Lancement du thread
        self.__Thread = Thread(self.update)
        self.__Thread.start()
        
        # Initialisation de départ
        self.stop()
        self.stop()
        
    def __read_data(self, value):
        value[0] = False
        return value[1:]
        
    def __get_motors(self):
        return self.__read_data(self.__motors)
    
    def __set_motors(self, motorLR): # [L: -255, R: +255, T: 0]
        try :
            motorLR = list(motorLR)
            
            # Si L, R non renseignée, ne pas les changer
            motorLR[0] = __select_value(motorLR[0], self.__motors[1])
            motorLR[1] = __select_value(motorLR[1], self.__motors[2])
            
            # Adaptation des données moteur
            dirL   = 1 + (motorLR[0] < 0)
            dirR   = 1 + (motorLR[1] < 0)
            motorL = min(abs(motorLR[0]), self.__max_motors)
            motorR = min(abs(motorLR[1]), self.__max_motors)
            self.__cmd.append(bytearray([0x00, dirL, motorL, dirR, motorR]))
            
            # Mise à jour auto (si activé)
            if(motorLR[2] > 0):
                sleep(motorLR[2])
                self.stop()
        except :
            return False
        return True
    
    def __get_phares(self):
        return list(self.__phares)
    
    def __set_phares(self, pharesLR):
        try :
            pharesL = min(abs(pharesLR[0]), self.__max_phares)
            pharesR = min(abs(pharesLR[1]), self.__max_phares)
            self.__cmd.append(bytearray([0x0B, pharesL, pharesR]))
            self.__phares = [pharesL, pharesR]
        except :
            return False
        return True
    
    def __get_ground_line(self):
        return self.__read_data(self.__line_logique)
    
    def __get_ground_analog(self):
        return self.__read_data(self.__line_analog)
    
    @property
    def last_error_msg(self):
        msg = self.__debug_msg
        self.__debug_msg = ""
        return msg
    
    def stop(self):
        self.moteurs = [0, 0]
        self.phares = [0, 0]
        
    def update(self) :
        
        # print("test")
        # Ecriture des données
        try :
            nb_commandes = len(self.__cmd)
            for i in range(nb_commandes-1, -1, -1) :
                self.__i2c.writeto(self.__addr, self.__cmd[i])
                sleep(0.005)
                self.__cmd.pop(i)
        except Exception as error_name: 
            self.__debug_msg = str(error_name)
            if self.__debug :
                print("i2c write error")
        
        # Lecture des données
        try :
            # Lecture Moteurs / Encodeurs
            self.__i2c.writeto(self.__addr, bytearray([0x00])) # 0 1 2 3 4 6 8 9 A
            full = struct.unpack('>BBBBHHBBB', self.__i2c.readfrom(self.__addr, 22))
            
            # Lecture capteurs sol / ligne
            self.__i2c.writeto(self.__addr, bytearray([0x1D]))
            line_d = struct.unpack('>BHHHHHH', self.__i2c.readfrom(self.__addr, 14))
            new_data = True
        except Exception as error_name: 
            self.__debug_msg = str(error_name)
            if self.__debug :
                print("i2c read error")
            return False
        
        # Traitement des données lues et MAJ des paramètres
        motorL = -full[1] if full[0] == 2 else full[1]
        motorR = -full[3] if full[2] == 2 else full[3]
        
        self.__motors        = [True, motorL,  motorR]
        self.__encoders      = [True, full[4], full[5]]
        self.__compensations = [True, full[6], full[7]]
        self.__pid           = [True, full[8]]
    
        line = []
        for i in range(0, 6):
            make = 1 if (line_d[0] & self.__masque[i]) else 0
            line.append(make)
        
        self.__line_logique = [True] + line
        self.__line_analog  = [True] + list(line_d[1:7])
        return True

    moteurs       = property(__get_motors, __set_motors)
    phares        = property(__get_phares, __set_phares)
    ground_line   = property(__get_ground_line)
    ground_analog = property(__get_ground_analog)


class MaqueenPlusV2(MaqueenPlusBridge):
    def __init__(self, i2c, addr=0x10, debug=False):
        MaqueenPlusBridge.__init__(self, i2c, addr, debug)
        self.__max_phares = 1
        
        # Création de la partie neopixels
        self.np = NeoPixel(Pin(23), 4) # create NeoPixel driver on GPIO0 for 4 pixels
        
    def __get_ground_line(self):
        return super().__get_ground_line()[0:5]
    
    def __get_ground_analog(self):
        return super().__get_ground_analog()[0:5]
    
    ground_line   = property(__get_ground_line)
    ground_analog = property(__get_ground_analog)


class MaqueenPlusV1(MaqueenPlusBridge):
    def __init__(self, i2c, addr=0x10, debug=False):
        MaqueenPlusBridge.__init__(self, i2c, addr, debug)
    
    def __get_encodeurs(self):
        return self.__read_data(self.__encoders)
    
    def encodeurs_reset(self):
        self.__cmd.append(bytearray([0x04, 0x00, 0x00, 0x00, 0x00]))
    
    def __get_compensations(self):  # [L: -255, R: +255]
        return self.__read_data(self.__compensations)
        
    def __set_compensations(self, comp): # [L: -255, R: +255]
        try :
            comp = list(comp)
            
            # Si L, R non renseignée, ne pas les changer
            comp[0] = __select_value(comp[0], self.__compensations[1])
            comp[1] = __select_value(comp[1], self.__compensations[2])
            
            # Adaptation des données moteur
            compL = min(abs(comp[0]), self.__max_motors)
            compR = min(abs(comp[1]), self.__max_motors)
            self.__cmd.append(bytearray([0x08, compL, compR]))
            
        except :
            return False
        return True
    
    def __get_pid(self):
        return self.__read_data(self._pid)
    
    def __set_pid(self, enable):
        try :
            self.__cmd.append(bytearray([0x0A, bool(enable)]))
        except :
            return False
        return True
    
    pid           = property(__get_pid, __set_pid)
    encodeurs     = property(__get_encodeurs)
    compensations = property(__get_compensations, __set_compensations)


# Creation

if __name__ == "__main__":      
    i2c  = I2C(1, scl=Pin(21), sda=Pin(22), freq=100000)      # crée un objet I2C
    maqueen = MaqueenPlusV1(i2c, debug=False)
        
    # Test phares
    print("\n\nEssai des phares")
    for i in range(9) :
        i = i%8
        maqueen.phares = (i, i)
        sleep(0.4)
        print(maqueen.__debug_msg, maqueen.phares, end="\r")
        maqueen.__debug_msg = ""
    
    # Test suiveur de ligne
    print("\n\nEssai du suiveur de ligne (logique)")
    for _ in range(50) :
        print(maqueen.ground_line, end="\r")
        sleep(0.1)
    
    # Test suiveur de ligne
    print("\n\nEssai du suiveur de ligne (analogique)")
    for _ in range(50) :
        print(maqueen.ground_analog, "     ", end="\r")
        sleep(0.1)
        
    # Test moteurs AV / AR
    print("\n\nEssai des moteurs AV / AR")
    print("Avant")
    maqueen.moteurs = (50, 50)
    sleep(0.4)
    print("Arrière")
    maqueen.moteurs = (-50, -50)
    sleep(0.5)
    print("Stop")
    maqueen.moteurs = (0, 0)
    sleep(0.4)
        
    # Test moteurs AV / AR
    print("\n\nEssai des moteurs D / G")
    print("Droite (Horaire)")
    maqueen.moteurs = (50, -50)
    sleep(0.4)
    print("Gauche (Antihoraire)")
    maqueen.moteurs = (-50, 50)
    sleep(0.5)
    print("Stop")
    maqueen.moteurs = (0, 0)
    sleep(0.4)


