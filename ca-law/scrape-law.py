#! /usr/bin/python3 -uW all
# -*- coding: utf-8 -*-

##
# scrape-law.py - convert the California Codes into RDF
# Copyright (C) 2011-2013  Eric S. Branson <bransone@ecs.csus.edu>
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

usage="""
scrape-law.py - convert the California Codes into RDF

Get the data from <ftp://www.leginfo.ca.gov/pub/bill/> e.g.
<ftp://www.leginfo.ca.gov/pub/bill/pubinfo_2013.zip>

Usage:	scrape-law.py [options] file
Arguments:

	file		ZIP file of the LC data
	-d		enable debugging (twice for verbose)
	-c code		output by code
	-h		show this help and exit

NOTE: To use on Windows console, "SET PYTHONIOENCODING=cp437:replace".
"""

import sys
import getopt
import logging
import zipfile
import csv
import string
import io
import itertools
import re
#import os.path
#import tempfile
try:
	import lxml.etree as etree
except ImportError:
	import xml.etree.ElementTree as etree
try:
	import rdflib, rdflib.graph
#	import rdflib, rdflib.graph, rdflib.store
#	import rdflib_sqlite
except ImportError:
	logging.fatal('cannot load rdflib')
	sys.exit(1)

#rdflib.plugin.register(
#	"SQLite", rdflib.store.Store,
#	"rdflib_sqlite.SQLite", "SQLite")

LC_URL = "http://data.lc.ca.gov/ontology/lc-law-onto-0.1#"
LC = rdflib.Namespace(LC_URL)
CODES_URL = "http://data.lc.ca.gov/dataset/codes/"
STATS_URL = "http://data.lc.ca.gov/dataset/statutes/"
#T_C = LC['Code']
T_D = T_C = LC['CodeDivision']
P_D_TYPE = LC['hasCodeDivisionType']
P_D_ENUM = LC['hasCodeDivisionEnum']
P_D_TITLE = LC['hasCodeDivisionTitle']
P_D_SUB = LC['hasCodeSubdivisions']
P_D_SEC = LC['hasCodeSections']
T_S = LC['CodeSection']
P_S_ENUM =  LC['hasCodeSectionEnum']
P_S_STAT = LC['isCodificationOf']
P_S_STATS = LC['isCodificationOfSection']
P_S_HIST = LC['hasCodeSectionHistoryNote']
P_S_PARA = LC['hasCodeParagraphs']
T_P = LC['CodeParagraph']
P_P_SUBP = LC['hasCodeSubParagraph']
P_P_ENUM = LC['hasCodeParagraphEnum']
P_P_TEXT = LC['hasCodeParagraphText']
P_P_LVL = LC['hasCodeParagraphIndent']

##
# Entry function. Parse parameters, call main function.
#
def main():
	process_codes = []
	print_codes = False
	debug = False

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ohdc:')
	except getopt.GetoptError as e:
		logging.fatal('getopt error: %s %s', e, usage)
		sys.exit(1)

	if len(args) < 1:
		logging.fatal('need filename %s', usage)
		sys.exit(1)

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
		elif opt in ('-c'):
			process_codes.append(arg.upper())
		elif opt in ('-o'):
			print_codes = True
		else:
			logging.fatal('invalid flag: %s %s', opt, usage)
			sys.exit(1)

	try:
		zfn = args[0]
		zf = zipfile.ZipFile(zfn)
	except IOError as e:
		logging.fatal('opening files: %s %s', e, usage)
		sys.exit(1)

	do_it(zf, process_codes, print_codes)

	zf.close()

##
# Build the organizational graph, match sections to their data, and read
# section text from file as we convert t,,,
#
def do_it(zf, codes, print_codes):
	logging.info('parsing law db...')
	law = parse_org(zf)

	logging.info('matching sections...')
	matchsecs(law, zf)

	if print_codes:
		print(law.keys())
		sys.exit(0)

	for code in filter(lambda x: not len(codes) or x in codes, list(law.keys())):
#		tmpf = tempfile.NamedTemporaryFile()
#		g = rdflib.graph.Graph('SQLite')
#		assert g.open(tmpf.name, create=True) == rdflib.store.VALID_STORE
		g = rdflib.graph.Graph()
		g.bind('lc', LC_URL)
		logging.info('converting organization to RDF...')
		for tup in org_to_rdf_gen(zf, None, law[code]):
			g.add(tup)
		fn = code.lower() + '-org.ttl'
		logging.info('writing %s...', fn)
		g.serialize(fn, 'turtle')
		del g

		g = rdflib.graph.Graph()
		g.bind('lc', LC_URL)
		logging.info('converting sections to RDF...')
		for tup in sec_to_rdf_gen(zf, None, law[code]):
			g.add(tup)
		fn = code.lower() + '-sec.ttl'
		logging.info('writing %s...', fn)
		g.serialize(fn, 'turtle')
		del g

		del law[code]
