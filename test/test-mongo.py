import download
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/test')
db = client.cache
webpage = db.webpage
r = webpage.find_one()
print r
webpage.delete
