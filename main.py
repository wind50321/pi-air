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
    for key in data_list[0]:  # PM25, PM10...
        if key != 'at' and key != '_id':
            avg = sum([data[key] for data in data_list]) / len(data_list)
            avg_data[key] = int(avg * 10) / 10  # 只保留小數點一位

    avg_data['at'] = data_list[-1]['at']  # 以最後一筆資料的時間紀錄
    return avg_data


def check_bad_data(data, data0):
    # print('checking for bad data')
    for key in data:
        if key != 'at' and data[key] - data0[key] > 50:
            return True
    return False


def main():
    sec_data_list = []
    ts0 = datetime.now(timezone.utc)  # timestamp for last minute
    sec_data0 = {
        'PM25': 0,  # for first time check
        'PM10': 0,
    }  # last second data

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

        if check_bad_data(sec_data, sec_data0):  # check for bad data
            print('skipping bad data: {}, PM2.5: {}, PM10: {}'.format(sec_data['at'], sec_data['PM25'], sec_data['PM10']))
        else:
            print('sec data: {}, PM2.5: {}, PM10: {}'.format(sec_data['at'], sec_data['PM25'], sec_data['PM10']))
            db.insert_data(sec_data)
            sec_data_list.append(sec_data)
            sec_data0 = sec_data

        if ts.minute != ts0.minute and sec_data_list:
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
