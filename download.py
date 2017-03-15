import urllib2
import urlparse
import re
import robotparser

user_agent='wswp'

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


def link_crawler(seed_url, link_regex):
    """Crawl from the given seed URL following links matched by link_regex"""
    # Parse robots.txt
    parts = urlparse.urlsplit(seed_url)
    robot_file = parts.scheme + '://' + parts.netloc + '/robots.txt'
    rp = robotparser.RobotFileParser()
    rp.set_url(robot_file)
    rp.read()

    queue = [seed_url]      # Task queue
    seen = set(seed_url)    # Visited urls
    valid_urls = []
    while queue:
        url = queue.pop()
        if not rp.can_fetch(user_agent, url):
            print 'forbidden:', url
            continue
        html = download(url)
        if not html:
            continue
        valid_urls.append(url)
        for link in get_links(html):
            if not re.match(link_regex, link):
                continue
            if link not in seen:
                seen.add(link)
                link = urlparse.urljoin(seed_url, link)
                if is_valid_link(link):
                    queue.append(link)
    return valid_urls


def get_links(html):
    """Extract all links from the web page"""
    # pattern = '''<a[^>]+href=['"](?!javascript)(.*?)['"]'''
    pattern = '''<a[^>]+href=['"](.*?)['"]'''
    link_regex = re.compile(pattern, re.IGNORECASE)
    return link_regex.findall(html)


def is_valid_link(link):
    return not link.startswith('javascript:')


def test():
    import pprint
    # links = link_crawler('http://www.linuxfromscratch.org/', '/lfs/?')
    links = link_crawler('http://example.webscraping.com/', '/(index|view)')
    pprint.pprint(links)


if __name__ == '__main__':
    test()
