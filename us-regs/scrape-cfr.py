#! /usr/bin/python3 -W all
# -*- coding: utf-8 -*-

##
# scrape-cfr.py - convert the Code of Federal Regulations into RDF
#

usage="""
scrape-cfr.py - convert the Code of Federal Regulations into RDF

This little script converts the GPO FDsys bulk XML files into
RDF for further semantic annoation and processing. Get the data from
<http://www.gpo.gov/fdsys/bulkdata/CFR/> or let this program
download it for you.

Usage:	scrape-cfr.py [options] [file [file ..]]
Arguments:

	file		GPO FDsys XML file
	-o file		output filename (default: stdout)
 	-d, --debug	enable debuging output (twice for verbose)
"""

import sys
import getopt
import os
import os.path
import lxml.etree
import re
import string

#
# Globals.
#

flags = {'debug': False, 'verbose': False}

##
# Entry function. Parse paramters, call main function.
#
def main():
	ifn = None
	ofn = None

	# parse commandline for flags and arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'd')
	except getopt.GetoptError:
		fatal('getopt error', usage, end='')

	# parse flags
	for opt, arg in opts:
		if opt in {'-d', '--debug'}:
			if flags['debug']:
				flags['verbose'] = True
			flags['debug'] = True
		else:
			fatal('invalid flag', opt, usage)

	# parse arguments
	if len(args) > 0:
		for arg in args:
			if not ifn:
				ifn = arg
			elif not ofn:
				ofn = arg
			else:
				fatal('too many files', usage)
	else:
		fatal('need file', usage)

	# open files
	try:
		fin = open(ifn, 'r')
		if ofn:
			fout = open(ofn, 'wb')
		else:
			fout = sys.stdout
	except IOError as e:
		fatal(e)

	# do it
	do_it(fin, fout)

	# cleanup
	fin.close()
	fout.close()

##
# Do it. 
#
def do_it(fin, fout):
	parser = lxml.etree.XMLParser(remove_blank_text=True, huge_tree=True)
	tree = lxml.etree.parse(fin, parser)
	r = tree.getroot()
	assert r.tag == 'CFRDOC'
	state = {'title': None, 'subtitle': None, 'chapter': None, 'subchapter': None, 'part': None}
	lookup = {'enum': {}, 'title': {}}

	# get org
	for el in r.xpath('.//*[self::TITLE or self::SUBTITLE or self::CHAPTER or self::SUBCHAP or self::PART]'):
		if el.tag in orgtypes.keys():
			org = orgtypes[el.tag](el)
			header, content = org
#			debug(header, content)
			subel = org_tup2el_r(lookup, org)

	# get sections
	for el in r.xpath('//SECTION'):
		assert el.tag == 'SECTION'
		sel, enum, title, status = new_sec(el)
		if enum in lookup['enum']:
			debug('section', repr(enum), repr(title))
		elif status and 'reserved' in status:
			warn('reserved enum not in lookup', repr(enum))
		else:
			warn('enum not in lookup', repr(enum), repr(title))

#
# Parse organization.
#

##
# Convert (recursively) org tuple into XML element. Also add
# sections (recursively) from org tuple so we can match them later.
#
def org_tup2el_r(lookup, org):
	assert type(org) == tuple
	if len(org) == 2:
		header, content = org
		debug(header)
		if content is not None:
			for sub in content:
				org_tup2el_r(lookup, sub)
	elif len(org) == 1:
		header, = org
		debug(header)
		typ, enum, title, stat = header
		lookup['enum'][enum] = lookup['title'][title] = None
	else:
		fatal('org_tup2el_r: invalid org')

##
#
#
def cfrdoc_iter_title(el):
	header = None
	tel = el.find('CFRTITLE/TITLEHD/HD')
	if tel is None:
		warn(el, 'has no derp', repr(lxml.etree.tostring(el, encoding=str)))
	else:
		header = parse_comb_header(tel)
	return (header, None)

##
#
#
def cfrdoc_iter_subtitle(el):
	header = None
	tel = el.find('HD')
	if tel is None:
		tel = el.find('RESERVED')
	if tel is None:
		warn(el, 'has no derp', repr(lxml.etree.tostring(el, encoding=str)))
	else:
		header = parse_comb_header(tel)
	return (header, None)

