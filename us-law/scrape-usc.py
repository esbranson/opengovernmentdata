#! /usr/bin/python3 -uW all
# -*- coding: utf-8 -*-

##
# scrape-usc.py - convert the Cornell USC XML files into RDF
# Copyright (C) 2008-2013  Eric S. Branson <bransone@ecs.csus.edu> 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# @todo
# In progress.
#
# for enum, ty=2 gives "(a)", ty=3 gives "(1)",
# ty=4 gives "(A)", ty=5 gives "(i)", ...

usage="""
scrape-usc.py - convert the Cornell USC XML files into RDF

Get the data from <http://voodoo.law.cornell.edu/uscxml/>.

Usage:		scrape-usc.py [options] [file [file ..]]
Arguments:

	file			Cornell XML tarfile
 	-d, --debug		enable debuging output (twice for verbose)
	-l, --load-dtd		enable loading of DTD
	-h			display this help and exit
"""

import sys
import getopt
import os
import os.path
import re
import tempfile
import tarfile
import itertools
import urllib.request
import tempfile
import logging
try:
	import lxml.etree as etree
except ImportError:
	import xml.etree.ElementTree as etree
try:
	import rdflib, rdflib.graph
except ImportError:
	logging.fatal('FATAL: need rdflib %s', usage)
	sys.exit(1)

#
# Globals.
#

LOC_URL = 'http://data.loc.gov/ontology/loc-law-onto-0.1#'
LOC = rdflib.Namespace(LOC_URL)
TITLES_URL = 'http://data.loc.gov/dataset/usc/'
#T_C = LOC['LawCode']
T_D = T_C = LOC['CodeDivision']
P_D_TYPE = LOC['hasCodeDivisionType']
P_D_ENUM = LOC['hasCodeDivisionEnum']
P_D_TITLE = LOC['hasCodeDivisionTitle']
P_D_STATUS =  LOC['hasCodeDivisionStatus']
P_D_SUB = LOC['hasCodeSubdivision']
P_D_SEC = LOC['hasCodeSection']
T_S = LOC['CodeSection']
P_S_TYPE = LOC['hasCodeSectionType']
P_S_ENUM = LOC['hasCodeSectionEnum']
P_S_ENUMS = LOC['hasCodeSectionEnumRange']
P_S_TITLE = LOC['hasCodeSectionTitle']
P_S_STATUS = LOC['hasCodeSectionStatus']
P_S_PARA = LOC['hasCodeParagraph']

flags = {'dtd': False}

##
# Entry function. Parse paramters, call main function.
#
def main():
	d = None
	debug = False

	# parse commandline for flags and arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hdl')
	except getopt.GetoptError:
		logging.fatal('getopt error %s', usage)
		sys.exit(1)

	# parse flags
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			print(usage)
			sys.exit(0)
		elif opt in {'-d', '--debug'}:
			if not debug:
				logging.getLogger().setLevel(logging.INFO)
				debug = True
			else:
				logging.getLogger().setLevel(logging.DEBUG)
		elif opt in {'-l', '--load-dtd'}:
			flags['dtd'] = True
		else:
			logging.fatal('invalid flag %s %s', opt, usage)
			sys.exit(1)

	# parse arguments
	if len(args) == 0:
		logging.fatal('need directory %s', usage)
		sys.exit(1)

	for fn in args:
		with tarfile.open(fn) as tf:
			do_it(tf)

##
#
#
def do_it(tf):
	# locate the TOC file
	fn = next(f for f in tf.getnames() if re.match('.*TOC\.XML$', f))
	d = os.path.dirname(fn)

	# parse XML
	r = parse_xml(tf.extractfile(fn)).getroot()

	enum = None
	for el in r.findall('supsec'):
		g = rdflib.graph.Graph()
		g.bind('loc', LOC_URL)
		for tup in parse_toc_xml_gen(tf, d, el, '0', None):
			if isinstance(tup, str):
				enum = tup
			elif tup is None:
				logging.warning('parse_toc_xml_gen yielded None')
			else:
				g.add(tup)
				logging.debug('got tup')
		fn = enum + 'usc.ttl'
		logging.debug('writing %s', fn)
		g.serialize(fn, 'turtle')

