from math import sqrt
from time import sleep
import _thread


# Classe Thread
class Thread():
    def __init__(self, update, dt=0.1):
        self.dt       = dt
        self.__state  = False
        self.__update = update
    
    def stop(self):
        self.__state = False
        sleep(self.dt)
        
    def start(self):
        self.__state = True
        _thread.start_new_thread(self.__thread, ())

    # Ne pas mettre de prints dans le thread
    # Les prints y sont (très) mal gérés et font planter l'ESP32
    def __thread(self):
        while self.__state :
            sleep(self.dt)
            try :
                self.__update()
            except :
                self.__state = False
                break


# Classe vecteur
class Vecteur():
    def __init__(self, coords=[0, 0, 0]):
        self.coords = [0, 0, 0]

    @property
    def norme(self):
        return sqrt(self.coords[0]**2 + self.coords[1]**2 + self.coords[2]**2)
    
    def __rx(self):
        return self.coords[0]

    def __ry(self):
        return self.coords[1]
    
    def __rz(self):
        return self.coords[2]
        
    def __wx(self, v):
        self.coords[0] = v

    def __wy(self, v):
        self.coords[1] = v
    
    def __wz(self, v):
        self.coords[2] = v
    
    def __str__(self):
        return self.coords
    
    x = property(__rx, __wx)
    y = property(__ry, __wy)
    z = property(__rz, __wz)


# Classe I2C_manage
# class I2C_manage():
#     def __init__(self, i2c):
#         pass


# Exemples
if __name__ == "__main__":
   vecteur = Vecteur()
   vecteur.coords = [1, 2, 3]
   print(vecteur)
   print(vecteur.norme)
   vecteur.x = 4
   print(vecteur)
   