##
#
#
def cfrdoc_iter_chapter(el):
	header = None
	tel = el.find('TOC/TOCHD/HD')
	if tel is None:
		tel = el.find('HD')
		if tel is None:
			tel = el.find('RESERVED')
	if tel is None:
		warn(el, 'has no derp', repr(lxml.etree.tostring(el, encoding=str)))
	else:
		header = parse_comb_header(tel)
	return (header, None)

##
#
#
def cfrdoc_iter_subchap(el):
	header = None
	tel = el.find('HD')
	if tel is None:
		tel = el.find('RESERVED')
	if tel is None:
		warn(el, 'has no derp', repr(lxml.etree.tostring(el, encoding=str)))
	else:
		header = parse_comb_header(tel)
	return (header, None)

##
#
#
def cfrdoc_iter_part(el):
	# find header
	tel = el.find('HD')
	if tel is None:
		tel = el.find('RESERVED')

	# parse header
	header = parse_comb_header(tel)

	sectioncontent = []
	sectioncur = {'SECTNO': None, 'SUBJECT': None}
	sectionstatus = set()

	for subel in el.xpath('CONTENTS/*'):
		if subel.tag in parttypes.keys():
			keyvals = parttypes[subel.tag](subel)
			for key, val in keyvals:
				# is reserved
				if subel.tag == 'RESERVED':
					sectionstatus.add('reserved')
				# add SECTNO to cur
				if subel.tag == 'SECTNO':
					sectioncur[key] = val
				# add to contents
				if subel.tag == 'SUBJECT' or subel.tag == 'RESERVED':
					if sectioncur['SECTNO'] != None:
						# extract
						typ = 'section'
						enum = sectioncur['SECTNO']
						title = val
						if sectionstatus == set():
							sectionstatus = None
						item = ((typ, enum, title, sectionstatus),)
						sectioncontent.append(item)
						# reset
						sectioncur['SECTNO'] = sectioncur['SUBJECT'] = None
						sectionstatus = set()
					elif val == None:
						pass
					else:
						warn('cfrdoc_iter_part subject: None in cur', repr(sectioncur), repr(lxml.etree.tostring(el, encoding=str)))
				# handle SUBPART
				if subel.tag == 'SUBPART':
					sectioncontent.append(val)
				# handle SUBJGRP
				if subel.tag == 'SUBJGRP':
					for pair in val:
						sectioncontent.append(pair)
		else:
			print('cfrdoc_iter_part skip', subel.tag)

	if None not in sectioncur.values():
		typ = 'section'
		enum = sectioncur['SECTNO']
		title = sectioncur['SUBJECT']
		item = ((typ, enum, title, sectionstatus), [])
		sectioncontent.append(item)
		warn('cfrdoc_iter_part: added cur')
	elif list(sectioncur.values()) != [None, None]:
		warn('cfrdoc_iter_part: None in cur', repr(sectioncur), repr(lxml.etree.tostring(el, encoding=str)))

	return (header, sectioncontent)

##
#
#
def part_iter_subpart(el):
	# find header
	for i,actel in enumerate(el):
		if actel.tag in {'HD', 'SUBJECT', 'RESERVED'}:
			break

	# parse header
	header = parse_comb_header(actel)

	if i == len(el)-1:
		return [(None, (header, []))]

	sectioncontent = []
	sectioncur = {'SECTNO': None, 'SUBJECT': None}
	sectionstatus = set()

	for subel in el[i+1:]:
		if subel.tag in subparttypes.keys():
			keyvals = subparttypes[subel.tag](subel)
			for key, val in keyvals:
				# is reserved
				if subel.tag == 'RESERVED':
					sectionstatus.add('reserved')
				# add SECTNO to cur
				if subel.tag == 'SECTNO':
					sectioncur[key] = val
				# add to contents
				if subel.tag == 'SUBJECT' or subel.tag == 'RESERVED':
					if sectioncur['SECTNO'] != None:
						# extract
						typ = 'section'
						enum = sectioncur['SECTNO']
						title = val
						if sectionstatus == set():
							sectionstatus = None
						item = ((typ, enum, title, sectionstatus),)
						sectioncontent.append(item)
						# reset
						sectioncur['SECTNO'] = sectioncur['SUBJECT'] = None
						sectionstatus = set()
					elif val == None:
						pass
					else:
						warn('part_iter_subpart subject: None in cur', repr(sectioncur), repr(lxml.etree.tostring(el, encoding=str)))
				# handle SUBJGRP
				if subel.tag == 'SUBJGRP':
					for pair in val:
						sectioncontent.append(pair)
		else:
			warn('part_iter_subpart skip', subel.tag)

	if None not in sectioncur.values():
		typ = 'section'
		enum = sectioncur['SECTNO']
		title = sectioncur['SUBJECT']
		item = ((typ, enum, title, sectionstatus), [])
		sectioncontent.append(item)
		warn('part_iter_subpart: added cur')
	elif list(sectioncur.values()) != [None, None]:
		warn('part_iter_subpart: None in cur', repr(sectioncur), repr(lxml.etree.tostring(el, encoding=str)))

	return [(None, (header, sectioncontent))]

