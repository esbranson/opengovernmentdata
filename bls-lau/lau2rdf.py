#!/usr/bin/python3 -u

usage="""lau2rdf - convert US BLS Local Area Unemployment Statistics data into RDF

See <https://www.bls.gov/lau/>. Requires python3, python3-rdfllib and 
python3-bsddb3.

Usage:  lau2rdf [options] la.data.* la.area laucnty##.txt GOVT_UNITS_*.txt NationalFedCodes_*.txt

	-o output	output file (default: stdout)
	-d			enable debugging
	-f fmt		use format for output file (default: turtle)
"""

import rdflib
import csv
import tempfile
import sys
import logging
import getopt
import re
import collections

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geonames'))
from geonames2rdf import FIPS2GNISDict
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from stats import StatsGraph

##
# Commandline driver function.
#
def main():
	outf = sys.stdout.buffer
	outfmt = 'turtle'
	debuglvl = logging.INFO

	logging.basicConfig(format='{levelname}/{funcName}/l{lineno} {message}', style='{', level=debuglvl)

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ho:df:')
	except getopt.GetoptError as e:
		logging.fatal('Getopt error {}'.format(e))
		return 1

	for opt, arg in opts:
		if opt in {'-o', '--output'}:
			outf = arg
		elif opt in {'-d', '--debug'}:
			debuglvl = logging.DEBUG
		elif opt in {'-f', '--format'}:
			# XXX verify, otherwise die and inform of valid input
			outfmt = arg
		elif opt in {'-h', '--help'}:
			print(usage, file=sys.stderr)
			return 0
		else:
			logging.fatal('Invalid flag {}'.format(opt))
			print(usage, file=sys.stderr)
			return 1
	if len(args) < 5:
		logging.fatal('Need input files')
		print(usage, file=sys.stderr)
		return 1

	logging.getLogger().setLevel(debuglvl)
	datafn = args[0]
	areafn = args[1]
	laucntyfn = args[2]
	govunitsfn = args[3]
	natfedfn = args[4]

	logging.info("Creating AreaMap")
	with open(areafn) as areaf, open(laucntyfn) as laucntyf, open(govunitsfn) as govunitsf, open(natfedfn) as natfedf:
		aream = AreaMap(areaf, laucntyf, govunitsf, natfedf)

	logging.info("Building RDF")
	g = LAUGraph()
	with open(datafn) as f:
		g.parse_data(f, aream)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# A map of city names => GNIS ID.
