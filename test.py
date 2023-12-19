from mbits   import mbits
from time    import sleep
from maqueen import MaqueenPlusV1

# Objet Maqueen
maqueen = MaqueenPlusV1(mbits.i2c)

# Test phares
print("\n\nEssai des phares")
for i in range(9) :
    i = i%8
    maqueen.phares = (i, i)
    sleep(0.4)
    print(maqueen.last_error_msg, maqueen.phares, end="\r")

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

# Test moteurs D / G
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


#################################


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