##
#
#
def iter_subjgrp(el):
	t = ' '.join(lxml.etree.tostring(el[0], method='text', encoding=str).split())

	sectioncontent = []
	sectioncur = {'SECTNO': None, 'SUBJECT': None}
	sectionstatus = set()

	for subel in el[1:]:
		if subel.tag in subparttypes.keys():
			keyvals = subparttypes[subel.tag](subel)
			for key, val in keyvals:
				# is reserved
				if subel.tag == 'RESERVED':
					sectionstatus.add('reserved')
				# add SECTNO to cur
				if subel.tag == 'SECTNO':
					sectioncur[key] = val
				# add to contents
				if subel.tag == 'SUBJECT' or subel.tag == 'RESERVED':
					if sectioncur['SECTNO'] != None:
						# extract
						typ = 'section'
						enum = sectioncur['SECTNO']
						title = val
						if sectionstatus == set():
							sectionstatus = None
						item = ((typ, enum, title, sectionstatus),)
						sectioncontent.append(item)
						# reset
						sectioncur['SECTNO'] = sectioncur['SUBJECT'] = None
						sectionstatus = set()
					elif val == None:
						pass
					else:
						warn('part_iter_subpart subject: None in cur', repr(sectioncur), repr(lxml.etree.tostring(el, encoding=str)))

	return [(None, sectioncontent)]

##
#
#
def part_iter_sectno(el):
	t = ' '.join(lxml.etree.tostring(el, method='text', encoding=str).split())
	if t == '':
		t = None
	return [('SECTNO', t)]

##
#
#
def part_iter_subject(el):
	t = ' '.join(lxml.etree.tostring(el, method='text', encoding=str).split())
	if t == '':
		t = None
	return [('SUBJECT', t)]

##
#
#
orgtypes = {'TITLE': cfrdoc_iter_title, 'SUBTITLE': cfrdoc_iter_subtitle, 'CHAPTER': cfrdoc_iter_chapter, 'SUBCHAP': cfrdoc_iter_subchap, 'PART': cfrdoc_iter_part}

##
#
#
parttypes = {'SECTNO': part_iter_sectno, 'SUBJECT': part_iter_subject, 'RESERVED': part_iter_subject, 'SUBJGRP': iter_subjgrp, 'SUBPART': part_iter_subpart}
subparttypes = {'SECTNO': part_iter_sectno, 'SUBJECT': part_iter_subject, 'RESERVED': part_iter_subject, 'SUBJGRP': iter_subjgrp}

