class MyClass:
    def __init__(self):
        print "MyClass::__init__"

    def __call__(self, url):
        result = url.capitalize()
        return result


def test1():
    o = MyClass()
    print o('abc')


if __name__ == '__main__':
    test1()