#
# TODO Currently only works for counties and most cities and towns.
#
class NameMap:
	##
	# Use BGN NationalFedCodes file to pre-build map of state/county
	# FIPS codes -> GNIS IDs etc.
	#
	# @input f: The BGN NationalFedCodes file.
	#
	def __init__(self, f):
		self.l = []
		csv_reader = csv.reader(f, delimiter='|')
		next(csv_reader)
		for row in csv_reader:
			gnis = row[0]
			name = row[1]
			census_class = row[4]
			state_fips = row[7]
			county_fips = row[10]
			county = row[11]
			self.l.append((gnis,name,census_class,state_fips,county_fips,county))

	##
	# Find city and return its GNIS ID.
	#
	# @input name: An un-normalized name from the <la.area> file.
	# @input ac: An area code from the <la.area> file.
	# @output: GNIS ID or None
	#
	def map_city2gnis(self, name, ac):
		name,county = NameMap.normalize_name(name)
		fips_s = ac[2:4]

		# Search for exact match.
		for item in self.l:
			if item[1] == name and item[3] == fips_s:
				return item[0]

		# Collect regular expression matches.
		matches = []
		for item in self.l:
			# If re matches, they're in our state, and have the right Census class.
			if re.search(name, item[1]) and item[3] == fips_s and item[2][0] in {'C','T','Z'}: # Townships, whatever Zs are
				matches.append(item)

		# Return None if no matches.
		if len(matches) == 0:
			logging.debug("No match for {} \"{}\"".format(ac, name))
			return None

		# Return the single match.
		if len(matches) == 1:
			return matches[0][0]

		# Return the single match in the given county.
		if county:
			items = list(filter(lambda item: item[5] == county, matches))
			if len(items) == 1:
				return items[0][0]

		# Otherwise pick the shortest name.
		shortest = sorted(matches, key=lambda l: len(l[1]))
		logging.debug("Short matching {} \"{}\" to {} \"{}\"".format(ac, name, shortest[0], shortest[1]))
		return shortest[0]

	##
	# Return a normalized name (for the NationalFedCodes file), along
	# with a county (as a tuple) if needed.
	#
	# @input name: An un-normalized name from the <la.area> file.
	# @output: A tuple (name,county) where county may be None.
	#
	@staticmethod
	def normalize_name(name):
		# Replacements.
		name = name.replace('St.', 'Saint')

		# Matching.
		res = name.split(' city, ')
		if len(res) > 1:
			return 'City of '+res[0], None

		res = name.split(' town, ')
		if len(res) > 1:
			return 'Town of '+res[0], None

		res = name.split(' town (')
		if len(res) > 1:
			county = res[1].split(' County), ')[0]
			return 'Town of '+res[0], county

		res = name.split(' village, ')
		if len(res) > 1:
			return 'Village of '+res[0], None

		res = name.split(' charter township, ')
		if len(res) > 1:
			return 'Charter Township of '+res[0], None

		res = name.split(' charter township (')
		if len(res) > 1:
			county = res[1].split(' County), ')[0]
			return 'Charter Township of '+res[0], county

		res = name.split(' township, ')
		if len(res) > 1:
			return 'Township of '+res[0], None

		res = name.split(' township (')
		if len(res) > 1:
			county = res[1].split(' County), ')[0]
			return 'Township of '+res[0], county

		res = name.split(' borough, ')
		if len(res) > 1:
			return 'Borough of '+res[0], None

		res = name.split(' municipality, ')
		if len(res) > 1:
			return 'Municipality of '+res[0], None

		res = name.split(' plantation, ')
		if len(res) > 1:
			return 'Plantation of '+res[0], None

		res = name.split(' unorganized, ')
		if len(res) > 1:
			return 'Unorganized Territory of '+res[0], None

		res = name.split(' gore, ')
		if len(res) > 1:
			return res[0]+' Gore', None

		res = name.split(' grant, ')
		if len(res) > 1:
			return res[0]+' Grant', None

		res = name.split(' location, ')
		if len(res) > 1:
			return res[0]+' Location', None

		# XXX What if above tests fail? What's left?
		return name, None

##
# A map of LAU area code => linked data ID URL.
#
# Use like a dictionary, as collections.UserDict manages the access
# methods such as __getitem__. We only populate the internal dictionary.
#
# TODO Currently only returns GNIS ID URLs.
#
class AreaMap(collections.UserDict):
	##
	# @input areaf: <https://download.bls.gov/pub/time.series/la/la.area>.
	# @input laucntyf: The LAU yearly county data file.
	# @input govunitsf: The BGN "Government Units" file.
	# @input natfedf: The BGN NationalFedCodes file.
	#
	def __init__(self, areaf, laucntyf, govunitsf, natfedf):
		super().__init__()

		logging.info("Building FIPSMap")
		fipsm = FIPS2GNISDict(govunitsf)

		logging.info("Building NameMap")
		namem = NameMap(natfedf)

		logging.info("Building map area => county GNIS")
		self.convert_county2gnis(laucntyf, fipsm)

		logging.info("Building map area => city GNIS")
		self.convert_city2gnis(areaf, namem)

	##
	# Get LAU area => county GNIS mappings.
	#
	# @input f: <https://www.bls.gov/lau/laucnty16.txt>
	# @input m: A FIPS2GNISDict.
	#
	def convert_county2gnis(self, f, m):
		#csv_reader = csv.reader(f, delimiter='|')
		for i in range(6):
			next(f) # skip headers

		for line in f:
			if not line.strip():
				break
			area = line[0:15]
			fips_s = line[18:20]
			fips_c = line[25:28]
			gnis = m[(fips_s, fips_c)] # TODO exceptions?
			if gnis is None:
				logging.warning("No GNIS for area {}".format(area))
			else:
				self[area] = StatsGraph.id_gnis[gnis]

	##
	# @input f: <https://download.bls.gov/pub/time.series/la/la.area>.
	# @input m: A NameMap.
	#
	def convert_city2gnis(self, f, m):
		csv_reader = csv.reader(f, delimiter='\t')
		next(csv_reader) # skip header

		for row in csv_reader:
			type = row[0] # see la.area_type
			area = row[1]
			if area in self.data:
				continue
			elif type in {'F', 'G', 'H'}: # XXX Should this include 'F' (counties)?
				name = row[2]
				gnis = m.map_city2gnis(name, area)
				if gnis is not None:
					self[area] = StatsGraph.id_gnis[gnis]

