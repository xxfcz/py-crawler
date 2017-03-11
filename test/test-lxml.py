import lxml.html

# fix broken html

broken_html = '<ul class=country><li id=area>Area: 244,820 sqr. km<li>Population</ul>'
tree = lxml.html.fromstring(broken_html)
fixed_html = lxml.html.tostring(tree, pretty_print=True)
print fixed_html

# extract data

el_area = tree.cssselect('ul > li#area')[0]
area = el_area.text_content()
print area
