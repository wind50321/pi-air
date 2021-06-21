import time

# db
from db_wrapper import DBWrapper

import urllib.request
import urllib.error


# wait for internet connection
def connect(host='http://google.com'):
    try:
        urllib.request.urlopen(host)  # Python 3.x
        return True
    except urllib.error.URLError:
        print('not connected to internet')
        return False


while True:
    if connect():
        break
    time.sleep(5)


db = DBWrapper()


# SDS011
import serial  # 引用pySerial模組
import struct
from datetime import datetime, timezone

# Change this to the right port - /dev/tty* on Linux and Mac and COM* on Windows
PORT = '/dev/tty.usbserial-1420'

UNPACK_PAT = '<ccHHHcc'
ser_sds011 = serial.Serial(PORT, 9600, bytesize=8, parity='N', stopbits=1)


def get_avg_data(data_list):
    avg_data = {}
    for key in data_list[0]:  # get avg for every type of data
        avg = sum([data[key] for data in data_list]) / len(data_list)
        avg_data[key] = int(avg * 10) / 10  # 只保留小數點一位
    return avg_data


def check_bad_data(data, data0):
    # print('checking for bad data')
    for key in data:
        if data[key] > data0[key] * 5:
            return True


def main():
    sec_data_list = []
    ts0 = datetime.now(timezone.utc)  # last timestamp
    sec_data0 = None  # last second data

    while True:
        # SDS011
        data = ser_sds011.read(10)
        unpacked = struct.unpack(UNPACK_PAT, data)
        ts = datetime.now(timezone.utc)  # for timestamp
        pm25 = unpacked[2] / 10.0
        pm10 = unpacked[3] / 10.0

        sec_data = {
            'PM25': pm25,
            'PM10': pm10,
        }

        if sec_data0 and check_bad_data(sec_data, sec_data0):  # check for bad data
            print('filtering bad data')
            continue
        sec_data0 = sec_data

        print('sec data: {}, PM2.5: {}, PM10: {}'.format(ts, sec_data['PM25'], sec_data['PM10']))
        sec_data_list.append(sec_data)
        db.insert_data(sec_data, ts)

        if ts.minute != ts0.minute:
            min_data = get_avg_data(sec_data_list)
            print('min data: {}, PM2.5: {}, PM10: {}'.format(ts, min_data['PM25'], min_data['PM10']))
            db.insert_minute_data(min_data, ts)
            ts0 = ts
            sec_data_list = []

        time.sleep(1)


if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            break
        except Exception as e:
            print(e)