##
# Parse a combined header.
#
def parse_comb_header(el):
	typ = enum = t = None
	elt = ' '.join(lxml.etree.tostring(el, method='text', encoding=str).split())
	status = set()
	typs = {'title', 'subtitle', 'chapter', 'subchapter', 'part', 'subpart'}

	# is reserved
	if el.tag == 'RESERVED':
		status.add('reserved')
	if '[Reserved]' in elt:
		status.add('reserved')
		rets = elt.split('[Reserved]', 1)
		nelt = rets[0].strip()
		warn('merged new elt: reserved', repr(elt), repr(nelt))
		elt = nelt
	if '[RESERVED]' in elt:
		status.add('reserved')
		rets = elt.split('[RESERVED]', 1)
		nelt = rets[0].strip()
		warn('merged new elt: reserved', repr(elt), repr(nelt))
		elt = nelt

	# special case: 'S ubpart'
	if elt[:8] == 'S ubpart':
		nelt = 'Subpart' + elt[8:]
		warn('merged new elt: S ubpart', repr(elt), repr(nelt))
		elt = nelt

	# special case: 'Supart'
	if elt[:6] == 'Supart':
		nelt = 'Subpart' + elt[6:]
		warn('merged new elt: Supart', repr(elt), repr(nelt))
		elt = nelt

	# special case: 1st word merges 'Subpart' with enum
	if elt[0:7] == 'Subpart' and elt[7] not in {'s',' ','—'} or elt[0:8] == 'Subparts' and elt[8] not in {' ','—'}:
		if elt[0:8] == 'Subparts':
			nelt = 'Subparts ' + elt[8:]
		else:
			nelt = 'Subpart ' + elt[7:]
		warn('merged new elt: merged enum', repr(elt), repr(nelt))
		elt = nelt

	# normal case: contains '—'
	if '—' in elt:
		rets = elt.split('—',1)
		assert len(rets) == 2

		rets2 = rets[0].split(None,1)

		t = rets[1]
		if len(rets2) == 2:
			typ = rets2[0].lower()
			enum = rets2[1]
		else:
			typ = rets2[0].lower()
			enum = None

	# normal case: plural and contains '-'
	elif '-' in elt and elt.split(None,1)[0].lower()[-1] == 's':
		rets = elt.split()
		typ = rets[0].lower()
		enums = rets[1].split('-')
		assert len(enums) == 2
		enum = (enums[0], enums[1])
		t = ' '.join(rets[2:])

	# normal case: contains '-'
	elif '-' in elt:
		rets = elt.split('-',1)
		assert len(rets) == 2

		rets2 = rets[0].split(None,1)

		t = rets[1]
		if len(rets2) == 2:
			typ = rets2[0].lower()
			enum = rets2[1]
		else:
			typ = rets2[0].lower()
			enum = None

	# special case: is still obviously a header
	elif elt.split(None,1) != [] and (elt.split(None,1)[0].lower() in typs or elt.split(None,1)[0][:-1].lower() in typs):
		warn('header without hyphen', repr(elt))

		rets = elt.split()
		typ = rets[0].lower()

		# special case: 2nd word merges enum with 1st word of description
		yep = None
		for i,c in enumerate(rets[1]):
			if c in string.ascii_lowercase:
				yep = i-1
				break

		if yep is not None and yep > 0:
			newrets = rets[2:]
			newrets.insert(0, rets[1][yep:])
			enum = rets[1][:yep]
			t = ' '.join(newrets)
			warn('2nd word merges enum with 1st word of description', repr(enum), repr(t))

		# normal special case: 'typ enum title...'
		else:
			desc = ' '.join(rets[2:])
			if desc == '':
				desc = None
			enum = rets[1]
			t = desc
			warn('normal?', repr(typ), repr(enum), repr(t))

	# unknown
	else:
		warn('part_iter_subpart: cant parse header', repr(elt), repr(lxml.etree.tostring(el, encoding=str)))
		t = elt

	# remove plural type
	if typ is not None and typ[-1] == 's':
		typ = typ[:-1]
		warn('removed plural type', repr(typ))

	# confirm typ
	if typ not in typs:
		warn('unknown type', repr(typ))

	if t == '':
		t = None

	if status == set():
		status = None

	return typ, enum, t, status

#
# Parse sections.
#

##
#
#
def new_sec(el):
	enum = title = status = None
	sel = lxml.etree.Element('section')
	iel = lxml.etree.SubElement(sel, 'info')

	enum, title, status = parse_el_info(el)

	# add info
	if enum:
		if isinstance(enum, str):
			enumel = lxml.etree.SubElement(iel, 'enum')
			enumel.text = enum
		elif isinstance(enum, tuple):
			enumsel = lxml.etree.SubElement(iel, 'enums')
			enumel0 = lxml.etree.SubElement(enumsel, 'enum')
			enumel0.attrib['type'] = 'beg'
			enumel0.text = enum[0]
			enumel1 = lxml.etree.SubElement(enumsel, 'enum')
			enumel1.attrib['type'] = 'end'
			enumel1.text = enum[1]
		else:
			fatal('new_sec unknown enum type:', type(enum))

	if title:
		titel = lxml.etree.SubElement(iel, 'title')
		titel.text = title

	if status:
		sel.attrib['status'] = ','.join(status)

	# get and add text
	for subpel in el.xpath('P'):
		textel = lxml.etree.SubElement(sel, 'text')
		text = lxml.etree.tostring(subpel, method='text', encoding=str).replace('\n', '').strip()
		textel.text = text

	return sel, enum, title, status

##
#
#
def parse_el_info(el):
	enum = title = None
	status = set()

	# get number
	sn = el.find('SECTNO')
	if sn is None:
		warn('new_sec no SECTNO:', repr(lxml.etree.tostring(el, encoding=str)))
	else:
		snt = ' '.join(lxml.etree.tostring(sn, method='text', encoding=str).split())
