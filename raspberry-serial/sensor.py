from datetime import datetime
import requests
import pytz
import json
from config import settings


class Sensor(object):

    sensor_type = None
    sampling_rate = None
#    url = "http://localhost:8000/v1/push-sensor-data/"
    url = "https://api.dusti.xyz/v1/push-sensor-data/"
    whitelist = []

    def __init__(self, filename=None):
        if self.sensor_type:
            self.sensor_uid = 'SENSOR_{}_UID'.format(self.sensor_type)
        else:
            self.sensor_uid = 'SENSOR_UID'
        if filename:
            self.filename = "{}.{}".format(filename, self.sensor_type)

    def filter(self, json_data):
        # filter all fields not in whitelist
        for key in json_data.keys():
            if key not in self.whitelist:
                del json_data[key]
        return json_data

    def check(self, message):
        # some checks to elimanate some of the 400s from the API
        if ':' not in message:
            return False
        if ';' not in message:
            return False
        if len(message.split(':')) != len(message.split(';')) + 1:
            return False
        return True

    def parse(self, message):
        if not self.check(message):
            return False
        json_data = dict(map(lambda x: x.split(':'),
                             message.strip().split(';')))
        return self.filter(json_data)

    def send(self, data, timestamp=None):
        payload = {
            "sampling_rate": self.sampling_rate,
            "sensordatavalues": []
        }
        if timestamp:
            payload['timestamp'] = timestamp

        for key, value in data.iteritems():
            d = {'value': value, 'value_type': key}
            payload['sensordatavalues'].append(d)

        headers = {'SENSOR': settings.get(self.sensor_uid),
                   'Content-Type': 'application/json'}
        r = requests.post(self.url, data=json.dumps(payload),
                          headers=headers, verify=False)
        print(r.status_code)
        print(r.text)

    def log(self, data):
        dt = str(pytz.timezone('Europe/Berlin').localize(datetime.now()))
        line = "{}| {}\n".format(dt, json.dumps(data))
        with open(self.filename, "a") as fp:
            print(line.strip())
            fp.write(line)


class SensorPPD42NS(Sensor):

    sensor_type = 'PPD42NS'
    sampling_rate = '15000'
    whitelist = ['P1', 'P2', 'durP1', 'durP2', 'ratioP1', 'ratioP2']

    def filter(self, json_data):
        for a, b in [('lowpulseoccupancyP1', 'durP1'),
                     ('lowpulseoccupancyP2', 'durP2'),
                     ('countP1', 'P1'),
                     ('countP2', 'P2')]:
            if a in json_data:
                json_data[b] = json_data.pop(a)
        json_data = super(SensorPPD42NS, self).filter(json_data)
        return json_data


class SensorSHT10(Sensor):

    sensor_type = 'SHT10'
    sampling_rate = None
    whitelist = ['temperature', 'humidity']

    def filter(self, json_data):
        for a, b in [('sht10_humidity', 'humidity'),
                     ('sht10_temperature', 'temperature')]:
            if a in json_data:
                json_data[b] = json_data.pop(a)
        json_data = super(SensorSHT10, self).filter(json_data)
        return json_data
