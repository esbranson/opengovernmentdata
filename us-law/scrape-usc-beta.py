#!/usr/bin/python3

import lxml.etree

def test():
	tree = lxml.etree.parse('/home/msr/src/opengovernment/raw/usc18@113-21.xml')
	for section in tree.xpath('//a:section', namespaces={'a': 'http://xml.house.gov/schemas/uslm/1.0'}):
		traverse(section)

def traverse(node):
	for subnode in node.xpath('./a:content|./a:subsection', namespaces={'a': 'http://xml.house.gov/schemas/uslm/1.0'}):
		if subnode.tag == '{http://xml.house.gov/schemas/uslm/1.0}content':
			for p in subnode.iterfind('{http://xml.house.gov/schemas/uslm/1.0}p'):
				print(lxml.etree.tostring(p.text,encoding=str))
		elif subnode.tag == '{http://xml.house.gov/schemas/uslm/1.0}subsection':
			traverse(subnode)

def main():
	test()

if __name__ == '__main__':
	main()

