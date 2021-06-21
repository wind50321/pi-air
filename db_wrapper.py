from pymongo import MongoClient
from settings import USERNAME, PASSWORD


class DBWrapper:
    def __init__(self):
        self.client = MongoClient(
            'mongodb+srv://{}:{}@cluster0.0e5pv.mongodb.net/air?retryWrites=true&w=majority'.format(USERNAME, PASSWORD))
        self.db = self.client.air

    def insert_data(self, sec_data, ts):
        d = {'at': ts}
        d.update(sec_data)
        self.db.air.insert_one(d)

    def insert_minute_data(self, minute_data, ts):
        d = {'at': ts}
        d.update(minute_data)
        self.db.air_minute.insert_one(d)