##
# Represent a LAU graph.
#
class LAUGraph(StatsGraph):
	ont_lau = rdflib.Namespace("http://data.bls.gov/ont/lau#")
	lau_tunempl = ont_lau['TotalUnemploymentObservation'] # rdfs:subClassOf qb:Observation
	lau_templ = ont_lau['TotalEmploymentObservation']
	lau_tlf = ont_lau['TotalLaborForceObservation']
	lau_runempl = ont_lau['RatioUnemploymentToLaborForceObservation']
#	lau_rempl = ont_lau['RatioEmploymentToLaborForceObservation']
#	lau_sid = ont_lau['sid']
	lau_area = ont_lau['area']
	lau_gnis = ont_lau['gnis']
#	lau_ind = ont_lau['indicator']
#	lau_adj = ont_lau['processing']
	lau_seas = ont_lau['seasonal']
	lau_rate = ont_lau['percent']
	lau_count = ont_lau['people'] # rdfs:subPropertyOf sdmx-measure:obsValue

	##
	#
	#
	def __init__(self):
		super().__init__()
		self.g.bind('lau', self.id_lau)
		self.g.bind('lau-ont', self.ont_lau)

	##
	# @input f: An <la.data.*> file.
	# @input m: An AreaMap object.
	#
	def parse_data(self, f, m):
		csv_reader = csv.reader(f, delimiter='\t')
		next(csv_reader)

		for n,row in enumerate(csv_reader, 1):
			if n % 10000 == 0:
				logging.debug("Processing {0}".format(n))

			sid = row[0].strip() #series_id
			year = row[1].strip()
			period = row[2].strip()
			value = row[3].strip()
	#		survey = sid[0:2]
			seas = sid[2] # S=Seasonally Adjusted U=Unadjusted
			ac = sid[3:18] # area_code
			meas = sid[18:20] # measure_code

			# XXX skip rest for now
			if ac not in m:
				continue

			# XXX not available. footcode 'N'
			if value == '-':
				continue

			# date
			if period == 'M13':
				date = rdflib.Literal(year, datatype=rdflib.XSD.gYear)
				freqval = StatsGraph.sdmx_freqa
			else:
				date = rdflib.Literal(year+'-'+period.lstrip('M'), datatype=rdflib.XSD.gYearMonth)
				freqval = StatsGraph.sdmx_freqm

			# type
			if meas == '03':
				typ = 'runempl'
				valtyp = self.lau_rate
				obstypval = self.lau_runempl
				dt = rdflib.XSD.decimal
			elif meas == '04':
				typ = 'tunempl'
				valtyp = self.lau_count
				obstypval = self.lau_tunempl
				dt = rdflib.XSD.nonNegativeInteger
			elif meas == '05':
				typ = 'templ'
				valtyp = self.lau_count
				obstypval = self.lau_templ
				dt = rdflib.XSD.nonNegativeInteger
			elif meas == '06':
				typ = 'tlf'
				valtyp = self.lau_count
				obstypval = self.lau_tlf
				dt = rdflib.XSD.nonNegativeInteger
			else:
				logging.warning('Unknown meas')
				valtyp = self.sdmx_obs
				indval = rdflib.Literal(value)

			# build URI
			url = self.id_lau['_'.join([typ,sid,year,period])]

			# add data
			self.g.add((url, rdflib.RDF.type, obstypval))
	#		self.g.add((url, self.lau_area, rdflib.Literal(ac, datatype=rdflib.XSD.string)))
			self.g.add((url, self.sdmx_freq, freqval))
			self.g.add((url, self.sdmx_time, date))
			self.g.add((url, valtyp, rdflib.Literal(value, datatype=dt)))

			# get GNIS from area code
			if ac in m:
				gnis = m[ac]
				self.g.add((url, self.lau_gnis, gnis))

			# seasonality
			if seas == 'S':
				self.g.add((url, self.sdmx_adj, self.lau_seas))

if __name__ == '__main__':
	main()

