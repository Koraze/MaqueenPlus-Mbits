# Librairies :
# - https://github.com/mattytrentini/micropython-tmp1075/blob/master/src/tmp1075.py (source)
# - https://github.com/barbudor/CircuitPython_TMP75/blob/master/barbudor_tmp75.py
# - https://www.elecrow.com/wiki/index.php?title=Mbits
#
# MicroPython Driver for the TI TMP1075 temperature sensor.
# Example:
# 	i2c = I2C(sda=Pin(33), scl=Pin(32), freq=133000)
# 	tmp1075 = Tmp1075(i2c)
# 	tmp1075.get_temperature()
# See datasheet: http://www.ti.com/lit/ds/symlink/tmp1075.pdf

class Tmp1075:
    REG_TEMP  = const(0x00)
    REG_CFGR  = const(0x01)
    REG_LLIM  = const(0x02)
    REG_HLIM  = const(0x03)
    REG_DIEID = const(0x0F)
    
    BIT_VALUE = 0.0625
        
    def __init__(self, i2c=None, addr=0x48):
        if not i2c:
            raise ValueError('I2C object needed')
        self.__i2c = i2c
        self.__addr = addr
        
        # https://forum.micropython.org/viewtopic.php?t=5675
        # Configuration du capteur
        self.__config = i2c.readfrom_mem(self.__addr, Tmp1075.REG_CFGR, 1)
        self.__resolution = 12  # allowed values are: 9,10,11,12
        self.__config_new = self.__config[0]
        self.__config_new &= ~0x60  # clear bits 5,6
        self.__config_new |= (self.__resolution - 9) << 5  # set bits 5,6
        self.__i2c.writeto_mem(self.__addr, Tmp1075.REG_CFGR, bytes([self.__config_new]))
        # self.__check_device()

    def __check_device(self):
        id = self.__i2c.readfrom_mem(self.__addr, Tmp1075.REG_DIEID, 2)
        if (id[0] << 8 + id[1]) != 0x7500:
            raise ValueError('Incorrect DIE ID (expect 0x7500) or bad I2C comms')
        # Throw exception if DIE ID isn't 0x7500
        # Could also check to ensure self._addr is a valid address.

    def __get_temperature(self):
        try :
            t = self.__i2c.readfrom_mem(self.__addr, Tmp1075.REG_TEMP, 2)
            t = ((t[0] << 4) + (t[1] >> 4))              # ignore the 4 least significant bits of the 2nd byte
            t2 = Tmp1075.twos_comp(t, self.__resolution) # Validation de la valeur reçue
            return t * Tmp1075.BIT_VALUE
        except :
            return None
        # return temperature in degrees Celcius, each bit represents 0.0625 degrees Celsius.
        # TODO
        # - Allow a conversion function?
        # - Works for negative numbers?
    
    def twos_comp(val, width):
        if val >= 2 ** width:
            raise ValueError("Value: {} out of range of {} bit value".format(val, width))
        else:
            return val - int((val << 1) & 2 ** width)
        
    temp = property(__get_temperature)


if __name__ == "__main__":
    from machine import Pin, I2C, PWM, ADC
    from time    import sleep
    i2c  = I2C(1, scl=Pin(21), sda=Pin(22), freq=100000)
    tmp = Tmp1075(i2c)
    for i in range(100):
        print(tmp.temp)
        sleep(0.5)
    