#		debug('new_sec snt:', repr(snt))

		# numbers
		sntnew = snt.replace('§', '').strip()
		if '§§' in snt:
			if '—' in snt:
				sntnewnew = sntnew.split('—')
				assert len(sntnewnew) == 2
				sntnew = (sntnewnew[0], sntnewnew[1])
			elif ' through ' in snt:
				sntnewnew = sntnew.split(' through ')
				assert len(sntnewnew) == 2
				sntnew = (sntnewnew[0], sntnewnew[1])
			elif '-' in snt:
				if snt.count('-') == 1:
					sntnewnew = sntnew.split('-')
					assert len(sntnewnew) == 2
					sntnew = (sntnewnew[0], sntnewnew[1])
				elif snt.count('-') == 2:
					sntnewnew = '.'.join(sntnew.rsplit('-',1))
					sntnewnewnew = sntnewnew.split('-')
					assert len(sntnewnewnew) == 2
					warn('parse_el_info sntnew converted', repr(sntnew), repr(sntnewnewnew))
					sntnew = (sntnewnewnew[0], sntnewnewnew[1])
				elif snt.count('-') == 3:
					sntnewnew = sntnew.split('-')
					assert len(sntnewnew) == 4
					left = '-'.join([sntnewnew[0], sntnewnew[1]])
					right = '-'.join([sntnewnew[2], sntnewnew[3]])
					sntnew = (left, right)
			if isinstance(sntnew, str) or len(sntnew) != 2:
				warn('parse_el_info len(sntnew) != 2', repr(sntnew), repr(lxml.etree.tostring(el, encoding=str)))

		if sntnew is not None and len(sntnew):
			enum = sntnew
		else:
			warn('new_sec empty SECTNO.text:', repr(sntnew), repr(lxml.etree.tostring(el, encoding=str)))
			enum = None

	# special case: 'Sec.' in enum
	# special case: 'Section' in enum
	# special case: whitespace in enum

	# get title
	tel = el.find('SUBJECT')
	if tel is None:
		tel = el.find('HD')
		if tel is None:
			tel = el.find('RESERVED')
			if tel is None:
				warn('parse_el_info no SUBJECT or HD', repr(lxml.etree.tostring(el, encoding=str)))
				t = ''
			else:
				t = ' '.join(lxml.etree.tostring(tel, method='text', encoding=str).split())
				status.add('reserved')
		else:
			t = ' '.join(lxml.etree.tostring(tel, method='text', encoding=str).split())

	else:
		t = ' '.join(lxml.etree.tostring(tel, method='text', encoding=str).split())

	# is reserved; remove '[Reserved]' and '[RESERVED]' from title and normalize
	if tel.tag == 'RESERVED':
		status.add('reserved')
	if '[Reserved]' in t:
		status.add('reserved')
		rets = t.split('[Reserved]', 1)
		nt = rets[0].strip()
		warn('merged new t: reserved', repr(t), repr(nt))
		t = nt
	if '[RESERVED]' in t:
		status.add('reserved')
		rets = t.split('[RESERVED]', 1)
		nt = rets[0].strip()
		warn('merged new t: reserved', repr(t), repr(nt))
		t = nt

	# parse title
	if enum is None:
		# if the enum was accidentally part of header
		rets = t.split()
		try:
			i = float(rets[0])
			# made it
			enum = rets[0]
			t = ' '.join(rets[1:])
			warn('new_sec_info extracted enum', repr(enum), repr(title))
		except Exception:
			pass

	# normalize
	if t == '':
		t = None

	if status == set():
		status = None

	return enum, t, status

##
#
#
def debug(*args, prefix='DEBUG:', file=sys.stdout, output=False, **kwargs):
	if output or flags['verbose']:
		if prefix is not None:
			print(prefix, *args, file=file, **kwargs)
		else:
			print(*args, file=file, **kwargs)

##
# Print error info and exit.
#
def fatal(*args, prefix='FATAL:', **kwargs):
	debug(*args, prefix=prefix, file=sys.stderr, output=True, **kwargs)
	sys.exit(1)

##
# Print warning info.
#
def warn(*args, prefix='WARNING:', output=False, **kwargs):
	if output or flags['debug']:
		debug(*args, prefix=prefix, file=sys.stderr, output=True, **kwargs)

##
# Print info.
#
def info(*args, prefix='INFO:', output=False, **kwargs):
	if output or flags['debug']:
		debug(*args, prefix=prefix, output=True, **kwargs)

# do it
if __name__ == "__main__":
	main()

