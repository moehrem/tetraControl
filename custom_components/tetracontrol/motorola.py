"""Handle communication with Motorola devices."""

## Konzept:
# COM-Verbindung aufbauen
# Funkgerät initialisieren, vorerst nur Motorola
# an COM senden: "ATZ\r\n"
# TetraInitMotorola = "2,2,20|1,3,130|1,3,131|1,3,10"
# 1,2,20 = Status TE
# 2,2,20 = Status MT & TE
# 1,3,130 =
# 1,3,131 =
# 1,3,10 = Status GPS
# 1,3,137 = Immediate Text raw_data
# 1,3,138 = Alarm-raw_data
# baudrate = 38400
#
# Statusabfrage Funkgerät:
# alle 30 Sekunden Verbindungsstatus prüfen
# an COM senden: "AT+GMM?\r\n"
# Antwort etwa so: "|+GMM: 54009,M83PFT6TZ6AG,91.2.0.0||OK|"
# Alarm
# alle 30s Position abfragen

import serial
import time
import re
