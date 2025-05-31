from checkNet import wait_network_connected
from usr.location import CoordinateSystemConvert, NMEAParse, GNSS
from machine import UART
# from time import sleep
import utime
# from _thread import start_new_thread

from modem import getDevImei


class Locator(object):
    def __init__(self):
        self.ct_Thread=True
        self.looper = True
        self.e_pprint=True
        self.last_loc_src=""
        self.loc_fail_ct=0
        self.lati = None
        self.longi = None
        self.altitude=0.0
        self.csc = CoordinateSystemConvert()
        self.nmea_parse = NMEAParse()
        self.gps_cfg = {"UARTn": UART.UART1,"buadrate": 115200,"databits": 8,"parity": 0,"stopbits": 1,"flowctl": 0,"gps_mode": 1,"nmea": 0b010111,"PowerPin": None,"StandbyPin": None,"BackupPin": None}
        self.gnss = GNSS(**self.gps_cfg)
        self.gnss.int_gps_enable()
        # self.read_gps()
        # start_new_thread(self.read_gps,())

    def pprint(self,strg):
        if self.e_pprint:
            print(strg)


    def read_gps(self):
        # utime.sleep(10)
        # while self.ct_Thread:
        #     if self.looper:
        gps_data = self.gnss.read(10)
        try:
            self.nmea_parse.set_gps_data(gps_data)
            lng = self.nmea_parse.Longitude
            lat = self.nmea_parse.Latitude
            alt = self.nmea_parse.Altitude
            self.last_loc_src = "GNSS"
            self.loc_fail_ct=0
                
            self.lati =float(lat)
            self.longi = float(lng)
            self.altitude = float(alt)
            self.pprint("GNSS Location Success")
            self.pprint("Latitude: {}".format(lat))
            self.pprint("Longitude: {}".format(lng))
            if(lng and lat):
                self.gnss.int_gps_disable()
                return lng, lat
        except:
            self.last_loc_src = "GNSS"
            self.loc_fail_ct=self.loc_fail_ct +1
            self.pprint("GNSS Location Fail")

    def get_location(self):
        """Returns the current latitude and longitude as a string."""
        if self.lati != 0.0 and self.longi != 0.0:
            return "Latitude: {}\nLongitude: {}".format(self.lati, self.longi)
        else:
            return "Location not available yet. Please try again later."
    # def mainloop(self):
    #     while True: 
    #         utime.sleep(10)


