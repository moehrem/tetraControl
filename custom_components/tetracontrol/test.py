import serial
import time

port = "/dev/pts/4"
ser = serial.Serial(port, 9600, timeout=1)

time.sleep(1)  # kurz warten, bis Verbindung steht

strings = [
    # "\r\nOK\r\n\r\n+GMI: MOTOROLA\r\n\r\nOK\r\n\r\n+GMM: 54009,M83PFT6TZ6AG,91.2.0.0\r\n\r\nOK\r\n\r\n+GMR: R27.220.9063\r\n\r\nOK\r\n\r\nOK\r\n\r\nOK\r\n\r\nOK\r\n\r\nOK\r\n\r\nOK\r\n\r\nOK\r\n",
    "\r\n+CTSDSR: 12,1234567,0,9876543,0,168\r\n0A4DD400000000000000005FE0002308517A100060\r\n",
    "\r\n+CTSDSR: 13,9876543,0,1234567,0,16\r\n8004\r\n",
    # +CME ERROR
]

for string in strings:
    ser.write(string.encode("utf-8"))
    time.sleep(0.5)
ser.close()
