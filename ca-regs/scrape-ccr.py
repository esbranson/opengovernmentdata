#! /usr/bin/python3 -uW all
# -*- coding: utf-8 -*-

##
# scrape-ccr.py - convert the California Code of Regulations into RDF
#

# NOTES:
#
# LN_C seems to be a latent note for chapter
#

usage="""
scrape-ccr.py - convert the California Code of Regulations into RDF

Get the data from <https://law.resource.org/pub/us/ccr/> or pay
$2000 for it.

Usage:	scrape-ccr.py [options] file [file ..]
Arguments:

	file		input RTF file from the Official CCR CD-ROM
	-o file		output RDF file ('-' for stdout) (default: file.ttl)
	-d		enable debuging output (twice for verbose)
	-s		step through execution
"""

import sys
import os
import getopt
import xml.etree.ElementTree
import re
import uno
import unohelper
import xml.sax.saxutils
import shlex
import subprocess
import time

##
# Global flags.
#
flags = {'debug': False, 'verbose': False, 'step': False}

##
# Entry function. Parse paramters, call main function.
#
def main():
	outfile = None

	# parse commandline for flagss and arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ds')
	except getopt.GetoptError:
		fatal('getopt error', usage, end='')

	# parse flags
	for opt, arg in opts:
		if opt in {'-d', '--debug'}:
			if flags['debug']:
				flags['verbose'] = True
			flags['debug'] = True
		elif opt in {'-s', '--step'}:
			flags['step'] = True
		elif opt in ('-o'):
			outfile = arg
		else:
			fatal('invalid flag', opt, usage)

	# parse arguments
	if len(args) > 0:
		infiles = args
	else:
		fatal('need CCR file', usage, end='')

	# do it
	for infile in infiles:
		# open files
		try:
			fin = OOFile(infile)
			if outfile:
				fout = open(outfile, 'wb')
			else:
				fout = sys.stdout
		except IOError as e:
			fatal('opening files')

		# do it
		do_it(fin, fout)

		# cleanup
		fin.close()
		if outfile:
			fout.close()

##
# Do it.
#
def do_it(fin, fout):
	state = State()
	skipped = {}

	for line in fin:
		if line.ltype in {'LVL0', 'LVL1', 'LVL2', 'LVL3', 'LVL4', 'LVL5', 'LVL6', 'LVL7', 'SUBLVL0', 'SUBLVL1', 'SECTION', 'APPENDIX', 'SECTION PARAGRAPH', 'NOTEP', 'HISTP', 'ANOTEP'}:
			if len(line.line.strip()) > 0:
				debug(' ', line.ltype, ': ', line.line, sep='')
			else:
				debug('!', line.ltype)
				warn(line.ltype, 'is empty')
		else:
			debug('!', line.ltype)

		# is beginning of new element
		if line.ltype in {'LVL0', 'LVL1', 'LVL2', 'LVL3', 'LVL4', 'LVL5', 'LVL6', 'SECTION', 'APPENDIX'}:
			state.event_org(line)

		# attach regular text to current note / history element
		elif line.ltype in {'NOTEP', 'HISTP'}:
			state.event_nh(line)

		# attach regular text to current section element
		elif line.ltype in {'SECTION PARAGRAPH', 'ANOTEP'}:
			state.event_p(line)

		# ignore everything else
		else:
			state.skip(line)

		if flags['step']:
			f = input()

	state.toxml(fout)

	info('processed:', state.counted, state.counts)
	info('skipped:', state.skipped)

##
#
#
class State:
	# NOTE: APPENDIX is at same place as section
	ltype_idx = {'LVL0': 0, 'LVL1': 1, 'LVL2': 2, 'LVL3': 3, 'LVL4': 4, 'LVL5': 5, 'LVL6': 6, 'SECTION': 7, 'APPENDIX': 7, 'NOTE': 8, 'HISTORY': 9, 'NOTEP': 8, 'HISTP': 9}

	def __init__(self):
		self.s = [None]*10
		self.counted = 0
		self.counts = {}
		self.skipped = {}

	##
	#
	#
	def event_org(self, line):
		typ, enum, desc, status = line.tokenize()
		# create element
		if line.ltype in {'SECTION'}:
			el = xml.etree.ElementTree.Element('section')
		else:
			el = xml.etree.ElementTree.Element('org')
