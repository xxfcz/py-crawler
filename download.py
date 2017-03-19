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


class Downloader:
    def __init__(self, delay=5, user_agent='wswp', num_retries=1, cache=None):
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.num_tries = num_retries
        self.cache = cache

    def __call__(self, url):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError:
                # url is not available in cache
                pass
            else:
                if self.num_tries > 0 and 500 <= result['code'] < 600:
                    # ignore cached result and re-download
                    result = None
                else:
                    print 'Hit cache:', url
        if result is None:
            self.throttle.wait(url)
            headers = {'User-agent': self.user_agent}
            result = self.download(url, headers, self.num_tries)
            if self.cache is not None:
                self.cache[url] = result

    def download(self, url, headers, num_retries=2):
        print 'Downloading:', url
        code = 200
        try:
            request = urllib2.Request(url, headers=headers)
            html = urllib2.urlopen(request).read()
        except urllib2.URLError as e:
            print 'Download error:', e
            html = None
            code = e.code
            if num_retries > 0:
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    return self.download(url, headers, num_retries - 1)
        return {'html': html, 'code': code}