#		tmpf.close()

##
# Recursively traverse law tree, yielding semantic triples for
# organization.
#
def org_to_rdf_gen(zf, code, item):
	# get org data
#	typ, n, t = item['header']
	typ, n, t = item[0]

	# create organizational node
	if code is None:
		org = rdflib.URIRef(build_url(n))
		code = n
		yield (org, rdflib.RDF.type, T_C)
	else:
		org = rdflib.BNode()
		assert org is not None
		yield (org, rdflib.RDF.type, T_D)

	# add type
	if typ:
		yield (org, P_D_TYPE, rdflib.Literal(typ))

	# add enumerations
	if n and code != n:
		yield (org, P_D_ENUM, rdflib.Literal(n))

	# add title
	if t:
		yield (org, P_D_TITLE, rdflib.Literal(t))

	# sub org items
	seq = rdflib.BNode()
	count = itertools.count(1)
	for subitem in item[1]:
		suborg = yield from org_to_rdf_gen(zf, code, subitem)
		assert suborg
		yield (seq, rdflib.RDF[next(count)], suborg)
	if next(count) != 1:
		yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
		yield (org, P_D_SUB, seq)

	# sub sec items
	seq = rdflib.BNode()
	count = itertools.count(1)
	for subitem in item[2]:
		enum, fn, (stat_y, stat_c, stat_s, hist) = subitem
		sec = rdflib.URIRef(build_url(code, enum))
		yield (seq, rdflib.RDF[next(count)], sec)
	if next(count) != 1:
		yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
		yield (org, P_D_SEC, seq)

	return org

##
# Recursively traverse law tree, yielding semantic triples for
# sections.
#
def sec_to_rdf_gen(zf, code, item):
	# get org data
	if code is None:
#		_, n, _ = item['header']
		_,n,_ = item[0]
		code = n

	# recurse organization
	for subitem in item[1]:
		yield from sec_to_rdf_gen(zf, code, subitem)
	
	# base case: section items
	for subitem in item[2]:
		# get section data
		(enum, fn, (stat_y, stat_c, stat_s, hist)) = subitem

		# create section node
		sec = rdflib.URIRef(CODES_URL + code + '/' + enum)
		yield (sec, rdflib.RDF.type, T_S)

		# add info
		yield (sec, P_S_ENUM, rdflib.Literal(enum))

		url = STATS_URL
		if stat_y:
			url += stat_y
		if stat_c:
			if not stat_y:
				url += 'Nil'
			url += '/' + stat_c
		if stat_y or stat_c:
			yield (sec, P_S_STAT, rdflib.URIRef(url))
		if stat_s:
			yield (sec, P_S_STATS, rdflib.Literal(stat_s))
		if hist:
			yield (sec, P_S_HIST, rdflib.Literal(hist))

		# add section p from file
		logging.debug('parsing %s in %s...', enum, fn)
		yield from parse_sec_xml_gen(zf, sec, fn)

##
# XXX
#
def parse_sec_xml_gen(zf, sec, fn):
		with zf.open(fn) as f:
			tree = etree.parse(f)
		seq = rdflib.BNode()
		count = itertools.count(1)
		for el in tree.getroot():
			if el.tag != 'p':
				logging.debug('to_rdf_gen: skip %s %s %s', fn, el.tag, el.attrib)
				continue
			node = yield from parse_sec_xml_r(el) # parse into RDF
			yield (seq, rdflib.RDF[next(count)], node)
		if next(count) != 1:
			yield (seq, rdflib.RDF.type, rdflib.RDF.Seq)
			yield (sec, P_S_PARA, seq)
		del tree

##
# Build a HTTP URL from a code and enum.
#
def build_url(code, enum=None):
		if enum is not None:
			return CODES_URL + code + '/' + enum
		else:
			return CODES_URL + code

##
# Parse the organizational structure into a nested dictionary.
#
# Each level is a dictionary of the lower levels. The lowest level is
# data of the form [(desc, (start, end), []), ...] where the empty
# list is for the secions.
#
# For the data of a non-lowest-level, follow the 'NULL' keys on
# down, as when
#
def parse_org(zf):
	law = {}

	# codes_tbl:
	#
	# (
	#	CODE,
	#	TITLE
	# )
	with io.TextIOWrapper(zf.open('CODES_TBL.dat'), encoding='utf-8', newline='') as codes_tbl:
		for r in csv.reader(codes_tbl, 'excel-tab', quotechar='`'):
			code = r[0]
			title = r[1].strip('* ').split(' - ')[0]