##
# Parse an XML file and return XML object, handling errors
# and cleaning up invalid XML entities if needed.
#
def parse_xml(f):
	# parser
	if flags['dtd']:
		p = etree.XMLParser(remove_blank_text=True, load_dtd=True, recover=True)
	else:
		p = etree.XMLParser(remove_blank_text=True, recover=True, resolve_entities=False)

	# do it
	while True:
		try:
			tr = etree.parse(f, p)
		except etree.XMLSyntaxError as e:
			er = p.error_log[-1]
			ty = er.type
			tyn = er.type_name
			l = er.line
			c = er.column

			logging.debug('parse: e %s %s error at %s %s', len(p.error_log), tyn, l, c)

			if ty == etree.ErrorTypes.ERR_NAME_REQUIRED:
				f2 = error_repl_entity(f, l, c)
				f.close()
				f = f2
			else:
				f.close()
				logging.fatal('parse: %s %s error at %s %s', len(p.error_log), tyn, l, c)
				sys.exit(1)
		else:
			break

	return tr

##
# Escape a lone ampersand in an XML file, and return the file object.
#
def error_repl_entity(fin, ln, col):
	fin.seek(0)
	fout = tempfile.TemporaryFile('w+')
	for i,line in enumerate(fin, 1):
		if i == ln:
			logging.debug('error_repl_entity: i line %s %s', i, repr(line))
			nline = line.replace('& ', '&amp; ')
			logging.debug('error_repl_entity: nline %s', repr(nline))
			fout.write(line.replace('& ', '&amp; '))
		else:
			fout.write(line)
	fout.seek(0)
	return fout

##
# Recursively parse a 'supsec' XML element. This includes its header,
# which possibly gives its type, enumeration, title, and status,
# and possibly subordinate 'supsec' and 'sec' XML elements.
#
def parse_toc_xml_gen(tf, d, r, lev, tit):
	# info
	refid = r.attrib['refid']
	fragid = r.attrib['fragid']
	lvl = r.attrib['lvl']
	if lev != lvl:
		logging.warning('SUPSEC unequal level')
	name = etree.tostring(r.find('name'), method='text', encoding=str)

	logging.debug('SUPSEC: lev lvl name refid fragid %s %s %s %s %s', lev, lvl, repr(name), refid, fragid)

	# parse header
	typ, n, title, status = parse_org_head(name)

	# now make node
	if tit == None:
		yield n
		tit = TITLES_URL + n
		node = rdflib.URIRef(tit)
		yield (node, rdflib.RDF.type, T_C)
	else:
		node = rdflib.BNode()
		yield (node, rdflib.RDF.type, T_D)

	# add type
	if typ:
		yield (node, P_D_TYPE, rdflib.Literal(typ, lang='en'))

	# add enums
	if n:
		yield (node, P_D_ENUM, rdflib.Literal(n, lang='en'))

	# add title
	if title:
		yield (node, P_D_TITLE, rdflib.Literal(title, lang='en'))

	# add status
	if status:
		yield (node, P_D_STATUS, rdflib.Literal(status, lang='en'))

	# sections
	seq = rdflib.BNode()
	n = None
	for n,sel in enumerate(r.xpath('sec'), 1):
		# info
		sname = sel.text
		srefid = sel.attrib['refid']
		sfragid = sel.attrib['fragid']

		logging.debug('SEC: sname srefid sfragid %s %s %s', sname, srefid, sfragid)

		with tf.extractfile(os.path.join(d, sfragid + '.XML')) as f:
			sec_node = yield from parse_sec_xml_gen(f, tit)
		yield (seq, rdflib.RDF[n], sec_node)
	if n:
		yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
		yield (node, P_D_SEC, seq)

	# sub org el
	nlev = str(int(lev)+1)
	n = None
	seq = rdflib.BNode()
	for n,subel in enumerate(r.findall('supsec'), 1):
		subnode = yield from parse_toc_xml_gen(tf, d, subel, nlev, tit)
		yield (seq, rdflib.RDF[n], subnode)
	if n:
		yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
		yield (node, P_D_SUB, seq)

	return node

