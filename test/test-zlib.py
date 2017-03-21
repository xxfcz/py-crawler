import zlib
from bson.binary import Binary

text = 'I love you'
compressed = Binary(zlib.compress(text))
print compressed

d = zlib.decompress(compressed)
print d