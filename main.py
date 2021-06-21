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
    pm25 = sum([data['PM25'] for data in data_list]) / len(data_list)
    pm10 = sum([data['PM10'] for data in data_list]) / len(data_list)
    pm25 = int(pm25 * 10) / 10  # 只保留小數點一位
    pm10 = int(pm10 * 10) / 10  # 只保留小數點一位
    avg_data = {
        'PM25': pm25,
        'PM10': pm10,
        'at': data_list[-1]['at'],  # 以最後一筆時間紀錄
    }
    return avg_data


def main():
    sec_data_list = []
    ts0 = datetime.now(timezone.utc)

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
            'at': ts,
        }

        print('sec data: {}, PM2.5: {}, PM10: {}'.format(sec_data['at'], sec_data['PM25'], sec_data['PM10']))
        db.insert_data(sec_data)
        sec_data_list.append(sec_data)

        if ts.minute != ts0.minute:
            min_data = get_avg_data(sec_data_list)
            print('min data: {}, PM2.5: {}, PM10: {}'.format(min_data['at'], min_data['PM25'], min_data['PM10']))
            db.insert_minute_data(min_data)
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