##
# Parse a 'name' XML header element of a 'supsec' parent XML element,
# which possibly gives its type, enumeration, title, and status.
#
def parse_org_head(name):
	if 'REPEALED' in name or 'Repealed' in name or name[0] == '[' or name[-1] == ']':
		if name[0] == '[':
			name = name.split('[',1)[1].rsplit(']',1)[0]
			split1 = name.split(None,1)
			split2 = split1[1].split(' - ',1)
			typ = split1[0].lower()
			n = split2[0]
			title = split2[1]
		else:
			split1 = name.split(None,1)
			split2 = split1[1].split(' - ',1)
			typ = split1[0].lower()
			n = split2[0]
			title = split2[1].split('[',1)[1].rsplit(']',1)[0]

		status = 'repealed'

	elif ' - ' not in name:
		typ = None
		n = None
		title = name
		status = None

	else:
		if ', APPENDIX' in name:
			split1 = name.split(', APPENDIX - ',1)
			status = 'appendix'
		else:
			split1 = name.split(' - ',1)
			status = None
		split2 = split1[0].split()
		typ = split2[0].lower()
		n = split2[1]
		title = split1[1]

	# watchout for appendies with same title number
	if n and 'appendix' in name.lower():
		n = n + 'A'

	logging.debug('parse_org_head: typ n title status %s %s %s %s', repr(typ), repr(n), repr(title), status)

	return typ, n, title, status

##
#
#
def parse_sec_xml_gen(f,tit):
	tr = parse_xml(f)

	# extract info
	el = tr.find('//section')
	if el is None: # uscode25/T25F01873.XML
		logging.warning('parse_sec_xml: no section %s', f)
		txt = tr.getroot().find('text')
		if txt is None:
			logging.warning('no text either')
			txt = tr.find('//text')
		if txt is None:
			logging.fatal('no //text either %s', etree.tostring(tr))
		head = etree.tostring(txt, method='text', encoding=str).replace('\n', '')
		num = None
		refid = None
		contel = None
	else:
		num = el.attrib['num']
		refid = el.attrib['extid']
		contel = el.find('sectioncontent')
		head = ' '.join(etree.tostring(el.find('head'), method='text', encoding=str).split())

	# parse header
	enum_parts, typ, enum, title, status = parse_sec_head(num, head)

	if len(enum_parts) == 0:
		logging.warning('parse_sec_xml: no enum_parts so using enum %s', enum)
		enum_parts.append(enum)

	# node
	if len(enum_parts) == 1 and isinstance(enum_parts[0], str):
		node = rdflib.URIRef(tit + '/' + enum_parts[0])
	else:
		logging.debug('make bnode %s %s', tit, enum_parts)
		node = rdflib.BNode()
	yield (node, rdflib.RDF.type, T_S)

	# add type
	if typ:
		yield (node, P_S_TYPE, rdflib.Literal(typ, lang='en'))

	# add enums
	for part in enum_parts:
		if enum and len(enum_parts) == 1 and enum != part:
			logging.warning('parse_sec_xml: enum and enum != enum_parts %s %s', enum, enum_parts)

		if isinstance(part, str):
			yield (node, P_S_ENUM, rdflib.Literal(part, lang='en'))
		elif isinstance(part, tuple):
			yield (node, P_S_ENUMS, rdflib.Literal(part[0], lang='en'))
			yield (node, P_S_ENUMS, rdflib.Literal(part[1], lang='en'))
		else:
			logging.fatal('not str or tuple: %s', part)
			sys.exit(1)

	# add title
	if title:
		yield (node, P_S_TITLE, rdflib.Literal(title, lang='en'))

	# add status
	if status:
		yield (node, P_S_STATUS, rdflib.Literal(status, lang='en'))

	# parse sectioncontent
	if contel is not None:
		# parse content in regular context
		# traverse children in order
		n = itertools.count(1)
		seq = rdflib.BNode()
		for subel in contel:
			newsubel = parse_sectioncontent_xml(subel, '1')
			if newsubel is not None:
				yield (seq, rdflib.RDF[next(n)], rdflib.Literal(etree.tostring(newsubel), lang='en'))
		if next(n) != 1:
			yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
			yield (node, P_S_PARA, seq)

	return node

