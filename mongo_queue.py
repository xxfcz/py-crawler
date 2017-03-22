from pymongo import MongoClient, errors
from datetime import datetime, timedelta


class MongoQueue:
    OUTSTANDING, PROCESSING, COMPLETE = range(3)

    def __init__(self, client=None, timeout=300):
        self.client = client if client is not None else MongoClient('localhost', 27017)
        self.db = self.client.cache
        self.timeout = timeout

    def __nonzero__(self):
        record = self.db.crawl_queue.find_one(
            {'status': {'$ne': self.COMPLETE}}
        )
        return True if record else False

    def push(self, url):
        """Add new URL to queue if does not exist"""
        try:
            self.db.crawl_queue.insert({'_id': url, 'status': self.OUTSTANDING})
        except errors.DuplicateKeyError as e:
            pass  # this url is already in the queue

    def pop(self):
        """Get an outstanding URL from the queue and set its status to PROCESSING."""
        record = self.db.crawl_queue.find_and_modify(
            query={'status': self.OUTSTANDING},
            update={'$set': {
                'status': self.PROCESSING,
                'timestamp': datetime.now()
            }}
        )
        if record:
            return record['_id']
        else:
            self.repair()
            raise KeyError

    def complete(self, url):
        self.db.crawl_queue.update({'_id': url}, {'$set': {'status': self.COMPLETE}})

    def repair(self):
        """Release stalled jobs"""
        # find records that have 'timestamp' older than timeout seconds ago and that are not completed
        record = self.db.crawl_queue.find_and_modify(
            query={
                'timestamp': {'$lt': datetime.now() - timedelta(seconds=self.timeout)},
                'status': {'$ne': self.COMPLETE}
            },
            update={'$set': {'status': self.OUTSTANDING}}
        )
        if record:
            print 'Released:', record['_id']
            return record['_id']
        else:
            return None

    def clear(self):
        self.db.crawl_queue.remove()

    def list(self):
        for c in self.db.crawl_queue.find():
            print c
