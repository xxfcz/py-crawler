import urllib2
import urlparse
import re


def download(url, user_agent='wswp', num_retries=2):
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


def craw_sitemap(url):
    sitemap = download(url)
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    for link in links:
        # html = download(link)
        print link


def link_crawler(seed_url, link_regex):
    """Crawl from the given seed URL following links matched by link_regex"""
    queue = [seed_url]
    seen = set(seed_url)
    while queue:
        url = queue.pop()
        html = download(url)
        for link in get_links(html):
            if re.match(link_regex, link):
                link = urlparse.urljoin(seed_url, link)
                if is_valid_link(link) and link not in seen:
                    seen.add(link)
                    queue.append(link)
    return seen


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
    links = link_crawler('http://www.linuxfromscratch.org/', '/lfs/?')
    pprint.pprint(links)


if __name__ == '__main__':
    test()
