import unittest
import time
import mongo_queue


class TestMongoQueue(unittest.TestCase):
    def setUp(self):
        self.q = mongo_queue.MongoQueue()
        self.q.clear()

    def test_nonzero(self):
        self.q.clear()
        self.assertTrue(not self.q, 'not nonzero if empty')

    def test_push_pop(self):
        q = self.q
        url = 'http://www.abcdefg.com/'
        q.push(url)
        result = q.pop()
        self.assertEqual(url, result, 'push and pop, you get the pushed item')

    def test_repair(self):
        q = mongo_queue.MongoQueue(timeout=3)
        q.clear()
        url = 'http://www.baidu.com/'
        q.push(url)
        time.sleep(2)
        q.pop()
        time.sleep(4)
        self.assertRaises(KeyError, q.pop)
        # self.assertEqual(url, r)


if __name__ == '__main__':
    unittest.main()
