import pprint
import download

URL_IN = 'http://www.1m1m.com'
URL_OUT = 'http://www.baidu.com'


def cb_links(url, html):
    if url == URL_IN:
        return [URL_OUT]
    else:
        return None


def test_8():
    """Test on returning links in callback"""
    links = download.link_crawler(URL_IN, None, 2, callback=cb_links)
    pprint.pprint(links)
