from pymongo import MongoClient
from datetime import datetime, timedelta
import pickle
import zlib
from bson.binary import Binary


class MongoCache:
    def __init__(self, expires=timedelta(days=1)):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client.cache
        # self.db.webpage.create_index('timestamp', expiresAfterSeconds=expires.total_seconds())

    def __getitem__(self, url):
        """Load value at this URL"""
        record = self.db.webpage.find_one({'_id': url})
        if record:
            return pickle.loads(zlib.decompress(record['result']))
        else:
            raise KeyError(url + ' does not exist')

    def __setitem__(self, url, result):
        """Save result for this URL"""
        record = {
            'result': Binary(zlib.compress(pickle.dumps(result))),
            'timestamp': datetime.utcnow()
        }
        self.db.webpage.update({'_id': url}, {'$set': record}, upsert=True)

    def list(self):
        cursor = self.db.webpage.find()
        for item in cursor:
            id = item['_id']
            print "url: %s" % (id)
            print "html: %s" % (self[id])

    def clear(self):
        self.db.webpage.remove()
