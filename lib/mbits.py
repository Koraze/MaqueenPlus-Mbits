from neopixel import NeoPixel
from machine  import Pin, I2C, PWM, ADC
from time     import sleep
from mpu6050  import MPU
from tmp75    import Tmp1075

# Signal logique    : Bouton A, B
# Signal analogique : Micro (12B CAN), HP (12B PWM - Max 16)
# Signal num I2C    : MPU6050 - Accel Gyro Temp (0x69), TMP75 (0x48) Temp
# Signal num autre  : Leds Neopixels x25

class Micro():
    def __init__(self, pin) :
        self.__adc = ADC(Pin(pin))          # create ADC object on ADC pin
        self.__adc.atten(ADC.ATTN_11DB)    # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
        self.__adc.width(ADC.WIDTH_12BIT)
        
    def __get_value(self):
        return self.__adc.read()

    value = property(__get_value)


class MBits():
    def __init__(self):
        self.__a     = Pin(36, Pin.IN)
        self.__b     = Pin(39, Pin.IN)
        self.__micro = Micro(35)
        self.speaker = PWM(Pin(33))
        self.speaker.deinit()
        self.i2c     = I2C(1, scl=Pin(21), sda=Pin(22), freq=100000)
        self.display = NeoPixel(Pin(13) , 25) # create NeoPixel driver on GPIO0 for 8 pixels
        self.mpu     = MPU(self.i2c)
        self.tmp     = Tmp1075(self.i2c)
        
    def __accel(self):
        self.mpu.read_data()
        return mbits.mpu.accel
    
    def __gyro(self):
        self.mpu.read_data()
        return mbits.mpu.gyro
    
    def __temp(self):
        return self.tmp.temp
    
    def __a(self):
        return 1 - self.__a.value()
    
    def __b(self):
        return 1 - self.__b.value()
    
    def __micro(self):
        return self.__micro.value
    
    accel = property(__accel)
    gyro  = property(__gyro)
    temp  = property(__temp)
    a     = property(__a)
    b     = property(__b)
    micro = property(__micro)
        


mbits = MBits()

if __name__ == "__main__":
    # Test Haut-Parleurs
    print("\n\nEssai du haut parleur")
    mbits.speaker.init()
    for i in range(100, 5000, 100) :
        mbits.speaker.freq(i)
        sleep(0.1)
    mbits.speaker.deinit()
    
    # Test Micro
    print("\n\nEssai du micro")
    for _ in range(50) :
        print(mbits.micro, end="\r")
        sleep(0.1)
        
    # Test Boutons
    print("\n\nEssai des boutons (cliquez sur A et B)")
    for _ in range(50) :
        print(mbits.a, mbits.b, end="\r")
        sleep(0.1)
        
    # Test capteurs
    print("\n\nEssai du mpu et du tmp (bougez la carte, ou réchauffez la)")
    for _ in range(50) :
        mbits.mpu.read_data()
        print("%+.2f %+.2f %+.2f" % (mbits.accel.x, mbits.gyro.x, mbits.temp), end="\r")
        sleep(0.1)
        
    # Test Ecran
    print("\n\nEssai de l'écran")
    p = 5
    for c in range(9) :
        r = c & 0x01
        g = c & 0x02
        b = c & 0x04
        mbits.display.fill((r*p, g*p, b*p))
        mbits.display.write()
        sleep(0.5)