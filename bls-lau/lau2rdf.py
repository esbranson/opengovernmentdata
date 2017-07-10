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
from geonames2rdf import FIPSMap
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
#			clas = row[2] # 'Civil'
#			census_code = row[3] # '99' + county FIPS if county
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
	#
	# TODO Test city name with county FIPS instead of state?
	#
	def get(self, name, ac):
		name,county = NameMap.normalize_name(name)
		fips_s = ac[2:4]
		allmatches = []
		# find all with that name inside
		for item in self.l:
			if name == item[1] and item[3] == fips_s: # XXX Not in original code; does this work?
				return item[0]
			if re.search(name, item[1]) and item[3] == fips_s:
				allmatches.append(item)
		# see if there is only 1 incorporated city
		citymatches = []
		for m in allmatches:
	#		if m[2][0] == 'P' or m[2][0] == 'C': #Census Class Codes for cities
			if m[2][0] in {'C','T','Z'}: # Townships, whatever Zs are
				citymatches.append(m)
		if len(citymatches) == 1:
			logging.debug('city {} {} {}'.format(ac, name, citymatches[0][0]))
			return citymatches[0][0]
		elif len(citymatches) > 1:
			# county?
			if county:
				# XXX whatif multiple matches?
				for item in citymatches:
					if item[5] == county:
						return item[0]
			# XXX pick shortest name?
			shortest = citymatches[0]
			same = True
			last = citymatches[0][0]
			for m in citymatches[1:]:
				if len(m[1]) < len(shortest[1]):
					shortest = m
	#			elif len(m[1]) == len(shortest[1]):
	#				logging.debug('city wtf samelen {} {}'.format(shortest, m))
				if same and m[0] == last: # if theyre all same gnis
					same = True
				else:
					same = False
				last = m[0]
			if not same:
				logging.warning('city outof {} {} {} {} {}'.format(ac, name, citymatches, 'pick', shortest))
			return shortest[0]
	#	if '(' in name:
	#		alt = name.split('(')[0].strip()
	#		logging.debug('city alt {} {}'.format(name, alt))
	##		return search_codes_city(gnlist, alt, fips_s, ac)
	#		return search_fips2gnis_city(gnlist, alt, county, fips_s, ac)
		return None

	##
	# Return a normalized (for the NationalFedCodes file) name, along
	# with a county (as a tuple) if needed.
	#
	@staticmethod
	def normalize_name(name):
		# XXX replacements
		name = name.replace('St.', 'Saint')

		# matching
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
# XXX Currently only works for counties and most cities and towns.
# XXX Currently only returns GNIS ID URLs.
# TODO Use the dict interface.
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
		fipsm = FIPSMap(govunitsf)

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
	# @input m: A FIPSMap.
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
			gnis = m.get(fips_s, fips_c) # TODO exceptions?
			if gnis is None:
				logging.warning("No GNIS for area {}".format(area))
			self[area] = gnis

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
				gnis = m.get(name, area)
				if gnis is None:
					logging.debug("No GNIS for area {}".format(area))
				else:
					self.data[area] = gnis

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
	#
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
	#		fn = row[4].strip() # footnote_codes

	#		survey = sid[0:2]
			seas = sid[2] # S=Seasonally Adjusted U=Unadjusted
			ac = sid[3:18] # area_code
			meas = sid[18:20] # measure_code
#			if len(sid) > 13: # XXX what is this????
#				ex = sid[13:]
#			else:
#				ex = ''

			# XXX skip rest for now
			if ac not in m:
				continue

			# XXX not available. footcode 'N'
			if value == '-':
				continue

#			# XXX duplicates? XXX what is this????
#			if len(ex):
#				continue

			ac_typ = ac[0:2]
			ac_fips = ac[2:4]
	#		ac_rest = ac[2:8]

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

			# get FIPS from LAUS area code
			if ac in m:
				gnis = m[ac]
				self.g.add((url, self.lau_gnis, self.id_gnis[gnis]))

			# seasonality
			if seas == 'S':
				self.g.add((url, self.sdmx_adj, self.lau_seas))
			elif seas == 'U':
				pass
			else:
				logging.warning('Unknown adjustment')

if __name__ == '__main__':
	main()