#			law[code] = {'header': None, 'org': SparseList(), 'sec': SparseList()}
			law[code] = [None,SparseList(),SparseList()]
#			l = law[code]
#			l['header'] = ('code', code, title)
			law[code][0] = ('code',code,title)

	# law_toc_tbl:
	#
	# (
	#	LAW_CODE,
	#	DIVISION,
	#	TITLE,
	#	PART,
	#	CHAPTER,
	#	ARTICLE,
	#	HEADING,
	#	ACTIVE_FLG,
	#	TRANS_UID,
	#	TRANS_UPDATE,
	#	NODE_SEQUENCE,
	#	NODE_LEVEL,
	#	NODE_POSITION,
	#	NODE_TREEPATH,
	#	CONTAINS_LAW_SECTIONS,
	#	HISTORY_NOTE,
	#	OP_STATUES,
	#	OP_CHAPTER,
	#	OP_SECTION
	# ) 
	with io.TextIOWrapper(zf.open('LAW_TOC_TBL.dat'), encoding='utf-8', newline='') as law_toc_tbl:
		for row in csv.reader(law_toc_tbl, 'excel-tab', quotechar='`'):
			# parse row
			code = row[0]
			if row[7] == 'Y':
				active = True
			elif row[7] == 'N':
				active = False
			else:
				logging.fatal('unknown row[7]')
				sys.exit(1)
			path = row[13]
			typ, n, t, s, e = parse_head(row[6])
			if row[14] == 'Y':
				empty = False
			elif row[14] == 'N':
				empty = True
			else:
				logging.fatal('unknown row[14]')
				sys.exit(1)
			if row[16] == 'NULL':
				op_stat = None
			else:
				op_stat = row[16]
			if row[17] == 'NULL':
				op_ch = None
			else:
				op_ch = row[17]
			if row[18] == 'NULL':
				op_sec = None
			else:
				op_sec = row[18]
#			# checks
#			if not empty and (s is None or e is None):
#				warn('DB insists', code, path, typ, n, t, 'has el but doesnt give s/e')
			if not active:
				logging.info('not active: %s %s %s %s %s %s',code,typ,n,t,s,e)
#			if empty:
#				info('empty:',typ,n,t,s,e)
			if (op_ch and not op_stat) or (op_sec and (not op_stat or not op_ch)):
				logging.info('~stat*(ch+sec): %s %s %s %s %s %s %s %s %s',op_stat,op_ch,op_sec,code,typ,n,t,s,e)
			if op_stat:
				try:
					y = int(op_stat)
				except ValueError:
					logging.info('years are in N: %s %s %s %s %s %s %s %s %s',op_stat,op_ch,op_sec,code,typ,n,t,s,e)
				else:
					if y < 1849 or y > 2013:
						logging.info('stat: %s %s %s %s %s %s %s %s %s',op_stat,op_ch,op_sec,code,typ,n,t,s,e)
#					op_stat
			org_start(law[code], path, (typ, n, t))

	return law

##
# parse the heading/description and section range
#
def parse_head(head):
#	debug('head: head', head)

	try:
		split1 = head.split(None, 1)
		typ = split1[0].lower()
		split2 = split1[1].split(None, 1)
		enum = split2[0].rstrip('.')
		if '[' in split2[1] and ']' in split2[1]:
			desc = split2[1].split('[')[0].strip()
			start = split2[1].rsplit(' - ',1)[0].rsplit('[',1)[-1].rstrip(']').rstrip('.')
			end = split2[1].rsplit(' - ',1)[1].split(']',1)[0].lstrip('[').rstrip('.')
			if start == [''] or end == ['']:
				start = end = None
		else:
			desc = split2[1]
			start = end = None

		# to throw ValueError
		float(enum)

	except IndexError as e:
		logging.debug('head: IndexError: %s %s', e, repr(head))
		desc = head
		typ = None
		enum = None
		start = end = None

	except ValueError as e:
		logging.debug('head: ValueError: %s %s', e, repr(head))

		# check if it starts with a number
		if enum[0] in string.digits:
			logging.debug('head: OK it starts w/ number')

		# check if its a roman numeral
		elif len(enum) == len([c for c in enum if c in 'IVXLCDM']):
			# "THE CIVIL CODE ..."
			if typ in {'part', 'subpart', 'title', 'subtitle', 'chapter', 'subchapter', 'article'}:
				logging.debug('head: OK it is roman numeral')

			else:
				logging.debug('head: CIVIL is not a roman numeral!')

				desc = head
				typ = None
				enum = None
				start = end = None

		else:
			logging.debug('head: NOT enum: %s', repr(head))

			desc = head
			typ = None
			enum = None
			start = end = None

