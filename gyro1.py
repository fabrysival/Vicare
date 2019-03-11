import time
import math
import mpu6050
import gps
import serial
import datetime

# Inizializzazione sensori
mpu = mpu6050.MPU6050()
mpu.dmpInitialize()
mpu.setDMPEnabled(True)
    

packetSize = mpu.dmpGetFIFOPacketSize()
# Apertura demone GPS su porta 2947
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
noncaduto = True
while noncaduto:
    # Lettura INT_STATUS byte
    mpuIntStatus = mpu.getIntStatus()
  
    if mpuIntStatus >= 2: # Drop pacchetti doppi
        # lettura contatore FIFO corrente
        fifoCount = mpu.getFIFOCount()
        
        # check overflow del FIFO per evitare blocchi o letture incorrette
        if fifoCount == 1024:
            # reset FIFO
            mpu.resetFIFO()
                      
            
        # Attesa dati corretti
        fifoCount = mpu.getFIFOCount()
        while fifoCount < packetSize:
            fifoCount = mpu.getFIFOCount()
        
        result = mpu.getFIFOBytes(packetSize)
        q = mpu.dmpGetQuaternion(result)
        g = mpu.dmpGetGravity(q)
        ypr = mpu.dmpGetYawPitchRoll(q, g)
        
        #print(ypr['yaw'] * 180 / math.pi),
    
        angolodxsx=ypr['pitch'] * 180 / math.pi
        #print(angolodxsx)
        
        angolofxrx=ypr['roll'] * 180 / math.pi
        #print(angolofxrx)
        report = session.next()
        if (angolodxsx < -55) or (angolodxsx >55) or (angolofxrx < -55) or (angolofxrx > 55):
            #print("Caduto ! ")
            if report['class'] == 'TPV':
                        if hasattr(report, 'lat'):
                                latitudine = str(report.lat)
                        if hasattr(report, 'lon'):    
                            longitudine = str(report.lon)
                            if hasattr(report, 'speed'):
                                velocita = str(report.speed * gps.MPS_TO_KPH)
                                noncaduto = False
                                recipient = "+39123456789" # numero QUI
                                message = "Caduto ! lat. " + latitudine + " lon. " + longitudine + " Vel. " + velocita + " k/h"
                                print(message)
                                file=open("/home/pi/gpslog.txt", "a")
                                file.write("\n" + str(datetime.datetime.now().strftime("%d/%m/%y %H:%M")) + " - " + message)
                                phone = serial.Serial("/dev/ttyUSB1",  115200, timeout=5)
                                try:
                                    time.sleep(0.5)
                                    phone.write(b'ATZ\r')
                                    time.sleep(0.5)
                                    phone.write(b'AT+CMGF=1\r')
                                    time.sleep(0.5)
                                    phone.write(b'AT+CMGS="' + recipient.encode() + b'"\r')
                                    time.sleep(0.5)
                                    phone.write(message.encode() + b"\r")
                                    time.sleep(0.5)
                                    phone.write(chr(26))
                                    time.sleep(0.5)
                                finally:
                                    phone.close()
                            #print("Caduto ! lat. " + latitudine + " lon. " + longitudine)
                    
    
        # verifica termine controlli FIFO   
        fifoCount -= packetSize  