#			el.attrib['type'] = lts # not for section duh
		# info
		iel = xml.etree.ElementTree.SubElement(el, 'info')
		if typ:
			typel = xml.etree.ElementTree.SubElement(iel, 'type')
			typel.text = typ
		if enum:
			nel = xml.etree.ElementTree.SubElement(iel, 'enum')
			nel.text = enum
		if desc:
			tel = xml.etree.ElementTree.SubElement(iel, 'title')
			tel.text = desc
		# attributes
		if status:
			el.attrib['status'] = status
		if typ == 'title':
			el.attrib['abbrev'] = enum + ' CCR'
		# get parent and attach to it
		# (only title has no parent)
		parent = self.get_parent(line)
		if parent is not None:
			parent.append(el)
		elif line.ltype not in {'LVL0'}:
			warn('do_it:', line.ltype, 'has no parent')
		# update state
		self.upd(line, el)
		# count
		self.count(line)

	##
	#
	#
	def event_nh(self, line):
		# create parent meta tag if necessary
		if line.ltype in {'NOTEP'} and self.s[self.ltype_idx['NOTE']] is None or line.ltype in {'HISTP'} and self.s[self.ltype_idx['HISTORY']] is None:
			# create element
			el = xml.etree.ElementTree.Element('meta')
			# attributes
			if line.ltype in {'NOTEP'}:
				el.attrib['type'] = 'note'
			elif line.ltype in {'HISTP'}:
				el.attrib['type'] = 'history'
			# attach to parent info el
			parent = self.get_parent(line)
			iel = parent.find('info')
			iel.append(el)
			# update state
			self.upd(line, el)
		# create p tag
		el = xml.etree.ElementTree.Element('p')
		# set text
#		el.text = line.html_escape(line.line)
		el.text = xml.sax.saxutils.escape(line.line) 
		# get parent and attach to it
		if line.ltype in {'NOTEP'}:
			self.s[self.ltype_idx['NOTE']].append(el)
		elif line.ltype in {'HISTP'}:
			self.s[self.ltype_idx['HISTORY']].append(el)
		# count
		self.count(line)

	##
	#
	#
	def event_p(self, line):
		# create p tag
		el = xml.etree.ElementTree.Element('p')
		# set text
#		el.text = line.html_escape(line.line)
		el.text = xml.sax.saxutils.escape(line.line)
		# find parent text el, creating if necessary
		parent = self.get_parent(line)
		textel = parent.find('text')
		if textel is None:
			textel = xml.etree.ElementTree.SubElement(parent, 'text')
		# attach to parent
		textel.append(el)
		# count
		self.count(line)

	##
	# Get the lowest non-None element above ltype, or None if its the highest.
	#
	def get_parent(self, line):
		# a NOTE is not a parent of HISTORY
		if line.ltype in {'SECTION PARAGRAPH', 'NOTEP', 'HISTP', 'ANOTEP'}:
			start = 7
		else:
			start = self.ltype_idx[line.ltype] - 1

		for i in range(start, -1, -1):
			if self.s[i] is not None:
				return self.s[i]
		return None

	##
	#
	#
	def upd(self, line, el):
		# update state
		ltn = self.ltype_idx[line.ltype]
		self.s[ltn] = el
		# normalize state
		if line.ltype not in {'NOTEP', 'HISTP'}:
			for i in range(ltn+1, len(self.s)):
				self.s[i] = None

	##
	#
	#
	def toxml(self, fout):
		fout.write('<?xml version="1.0" encoding="UTF-8"?>'.encode())
		for i in range(len(self.s)):
			if self.s[i] is not None:
				xml.etree.ElementTree.ElementTree(self.s[i]).write(fout)
				return
		raise RuntimeError

	##
	#
	#
	def count(self, line):
		self.counted += 1
		if line.ltype not in self.counts:
			self.counts[line.ltype] = 1
		else:
			self.counts[line.ltype] += 1

	##
	#
	#
	def skip(self, line):
		if line.ltype not in self.skipped:
			self.skipped[line.ltype] = 1
		else:
			self.skipped[line.ltype] += 1