#	debug('head: typ enum desc start end', typ, repr(enum), repr(desc), start, end)

	return typ, enum, desc, start, end

##
# Use a DB "treepath" (one-based indexing separated by a period) to traverse
# a list (actually a SparseList), creating a list at each traversal if
# necessary.
#
# A list represents an organizational element, with the zeroth item
# representing the organizational element data, the subsequent items
# representing its children, and any non-zeroth non-list items representing
# sections.
#
# Ex:
#
# {'header': ('type1', 'enum1' 'title1'), 'org': [{'header': ('type2', 'enum1' 'title1'), 'sec': [('enum1', 'fn1', ('staty1', 'statch1')), ('enum2', 'fn2', ('staty2', 'statch2'))]}, {'header':('type2', 'enum2' 'title2'), 'sec': [('enum3', 'fn3', ('staty3', 'statch3')), ...]}, ...]}
#
def org_get(l, path):
	for p in path.split('.'):
#		debug('org_get path p l:', p, l)
		i = int(p)-1 # paths are one-based
#		ln = l['org'][i]
		ln = l[1][i]
		if ln is None:
#			l['org'][i] = {'header': None, 'org': SparseList(), 'sec': SparseList()}
			l[1][i] = [None, SparseList(), SparseList()]
#			ln = l['org'][i]
			ln = l[1][i]
		l = ln
#	debug('org_get path p l:', path, l)
	return l

##
# Traverse a list and add the data to the zeroth position of the list
# at that level. Used for organizational elements as the zeroth item
# is always the organizational element's data.
#
def org_start(l, path, data):
	l = org_get(l, path)
#	l['header'] = data
	l[0] = data
#	debug('org_start path data l', path, data, l)

##
# Traverse a list and append the data to the list at that level.
#
def org_app(l, path, pos, data):
	l = org_get(l, path)
	i = int(pos)-1 # paths are one-based
#	l['sec'][i] = data
	l[2][i] = data
#	debug('org_app path pos data l', path, pos, data, l)

##
# A list that will automatically grow, setting preceeding items as None.
#
# See <http://stackoverflow.com/questions/1857780/sparse-assignment-list-in-python>.
#
class SparseList(list):
	def __setitem__(self, index, value):
		missing = index - len(self) + 1
		if missing > 0:
			self.extend([None] * missing)
		list.__setitem__(self, index, value)

	def __getitem__(self, index):
		try:
			return list.__getitem__(self, index)
		except IndexError:
			return None

##
# Match all sections and add their data to the organization data
# structure. Only one element, the deepest element, gets the data.
#
# TODO: what do brackets in section mean?
# TODO: mod for use in CONS
#
def matchsecs(law, zf):
	rows = {} 

	logging.info('parsing and matching section tables...')

	# law_toc_sections_tbl:
	#
	# (
	#       ID,
	#       LAW_CODE,
	#       NODE_TREEPATH,
	#       SECTION_NUM,
	#       SECTION_ORDER,
	#       TITLE,
	#       OP_STATUES,
	#       OP_CHAPTER,
	#       OP_SECTION,
	#       TRANS_UID,
	#       TRANS_UPDATE,
	#       LAW_SECTION_VERSION_ID,
	#       SEQ_NUM
	# )	
	with io.TextIOWrapper(zf.open('LAW_TOC_SECTIONS_TBL.dat'), encoding='utf-8', newline='') as law_toc_sec_tbl:
		for r1 in csv.reader(law_toc_sec_tbl, 'excel-tab', quotechar='`'):
			key = r1[11]
			code = r1[1]
			path = r1[2]
			sec = r1[3].strip('[]').rstrip('.') # not sure what brackets mean
			pos = r1[4]
			assert int(pos) != 0
			if sec.count(' '):
				sec = sec.split()[-1]
			rows[key] = [code, path, sec, pos]

	# law_section_tbl:
	#
	# (
	#       id,
	#       law_code,
	#       section_num,
	#       op_statutes,
	#       op_chapter,
	#       op_section,
	#       effective_date,
	#       law_section_version_id,
	#       division,
	#       title,
	#       part,
	#       chapter,
	#       article,
	#       history,
	#       content_xml,
	#       active_flg,
	#       trans_uid,
	#       trans_update,
	# )
	#
	with io.TextIOWrapper(zf.open('LAW_SECTION_TBL.dat'), encoding='utf-8', newline='') as law_sec_tbl:
		for r2 in csv.reader(law_sec_tbl, 'excel-tab', quotechar='`'):
