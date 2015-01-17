from time import sleep
from xml.dom.minidom import parse
import logging

import plg.utils.androidutil as au

def sendgpssignal(device, lat, lon, alt=None):
    args = ['emu', 'geo', str(lon), str(lat)]
    if alt is not None:
        args.append(str(alt))
    return au.runadbcmd(args, device)

def sendgpstoall(point):
    for device in au.onlinedevices():
        logging.debug('gps %s %s', device, str(point))
        sendgpssignal(device, *point)

def gpstask(points, sleeptime=2):
    while True:
        for point in points:
            sendgpstoall(point)
            sleep(sleeptime)

def gpx_extract(gpxfile):
    doc = parse(gpxfile)
    for trkpt in doc.getElementsByTagName('trkpt'):
        lat = trkpt.getAttribute('lat').strip()
        lon = trkpt.getAttribute('lon').strip()
        ele = trkpt.getElementsByTagName('ele')
        if ele:
            yield (lat, lon, ele[0].firstChild.data.strip())
        else:
            yield (lat, lon)