##
#
#
class Line:
#	t_all = {'LVL0', 'LVL1', 'LVL2', 'LVL3', 'LVL4', 'LVL5', 'LVL6', 'SECTION', 'APPENDIX', 'SECTION PARAGRAPH', 'NOTEP', 'HISTP', 'ANOTEP'}
	t_org = {'LVL0', 'LVL1', 'LVL2', 'LVL3', 'LVL4', 'LVL5', 'LVL6', 'SECTION', 'APPENDIX'}

	orgre = '(TITLE|Division|Part|Subdivision|Chapter|Subchapter|Article|Subarticle|Appendix)\s+(\d+.*)\.\s*(.*)\s+(\[Repealed\]|\[Renumbered\]|\[Reserved\])*\**'
	orgrens = '(TITLE|Division|Part|Subdivision|Chapter|Subchapter|Article|Subarticle|Appendix)\s+(\d+.*)\.\s*(.*)'
	appre = 'Appendix\s(.+?)\s*(.*)'
	secre = '§(\d+.*?)\.\s(.*?)\.\s*(\[Repealed\]|\[Renumbered\]|\[Reserved\])*'
#	secre = '§(\d+.*?)\.\s(.*)\s*(\[Repealed\]|\[Renumbered\]|\[Reserved\])*'
	secrenp = '§(\d+.*?)\.\s(.*)'

#	html_escape_table = { 
#		'&': '&amp;',
#		'"': '&quot;',
#		"'": '&apos;',
#		'>': '&gt;',
#		'<': '&lt;',
#	}

	def __init__(self, ltype, line):
		self.ltype = ltype
		self.line = line
		#self.lts, self.lnum, self.ltit, self.rep = self.tokenize()

	##
	# 
	#
	def tokenize(self):
		if self.ltype not in self.t_org:
			warn('Line.tokenize: non-org ltype')
			raise RuntimeError

		if self.ltype in {'SECTION'}:
			return self.tokenize_section()
		else:
			return self.tokenize_org()

	def tokenize_org(self):
		# lts is (normalized) organizational type string (it seems the order varies, but the LVL* gives a true heirarchy)
		# lnum is organizational number string
		if re.search('\[|\*', self.line):
			m = re.match(self.orgre, self.line)
		else:
			m = re.match(self.orgrens, self.line)
			if not m:
				m = re.match(self.appre, self.line)
				if not m:
					warn('Line.tokenize_org:', self.ltype, 'did not match appre on', self.line)
					return ('', '', '', None)
				return ('appendix', m.group(1), m.group(2), None)
		if not m:
			warn('Line.tokenize_org:', self.ltype, 'did not match on', self.line)
			return ('', '', '', None)
		groups = m.groups()
#		lts = self.html_escape(groups[0].lower())
		typ = xml.sax.saxutils.escape(groups[0].lower())
#		lnum = self.html_escape(groups[1])
		enum = xml.sax.saxutils.escape(groups[1])
		# ltit is the (normalized) organizational title string
#		ltit = self.html_escape(groups[2].rstrip('.')) # why is the period being included?
		desc = xml.sax.saxutils.escape(groups[2].rstrip('.')) # why is the period being included?
		if len(groups) == 4 and groups[3]:
			status = groups[3].strip('[]*')
		else:
			status = None
		return (typ, enum, desc, status)

	def tokenize_section(self):
		status = None
		m = re.match(self.secre, self.line)
		if m:
			status = m.group(3)
		else:
			warn('Line.tokenize_section:', self.ltype, 'did not match secre on', self.line)
			m = re.match(self.secrenp, self.line)
			if not m:
				warn('Line.tokenize_section:', self.ltype, 'did not match secrenp on', self.line)
				return ('', '', '', None)
#		lnum = self.html_escape(m.group(1))
		lnum = xml.sax.saxutils.escape(m.group(1))
