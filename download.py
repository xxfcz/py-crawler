import urllib2
import urlparse
import re
import robotparser
import datetime
import time
import pprint


user_agent = 'wswp'
g_delay = 1  # seconds


class Throttle:
    """Add a delay between downloads to the same domain"""

    def __init__(self, delay):
        self.delay = delay
        # last accessed timestamp of each domain
        self.domains = {}

    def wait(self, url):
        domain = urlparse.urlparse(url).netloc
        last_accessed = self.domains.get(domain)
        if last_accessed is not None and self.delay > 0:
            sleep_secs = self.delay - (datetime.datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                print 'sleeping for %d seconds ...' % (sleep_secs)
                time.sleep(sleep_secs)
        # update last accessed time
        self.domains[domain] = datetime.datetime.now()


def download(url, num_retries=2):
    print 'Downloading:', url
    try:
        headers = {'User-agent': user_agent}
        request = urllib2.Request(url, headers=headers)
        html = urllib2.urlopen(request).read()
    except urllib2.URLError as e:
        print 'Download error:', e
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, num_retries - 1)
    return html


def link_crawler(seed_url, link_regex, max_depth=2):
    """Crawl from the given seed URL following links matched by link_regex"""
    # Parse robots.txt
    parts = urlparse.urlsplit(seed_url)
    robot_file = parts.scheme + '://' + parts.netloc + '/robots.txt'
    rp = robotparser.RobotFileParser()
    rp.set_url(robot_file)
    rp.read()

    throttle = Throttle(g_delay)
    queue = [seed_url]  # download task queue
    seen = {seed_url: 0}  # visited urls and their depths
    valid_urls = []
    while queue:
        url = queue.pop()
        if not rp.can_fetch(user_agent, url):
            print 'Blocked by robots.txt:', url
            continue
        depth = seen[url]
        if depth == max_depth:
            continue
        throttle.wait(url)
        html = download(url)
        if not html:
            continue
        valid_urls.append(url)
        for link in get_links(html):
            if not re.match(link_regex, link):
                continue
            link = urlparse.urljoin(seed_url, link)
            if is_valid_link(link) and link not in seen:
                seen[link] = depth + 1
                queue.append(link)
    print 'Seen:'
    pprint.pprint(seen)
    return valid_urls


def get_links(html):
    """Extract all links from the web page"""
    # pattern = '''<a[^>]+href=['"](?!javascript)(.*?)['"]'''
    pattern = '''<a[^>]+href=['"](.*?)['"]'''
    link_regex = re.compile(pattern, re.IGNORECASE)
    return link_regex.findall(html)


def is_valid_link(link):
    return not link.startswith('javascript:')


def test1():
    links = link_crawler('http://www.linuxfromscratch.org/', '/lfs/?', 2)
    # links = link_crawler('http://example.webscraping.com/', '/(index|view)')
    print 'Valid links:'
    pprint.pprint(links)


# def test2():
#     th = Throttle(10)
#     th.wait('http://www.163.com')
#     th.wait('http://www.163.com')


if __name__ == '__main__':
    test1()
    # test2()
