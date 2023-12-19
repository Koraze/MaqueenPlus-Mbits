# https://github.com/tuupola/micropython-mpu9250
# https://github.com/CoreElectronics/CE-PiicoDev-MPU6050-MicroPython-Module/blob/main/PiicoDev_MPU6050.py

import struct
from tools       import Vecteur
from time        import sleep
from micropython import const


class MPU():
    # Adresses importantes
    __ADDRESSES           = [const(0x68), const(0x69)]
    
    # Registres importants
    __R_PWR_MGMT_1B         =  0x6B
    __R_GYRO_CONFIG_1B      =  0x1b
    __R_ACCEL_CONFIG_2B     =  0x1c
    __R_ACCEL_TEMP_GYRO_14B =  0x3b
    __R_WHO_AM_I            =  0x6b
    __WHO_AM_I_ANSWERS      = [const(0x75), const(0x71), const(0x70), const(0x40), 0]  # MPU 6050, 6250, 6500

    # Configuration
    __ACCEL_SO   = 2048
    __ACCEL_MASK = 0b00011000
    __ACCEL      = {
        "2G" : [0b00000000, __ACCEL_SO * 8],  # 1 / 16384 ie. 0.061 mg / digit
        "4G" : [0b00001000, __ACCEL_SO * 4],  # 1 / 8192  ie. 0.122 mg / digit
        "8G" : [0b00010000, __ACCEL_SO * 2],  # 1 / 4096  ie. 0.244 mg / digit
        "16G": [0b00011000, __ACCEL_SO * 1],  # 1 / 2048  ie. 0.488 mg / digit
    }
    
    __GYRO_SO   = 16.4
    __GYRO_MASK = 0b00011000
    __GYRO      = {
        "250DPS"  : [0b00000000, __GYRO_SO * 8],
        "500DPS"  : [0b00001000, __GYRO_SO * 4],
        "1000DPS" : [0b00010000, __GYRO_SO * 2],
        "2000DPS" : [0b00011000, __GYRO_SO * 1],
    }
    
    __TEMP_SO     = 340    # 333.87
    __TEMP_OFFSET = 36.53  # 21

    # Conversions
    __SF_G     = 1
    __SF_M_S2  = 9.80665           # 1 g = 9.80665 m/s2 ie. standard gravity
    __SF_DEG_S = 1
    __SF_RAD_S = 0.017453292519943 # 1 deg/s is 0.017453292519943 rad/s
    
    # Fonctions
    def __init__(self, i2c, address=None):
        self.__i2c      = i2c
        self.__address  = address
        self.__a_config = None
        self.__g_config = None
        self.__g_offset = [0, 0, 0]
        
        self.accel = Vecteur()
        self.gyro  = Vecteur()
        self.temp  = 0
        
        self.__whoiam   = self.__check_whoiam()
        self.on()
        self.gyro_config("250DPS")
        self.accel_config("2G")
        self.gyro_calibrate(count=256, delay=0)
        print(self.__whoiam)
        
    
    def __register(self, register, write=None, read=None):
        if type(read) is int :
            if read > 0 :
                return self.__i2c.readfrom_mem(self.__address, register, read)
        
        if write is not None :
            type_  = type(write)
            result = None
            if type_ is int :
                result = bytearray([write])
            elif type_ is list or type_ is bytes :
                if len(write) > 0 :
                    result = bytearray(write)
            elif type_ is bytearray :
                result = write
                
            if result :
                self.__i2c.writeto_mem(self.__address, register, result)
        
        return None
    
    
    def __check_whoiam(self):
        # Ajout de l'adresse personnalisée
        if type(self.__address) is int :
            MPU.__ADDRESSES = [self.__address] + MPU.__ADDRESSES
        
        # Essai des adresses
        for a in MPU.__ADDRESSES :
            try:
                self.__address = a
                r = self.__register(MPU.__R_WHO_AM_I, read=1)
                r = r[0]
                if r in MPU.__WHO_AM_I_ANSWERS :
                    print("MPU who I am is", r)
                    return r
            except:
                pass
                    
        # Retour d'erreur si rien trouvé
        raise RuntimeError("MPU6500 not found in I2C bus.")
        return False
    
    
    def on(self):
        # Ajout de l'adresse personnalisée
        self.__register(MPU.__R_PWR_MGMT_1B, write=0)
    
    
    def gyro_config(self, value=None):
        if type(value) is str:
            if value in MPU.__GYRO :
                config = MPU.__GYRO[value]
                self.__register(MPU.__R_GYRO_CONFIG_1B, write=config[0])
                sleep(0.005)
                retour = self.__register(MPU.__R_GYRO_CONFIG_1B, read=1)
                if retour[0] == config[0] :
                    self.__g_config = config
                    self.__g_config.append(value)
                    print("new gyro config :", value)
                else :
                    self.__g_config = None
                    print("something wrong happens", retour[0], "instead of", config[0])
            else :
                print("wrong value used, only use", MPU.__GYRO.keys())
        
        if self.__g_config :
            return self.__g_config[2]
        return None
    
    
    def accel_config(self, value=None):
        if type(value) is str:
            if value in MPU.__ACCEL :
                config = MPU.__ACCEL[value]
                self.__register(MPU.__R_ACCEL_CONFIG_2B, write=config[0])
                sleep(0.005)
                retour = self.__register(MPU.__R_ACCEL_CONFIG_2B, read=2)
                if retour[0] == config[0] :
                    self.__a_config = config
                    self.__a_config.append(value)
                    print("new accel config :", value)
                else :
                    self.__a_config = None
                    print("something wrong happens, ", retour[0], "instead of", config[0])
            else :
                print("wrong value used, only use", MPU.__ACCEL.keys())
                
        if self.__a_config :
            return self.__a_config[2]
        return None
    
    def read_data(self):
        if not self.__a_config or not self.__g_config :
            return None
        
        data = self.__register(MPU.__R_ACCEL_TEMP_GYRO_14B, read=14)
        data = struct.unpack(">hhhhhhh", data)
        
        for i in range(3) :
            self.accel.coords[i] = data[i]   / self.__a_config[1]
            self.gyro.coords[i]  = data[i+4] / self.__g_config[1] - self.__g_offset[i]
        
        self.temp = (data[3] - MPU.__TEMP_OFFSET) / MPU.__TEMP_SO + MPU.__TEMP_OFFSET
        
    def gyro_calibrate(self, count=256, delay=0):
        offset = [0, 0, 0]
        
        for i in range(count) :
            sleep(delay)
            self.read_data()
            for j in range(3) :
                offset[j] += self.gyro.coords[j]
                
        for j in range(3) :
            offset[j] /= float(count)
        print(offset)
        self.__g_offset = offset
    


# Exemples
if __name__ == "__main__":
    from machine import Pin, I2C, PWM, ADC
    i2c  = I2C(1, scl=Pin(21), sda=Pin(22), freq=100000)
    print("scan i2c", i2c.scan())
    mpu = MPU(i2c)
    for i in range(10):
        mpu.read_data()
        print("%+.2f %+.2f %+.2f" % (mpu.accel.x, mpu.gyro.x, mpu.temp))
        sleep(1)


