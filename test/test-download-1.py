import pprint
import download


def test_1():
    html = download.download('http://www.linuxfromscratch.org/')
    print html


# server error
def test_2():
    download.download('http://httpstat.us/500')


# link_crawler
def test_3():
    links = download.link_crawler('http://www.linuxfromscratch.org/', '/lfs/?', 2)
    # links = link_crawler('http://example.webscraping.com/', '/(index|view)')
    print 'Valid links:'
    pprint.pprint(links)


def test_4():
    th = download.Throttle(10)
    th.wait('http://www.163.com')
    th.wait('http://www.163.com')


def test_5():
    cache = {}
    d = download.Downloader(1, 'xxf', 1, cache)
    d('http://www.linuxfromscratch.org/')
    d('http://www.linuxfromscratch.org/lfs/')
    d('http://www.linuxfromscratch.org/')


if __name__ == '__main__':
    test_5()
