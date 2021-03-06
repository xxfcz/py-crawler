import download
import re
import lxml.html
import mongo_cache
import csv

FIELDS = ('area', 'population', 'iso', 'country', 'capital', 'continent', 'tld', 'currency_code', 'currency_name',
          'phone', 'postal_code_format', 'postal_code_regex', 'languages', 'neighbours');


def cb_print1(url, html):
    if not re.search('/view/', url):
        return

    tree = lxml.html.fromstring(html)
    country = tree.cssselect('#places_country__row > td.w2p_fw')[0].text_content()
    area = tree.cssselect('#places_area__row > td.w2p_fw')[0].text_content()
    print 'Country:', country, '\tArea:', area


def cb_print2(url, html):
    if re.search('/view/', url):
        tree = lxml.html.fromstring(html)
        row = [tree.cssselect('#places_%s__row > td.w2p_fw' % field)[0].text_content()
               for field in FIELDS]
        print url, row


# Save extracted data to .cvs file
class ScrapeCallback:
    def __init__(self):
        self.writer = csv.writer(open('countries.csv', 'w'))
        self.fields = FIELDS
        self.writer.writerow(self.fields)

    def __call__(self, url, html):
        if re.search('/view/', url):
            tree = lxml.html.fromstring(html)
            row = [tree.cssselect('#places_%s__row > td.w2p_fw' % field)[0].text_content()
                   for field in FIELDS]
            print row
            self.writer.writerow(row)


cache = mongo_cache.MongoCache()
cb = ScrapeCallback()
download.link_crawler('http://example.webscraping.com/', '/(index|view)', delay=-1, callback=cb, cache=cache)
