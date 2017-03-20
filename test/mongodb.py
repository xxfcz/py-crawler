import download
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/test')
db = client.test
cache = db.cache

# data = {'x': 1, 'y': 2, 'z': 3}
# cache.insert(data)

r = cache.find_one()
print r
