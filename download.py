import urllib2
import urlparse
import re
import robotparser
import datetime
import time
import threading


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
        headers = {'User-agent': 'wswp'}
        request = urllib2.Request(url, headers=headers)
        html = urllib2.urlopen(request).read()
    except urllib2.URLError as e:
        print 'Download error:', e
        html = None
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, num_retries - 1)
    return html


def link_crawler(seed_url, link_regex=None, max_depth=2, delay=1, user_agent='wswp', num_retries=1, callback=None,
                 cache=None):
    """Crawl from the given seed URL following links matched by link_regex"""
    # Parse robots.txt
    parts = urlparse.urlsplit(seed_url)
    robot_file = parts.scheme + '://' + parts.netloc + '/robots.txt'
    rp = robotparser.RobotFileParser()
    rp.set_url(robot_file)
    rp.read()

    d = Downloader(delay, user_agent, num_retries, cache)
    queue = [seed_url]  # download task queue
    seen = {seed_url: 0}  # visited urls and their depths
    valid_urls = []
    while queue:
        url = queue.pop()
        if not rp.can_fetch(user_agent, url):
            print 'Blocked by robots.txt:', url
            continue
        depth = seen[url]
        links = []
        if depth == max_depth:
            continue
        html = d(url)
        if not html:
            continue
        valid_urls.append(url)
        if callback:
            links.extend(callback(url, html) or [])
        if link_regex:
            links.extend(link for link in get_links(html) if re.match(link_regex, link))
        for link in links:
            link = normalize(seed_url, link)
            if is_valid_link(link) and link not in seen:
                seen[link] = depth + 1
                queue.append(link)
    # print 'Seen:'
    # pprint.pprint(seen)
    return valid_urls


class Spider:
    def __init__(self):
        self.link_regex = None
        self.num_retries = 2
        self.max_depth = 4
        self.delay = 1
        self.user_agent = 'wswp'
        self.callback = None
        self.cache = None
        self.max_threads = 8

    def crawl_site(self, seed_url):
        if self.max_threads > 1:
            return self._do_crawl_mt(seed_url, None)
        else:
            return self._do_crawl(seed_url, None)

    def crawl_links(self, links):
        if self.max_threads > 1:
            return self._do_crawl_mt(None, links)
        else:
            return self._do_crawl(None, links)

    def _do_crawl(self, seed_url, links):
        # Parse robots.txt
        rp = None
        if seed_url:
            parts = urlparse.urlsplit(seed_url)
            robot_file = parts.scheme + '://' + parts.netloc + '/robots.txt'
            rp = robotparser.RobotFileParser()
            rp.set_url(robot_file)
            rp.read()

        d = Downloader(self.delay, self.user_agent, self.num_retries, self.cache)
        queue = [seed_url] if seed_url else links[:]  # download task queue
        seen = {seed_url: 0} if seed_url else {}  # visited urls and their depths
        valid_urls = []
        while queue:
            url = queue.pop()
            if rp and not rp.can_fetch(self.user_agent, url):
                print 'Blocked by robots.txt:', url
                continue
            depth = seen[url] if url in seen else 0
            links = []
            if depth == self.max_depth:
                continue
            html = d(url)
            if not html:
                continue
            valid_urls.append(url)
            if self.callback:
                links.extend(self.callback(url, html) or [])
            if self.link_regex:
                links.extend(link for link in get_links(html) if re.match(self.link_regex, link))
            for link in links:
                link = normalize(seed_url, link)
                if is_valid_link(link) and link not in seen:
                    seen[link] = depth + 1
                    queue.append(link)
        return valid_urls

    def _do_crawl_mt(self, seed_url, urls):
        # Parse robots.txt
        rp = None
        if seed_url:
            parts = urlparse.urlsplit(seed_url)
            robot_file = parts.scheme + '://' + parts.netloc + '/robots.txt'
            rp = robotparser.RobotFileParser()
            rp.set_url(robot_file)
            rp.read()

        d = Downloader(self.delay, self.user_agent, self.num_retries, self.cache)
        queue = [seed_url] if seed_url else urls[:]  # download task queue
        seen = {seed_url: 0} if seed_url else {}  # visited urls and their depths
        valid_urls = []

        def process_queue():
            while True:
                try:
                    url = queue.pop()
                except IndexError:
                    # queue is empty
                    break
                else:
                    if rp and not rp.can_fetch(self.user_agent, url):
                        print 'Blocked by robots.txt:', url
                        continue
                    depth = seen[url] if url in seen else 0
                    links = []
                    if depth == self.max_depth:
                        continue
                    html = d(url)
                    if not html:
                        continue
                    valid_urls.append(url)
                    if self.callback:
                        links.extend(self.callback(url, html) or [])
                    if self.link_regex:
                        links.extend(link for link in get_links(html) if re.match(self.link_regex, link))
                    for link in links:
                        link = normalize(seed_url, link)
                        if is_valid_link(link) and link not in seen:
                            seen[link] = depth + 1
                            queue.append(link)

        threads = []
        while threads or queue:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)
            while len(threads) < self.max_threads and queue:
                thread = threading.Thread(target=process_queue)
                threads.append(thread)
                thread.setDaemon(True)
                thread.start()

        # all threads finished
        time.sleep(1)

        return valid_urls


def normalize(seed_url, link):
    """Normalize this URL by removing hash and adding domain
    """
    link, _ = urlparse.urldefrag(link)  # remove hash to avoid duplicates
    return urlparse.urljoin(seed_url, link)


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
        return result['html']

    def download(self, url, headers, num_retries=2):
        print 'Downloading:', url
        code = 200
        try:
            request = urllib2.Request(url, headers=headers)
            html = urllib2.urlopen(request).read()
        except urllib2.URLError as e:
            print 'Download error:', e
            html = None
            code = 400
            has_code = hasattr(e, 'code')
            if num_retries > 0:
                if has_code:
                    code = e.code
                    if 500 <= e.code < 600:
                        return self.download(url, headers, num_retries - 1)
        return {'html': html, 'code': code}
