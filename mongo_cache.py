from pymongo import MongoClient
from datetime import datetime, timedelta


class MongoCache:
    def __init__(self, expires=timedelta(days=30)):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.cache
        self.db.webpage.create_index('timestamp', expiresAfterSeconds=expires.total_seconds())

    def __getitem__(self, url):
        """Load value at this URL"""
        record = self.db.webpage.find_one({'id': url})
        if record:
            return record['result']
        else:
            raise KeyError(url + ' does not exist')

    def __setitem__(self, url, result):
        """Save result for this URL"""
        record = {'result': result, 'timestamp': datetime.utcnow()}
        self.db.webpage.update({'id': url}, {'$set': record}, upsert=True)