#			code = r2[1]
			key = r2[7]
			stat_y = r2[3]
			stat_c = r2[4]
			stat_s = r2[5]
			hist = r2[13]
			fn = r2[14] # filename
			act = r2[15]

			if act != 'Y':
				logging.fatal('row not active! %s', row)
				sys.exit(1)

			if stat_y == 'NULL':
				stat_y = None
			if stat_c == 'NULL':
				stat_c = None
			if stat_s == 'NULL':
				stat_s = None
			stat = (stat_y,stat_c,stat_s,hist)

			rows[key].append(fn)
			rows[key].append(stat)

	logging.info('adding section tables to law structure...')

	for key in rows:
		code = rows[key][0]
		path = rows[key][1]
		sec = rows[key][2]
		pos = rows[key][3]
		fn = rows[key][4]
		stat = rows[key][5]

		org_app(law[code], path, pos, (sec, fn, stat))

regex = re.compile('^\(([^)])\)')

##
# Levels:
# 0 - No enum.
# 1 - (a)
# 2 - (1)
# 3 - (A)
# 4 - (i)
#
def text_to_para(text):
	enums = regex.findall(text)
	if len(enums):
		if len(enums) > 1:
			logging.warning('AHA!', enums, text)
		split = text.split(maxsplit=1)
		if len(split) > 1:
			para = split[1]
			logging.debug('text match %s', enums)
			return enums, para
		else: # just enums?
			logging.warning('no para %s', text)
			return enums, None
	else:
		logging.debug('text no %s', text[:10])
		return None, text

##
# XXX Parse (interpret, convert, and clean) the XML file.
#
def parse_sec_xml_r(el):
	if el.tag == 'p':
		pnode = rdflib.BNode()
		text = io.StringIO()
		yield (pnode, rdflib.RDF.type, T_P)

		# add text
		if el.text:
			text.write(el.text)

		# iterate over sub el and prepare to append them to el
		for subel in el:
			s = yield from parse_sec_xml_r(subel)
			if isinstance(s, str):
				text.write(s)
			else:
				logging.info('parse_sec_xml_r p subel %s', s)

		# add tail
		if el.tail:
			text.write(el.tail)

#		logging.debug('parse_sec_xml_r: text %s', text)

		# interpret text
		enums, para = text_to_para(text.getvalue())
		text.close()
		if enums:
			for enum in enums:
				yield (pnode, P_P_ENUM, rdflib.Literal(enum))
				logging.debug('parse_sec_xml_r: enum %s', enum)
		if para:
			yield (pnode, P_P_TEXT, rdflib.Literal(para))
			logging.debug('parse_sec_xml_r: para %s', para)

		ret = pnode

	# EnSpace and EmSpace span tags represents a space so and have tails but no text or children
	elif el.tag == 'span' and 'class' in el.attrib and (el.attrib['class'] == 'EnSpace' or el.attrib['class'] == 'EmSpace' or el.attrib['class'] == 'ThinSpace'):
		ss = [' ']
		if el.tail:
			ss.append(el.tail)
		ret = ''.join(ss)

	# SmallCaps have text and tails but have no children ... right?
	elif el.tag == 'span' and 'class' in el.attrib and el.attrib['class'] == 'SmallCaps':
		ss = []
		if el.text:
			ss.append(el.text)
		if el.tail:
			ss.append(el.tail)
		if len(ss) > 0:
			ret = ' '.join(''.join(ss).split())
		else:
			ret = None

	elif el.tag == 'br':
		ret = ' '

	elif el.tag == '{http://lc.ca.gov/legalservices/schemas/caml.1#}Fraction':
		assert len(el) == 2
		num = el[0].text
		den = el[1].text
		math = etree.Element('math', nsmap={None: "http://www.w3.org/1998/Math/MathML"})
		frac = etree.SubElement(math, 'mfrac')
		etree.SubElement(frac, 'mn').text = num
		etree.SubElement(frac, 'mn').text = den
		ret = etree.tostring(math)

	elif el.tag == 'i':
		if len(el) > 0:
			logging.info('tag i has subelements!')
		ret = el.text

	else:
		logging.debug('tag %s unknown %s', el.tag, el.attrib)
		ret = ''

	return ret

# do it
if __name__ == "__main__":
	main()

