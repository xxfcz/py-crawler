import urllib2
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


# craw_sitemap('http://example.webscraping.com/sitemap.xml')


def link_crawler(seed_url, link_regex):
    """Crawl from the given seed URL following links matched by link_regex
    """
    queue = [seed_url]
    while queue:
        url = queue.pop()
        html = download(url)
        for link in get_links(html):
            if re.match(link_regex, link):
                queue.append(link)


# extract all links from the web page
def get_links(html):
    pattern = '''<a[^>]+href=['"](?!javascript)(.*?)['"]'''
    link_regex = re.compile(pattern, re.IGNORECASE)
    return link_regex.findall(html)


def test():
    import pprint
    html = download('http://www.baidu.com/')
    links = [link for link in get_links(html) if is_valid_link(link)]
    pprint.pprint(links)


def is_valid_link(link):
    return not re.match('^javascript:', link, re.IGNORECASE)


if __name__ == '__main__':
    test()
