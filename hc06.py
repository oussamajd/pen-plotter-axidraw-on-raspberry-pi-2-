import serial
import time


def readlineCR(port):
    rv = ""
    while True:
        ch = port.read()
        rv += ch
        if ch=='\r' or ch=='':
            return rv

port = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=1.0)
file=open("text.txt",'w')
x=0
while x<2:
    rcv = readlineCR(port)
    x=len(rcv)
    
    print rcv
    file.write(rcv)
file.close()
if file.closed:
    import text2gcode