#		ltit = self.html_escape(m.group(2).rstrip('.'))
#		ltit = xml.sax.saxutils.escape(m.group(2).rstrip('.'))
		if m.group(2) is None:
			warn('tokenize_section ltit is None')
		ltit = xml.sax.saxutils.escape(m.group(2)+'.')
		if status:
			status = status.strip('[]*').lower()

		debug('section tokenize', lnum, status, ltit)

		return (None, lnum, ltit, status)

#	def html_escape(self, text):
#		return ''.join(self.html_escape_table.get(c,c) for c in text)

	def __len__(self):
		return len(self.line)

	def __str__(self):
		return self.line

	def __eq__(self, other):
		return self.ltype == other

	def __hash__(self):
		return hash(self.ltype)

##
#
#
class OOFile():
	##
	# Open a file and return its UNO XText.
	#
	def __init__(self, filename):
		# start oo
		cmd = 'soffice --accept="pipe,name=officepipe;urp;StarOffice.ServiceManager" --norestore --nofirstwizard --nologo --headless --nosplash --nolockcheck'
		cmdl = shlex.split(cmd)
		p = subprocess.Popen(cmdl, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, universal_newlines=True)
		p.stdin.close()
		p.stdout.close()

		# sleep
		time.sleep(5)

		# get URL
		url = unohelper.systemPathToFileUrl(os.path.abspath(filename))

		# connect to oo
		local = uno.getComponentContext()
		resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
		context = None
		for i in range(3):
			try:
				context = resolver.resolve("uno:pipe,name=officepipe;urp;StarOffice.ComponentContext")
			except Exception as e:
				warn('failed to connect', i, '/ 3 ... retrying in 5 seconds')
				time.sleep(5)
		if not context:
			fatal('failed to connect!')

		# get ...
		desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
		doc = desktop.loadComponentFromURL(url ,"_blank", 0, ())
	
		# get the com.sun.star.text.Text service
		text = doc.getText()

		self.p = p
		self.desktop = desktop
		self.doc = doc
		self.text = text

	def __iter__(self):
		return self.__para_gen()

	##
	# Iterate over paragraphs in an UNO XText object.
	#
	# This will yield tuples of the style and paragraph.
	#
	# See <http://wiki.services.openoffice.org/wiki/Documentation/DevGuide/Text/Iterating_over_Text>.
	#
	# TODO: encode italics, bold, etc. Even in stuff that will be an attribute?
	#
	def __para_gen(self):
		# call the XEnumerationAccess's only method to access the actual Enumeration
		text_enum = self.text.createEnumeration()
		while text_enum.hasMoreElements():
			# get next enumerated com.sun.star.text.Paragraph
			para = text_enum.nextElement()
			if para.supportsService('com.sun.star.text.Paragraph'):
				st = []
				para_enum = para.createEnumeration()
				while para_enum.hasMoreElements():
					# get the next enumerated com.sun.star.text.TextPortion
					portion = para_enum.nextElement()
					if portion.TextPortionType == 'Text':
						# yield the string and its paragraph style
	#					s = portion.getString().strip()
						s = portion.getString()
						style = None
						if portion.supportsService('com.sun.star.style.ParagraphProperties') and hasattr(portion, 'ParaStyleName'):
								style = portion.ParaStyleName.strip()
						st.append(s)
				yield Line(style, str.join('', st))

#	def __enter__(self):
#		pass

	def __exit__(self):
		self.close()

	def close(self):
		# fucking die
#		del self.text
		self.doc.dispose()
#		del self.doc
		debug('OOFile: calling XDesktop::Terminate()...', end=' ')
		self.desktop.terminate()
#		print('fucking die die die die')
#		self.p.terminate()
		self.p.wait()
		debug('done')

		# fucking die die die you fucking piece of shit
#		cmd2 = 'soffice --unaccept="all"'
#		cmd2l = shlex.split(cmd2)
#		p2 = subprocess.Popen(cmd2l, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, universal_newlines=True)
#		p2.stdin.close()
#		p2.stdout.close()
#		p2.wait()
#
#		print('fucking died now?')

	def __del__(self):
		try:
			self.close()
		except AttributeError:
			pass

##
# Print debugging info.
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

