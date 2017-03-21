from zipfile import ZipFile
import csv
import download
import mongo_cache

MAX_URLS = 20

# top-1m.csv.zip can be downloaded from http://101.110.118.23/s3.amazonaws.com/alexa-static/top-1m.csv.zip
zf = ZipFile(open('top-1m.csv.zip', 'r'))
csv_fn = zf.namelist()[0]
records = csv.reader(zf.open(csv_fn))
urls = []
for _, website in records:
    urls.append('http://' + website)
    if len(urls) >= MAX_URLS:
        break

cache = mongo_cache.MongoCache()
spider = download.Spider()
spider.cache = cache
spider.crawl_links(urls)