##
#
#
def parse_sec_head(num, head):
	logging.debug('parse_sec_head: num head %s %s', repr(num), repr(head))

	# get numbers for special sections, and to verify enum for regular sections
	enum_parts = []
	if num is not None: # uscode25/T25F01873.XML
		for s in num.split(',_'):
			if '_to_' in s:
				ss = s.split('_to_')
				assert len(ss) == 2
				enum_parts.append((ss[0], ss[1]))
			else:
				enum_parts.append(s)

	# repealed
	if 'Repealed' in head:
		logging.debug('parse_sec_head: is repealed')

		typ = None
		enum = None
		title = None
		status = 'repealed'

	# renumbered
	elif 'Renumbered' in head:
		logging.debug('parse_sec_head: is renumbered')

		typ = None
		enum = None
		title = None
		status = 'renumbered'

	# transferred
	elif 'Transferred' in head:
		logging.debug('parse_sec_head: is transferred')

		typ = None
		enum = None
		title = None
		status = 'transferred'

	# omitted
	elif 'Omitted' in head:
		logging.debug('parse_sec_head: is omitted')

		typ = None
		enum = None
		title = None
		status = 'omitted'

	# vacant
	elif 'Vacant' in head:
		logging.debug('parse_sec_head: is vacant')

		typ = None
		enum = None
		title = None
		status = 'vacant'

	else:
		secres = []

		# create re knowing enum
		if len(enum_parts) == 1:
			enum_parts[0] = enum_parts[0].replace('-', '–') # XXX: re disallowed chars?
#			secres.append('(§|Rule|Rules|Form)*\s*(' + enum_parts[0] + ')\.*\s*(.*)')
			secres.append('(§|Rule|Rules|Form| §)*\s*(' + enum_parts[0] + ')\.*\s*(.*)')
		else:
			logging.warning('parse_sec_head: WTF %s %s', num, enum_parts)

#			secre = '(§|Rule|Rules|Form)*\s*(\d+.*?)\.*\s*(.*)'
#			secre = '(§|Rule|Rules|Form| §)*\s*(\d+.*?)\.*\s*(.*)'
		secres.append('(§|Rule|Rules|Form| §)*\s*(\d+.*?)\.\s*(.*)')
		secres.append('(§|Rule|Rules|Form| §)*\s*(\d+.*?)\s*(.*)') # missing period after section number?
		secres.append('(§|Rule|Rules|Form| §)*\s*(.+?)\.\s*(.*)') # no digits in section number?
		secres.append('(§|Rule|Rules|Form| §)*\s*(.+?)\s*(.*)') # neither?

		for secre in secres:
			logging.debug('parse_sec_head: secre %s', secre)

			m = re.match(secre, head)
			if m is not None:
				break
			logging.warning('parse_sec_head: no match')

		if m is None:
			logging.fatal('SECTION m %s', repr(head))
			sys.exit(1)

		typ = m.group(1)
		if typ and typ in ' §':
			typ = None # only used by special sections
		enum = m.group(2)
		title = m.group(3).rstrip(']') + '.' # end with a period!
		status = None

	logging.debug('parse_sec_head: enum_parts typ enum title status %s %s %s %s %s', enum_parts, repr(typ), repr(enum), repr(title), status)

	return enum_parts, typ, enum, title, status

##
#
#
def parse_sectioncontent_xml(el, lvl):
	if el.tag in {'text'}:
		tel = etree.Element('text')

#		text = etree.tostring(el, method='text', encoding=str)
		text = ' '.join(etree.tostring(el, method='text', encoding=str).split())

		logging.debug('TEXT %s %s', lvl, text)

		tel.text = text

		return tel

	elif el.tag in {'psection'}:
		pel = etree.Element('p')

		# level
		lev = el.attrib['lev']
		if lev != lvl:
			# it seems some sections have parts that jump levels...
			logging.warning('PSECTION unequal level %s %s', lvl, lev)

		# enum
		enum = el.find('enum')
		if enum is not None:
			enum.attrib.clear()
			pel.append(enum)

		# title
		title = el.find('head')
		if title is not None:
			title = ' '.join(etree.tostring(title, method='text', with_tail=False, encoding=str).split())
			titel = etree.SubElement(pel, 'title')
			titel.text = title

		logging.debug('PSECTION %s %s %s %s', enum, title, lvl, lev)

		# sub el
		nlvl = str(int(lvl) + 1)
		for subel in el:
			newsubel = parse_sectioncontent_xml(subel, nlvl)
			if newsubel is not None:
				pel.append(newsubel)

		return pel

	else:
		logging.debug('skipped %s', el.tag)
		return None

# do it
if __name__ == "__main__":
	main()

