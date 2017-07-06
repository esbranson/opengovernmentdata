#!/usr/bin/python3 -u

##
# oes2rdf - convert the US BLS Occupational Employment Statistics dataset into RDF
#

usage="""
oes2rdf - convert the US BLS Occupational Employment Statistics dataset into RDF

Requires python3-rdfllib and python3-bsddb3. See <https://www.bls.gov/oes/>.

Usage:  oes2rdf [options] oe.data.* oe.industry GOVT_UNITS_*.txt
Arguments:

	-o output	output file (default: stdout)
	-d			enable debugging
	-f fmt		use format for output file (see RDFLib documentation)	
"""

import rdflib
import rdflib.plugins.sleepycat
import getopt
import csv
import tempfile
import sys
import itertools
import logging

oes = rdflib.Namespace("http://data.bls.gov/dataset/oes/")
oes_onto = rdflib.Namespace("http://data.bls.gov/ont/oes#")
gnis = rdflib.Namespace("http://data.usgs.gov/id/gnis/")
soc = rdflib.Namespace("http://data.omb.gov/id/soc/")
cbsa = rdflib.Namespace("http://data.omb.gov/id/cbsa/")
#csa = rdflib.Namespace("http://data.omb.gov/id/csa/")
naics_ind = rdflib.Namespace("http://data.census.gov/id/naics-industry/")
naics_own = rdflib.Namespace("http://data.cenus.gov/id/naics-ownership/")
qb = rdflib.Namespace("http://purl.org/linked-data/cube#")
sdmx_dimension = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
sdmx_measure = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
sdmx_attribute = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
sdmx_code = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/code#")

# TODO: use rdfs:subPropertyOf
obstype = qb['Observation']
emptype = oes_onto['EmplObservation']
empsemtype = oes_onto['EmplSEMObservation']
wagemeanatype = oes_onto['WageMeanAnnualObservation']
wagemedatype = oes_onto['WageMedianAnnualObservation']
wagsemtype = oes_onto['WageSEMObservation']
areaprop = sdmx_dimension['refArea']
indprop = oes_onto['industry']
ownprop = oes_onto['ownership']
socprop = oes_onto['occupation']
freqprop = sdmx_dimension['freq']
tpprop = sdmx_dimension['timePeriod']
freqvala = sdmx_code['freq-A'] # see <http://sdmx.org/docs/1_0/SDMXCommon.xsd> TimePeriodType
#curval = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217
peopvalprop = oes_onto['people'] # rdfs:subPropertyOf sdmx-measure:obsValue
percvalprop = oes_onto['percentRelStdErr'] # rdfs:subPropertyOf sdmx-measure:obsValue
#obsvalprop = sdmx_measure['obsValue']
curvalprop = sdmx_measure['currency']
dtgy = rdflib.XSD.gYear
dtnni = rdflib.XSD.nonNegativeInteger
dtd = rdflib.XSD.decimal

##
# Driver function. Create FIPS-to-GNISID map, then create RDF data cube graph,
# then save graph.
#
def main():
	outf = sys.stdout.buffer
	outfmt = 'turtle'
	debuglvl = logging.INFO

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'o:df:')
	except getopt.GetoptError as e:
		logging.fatal('getopt error {}'.format(e))
		return 1

	if len(args) < 3:
		logging.fatal('need input files')
		return 1
	for opt, arg in opts:
		if opt in {'-o', '--output'}:
			outf = arg
		elif opt in {'-d', '--debug'}:
			debuglvl = logging.DEBUG
		elif opt in {'-f', '--format'}:
			outfmt = arg
		else:
			logging.fatal('invalid flag {}'.format(opt))
			return 1

	datafn = args[0] # oe.data.0.Current
	indfn = args[1] # oe.industry
	govfn = args[2] # GOVT_UNITS_*.txt
	logging.basicConfig(format='{levelname} {process}/{thread}/{funcName} {message}', style='{', level=debuglvl)

	logging.info("Building FIPSMap")
	with open(govfn) as f:
		gnism = FIPSMap(f)

	logging.info("Building IndustryMap")
	with open(indfn) as f:
		indm = IndustryMap(f)

	logging.info("Building RDF")
	g = OESGraph()
	with open(datafn) as f:
		g.build(f, gnism, indm)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# A map (FIPS state numeric, FIPS county numeric) => GNIS ID.
#
class FIPSMap:
	##
	# Use BGN "Government Units" file to pre-build map of state/county
	# FIPS codes -> GNIS IDs.
	#
	# @input f: The BGN "Government Units" file.
	#
	def __init__(self, f):
		self.m = {}
		csv_reader = csv.reader(f, delimiter='|')
		next(csv_reader)
		for row in csv_reader:
			self.add(row[0], row[4], row[2])
	def add(self, gnisid, fips_sn, fips_cn=''):
		self.m[(fips_sn, fips_cn)] = gnisid
	def get(self, fips_sn, fips_cn=''):
		return (fips_sn, fips_cn) in self.m and self.m[(fips_sn, fips_cn)] or None

##
# A map (FIPS state numeric, FIPS county numeric) => GNIS ID.
#
class IndustryMap:
	##
	# Use oe.industry file to pre-build map of industry codes to -> NAICS codes.
	#
	# TODO: Deal with the national level with ownership codes.
	#
	# @input f: The oe.industry file.
	#
	def __init__(self, f):
		self.m = {}
		csv_reader = csv.reader(f, delimiter='\t', skipinitialspace=True)
		next(csv_reader)
		for row in csv_reader:
			code = row[0].strip()
			lvl = int(row[2].strip())
			if code == '000000':
				ind = '0'
				own = '0'
			elif code == '000001':
				ind = '0'
				own = '5'
			elif '-' in code:
				ind = code[0:2]
				if ind == '31':
					ind = '31-33'
				elif ind == '44':
					ind = '44-45'
				elif ind == '48':
					ind = '48-49'
				own = '0'
			else:
				ind = code[0:lvl]
				own = '0'
			self.add((ind,own), code)
	def add(self, naics, code):
		self.m[code] = naics
	def get(self, code):
		return code in self.m and self.m[code] or None

##
#
#
class OESGraph:
	##
	#
	#
	def __init__(self):
		with tempfile.TemporaryDirectory() as tmpdn:
			g = rdflib.Graph(rdflib.plugins.sleepycat.Sleepycat(tmpdn))
		self.g = g
		g.bind('oes', oes)
		g.bind('oes-ont', oes_onto)
		g.bind('gnis', gnis)
		g.bind('cbsa', cbsa)
		g.bind('naics-ind', naics_ind)
		g.bind('naics-own', naics_own)
		g.bind('soc', soc)
		g.bind('qb', qb)
		g.bind('sdmx-dimension', sdmx_dimension)
		g.bind('sdmx-measure', sdmx_measure)
		g.bind('sdmx-attribute', sdmx_attribute)
		g.bind('sdmx-code', sdmx_code)
	##
	#
	#
	@staticmethod
	def parse_industry(s, m):
		ret = m.get(s)
		if ret is None:
			return None,None
		ind,own = ret
		return naics_ind[ind], naics_own[own]

	##
	# Return SOC url.
	#
	@staticmethod
	def parse_occupation(s):
		frag = s[0:2] + '-' + s[2:6]
		return soc[frag]

	##
	# Parse the series_id field. Return None if we should skip record.
	#
	# TODO: don't skip nonmetropolitan areas
	#
	@staticmethod
	def parse_series(s, gnism, indm):
		survey = s[0:2]
		seasonal = s[2:3]
		areatye = s[3:4]
		area = s[4:11]
		industry = s[11:17]
		occupation = s[17:23]
		datatype = s[23:25]

		assert survey == 'OE'
		if datatype not in {'01','02', '04', '05', '13'}:
			#logging.debug("skipping record: datatype {0}".format(datatype))
			return (None,)*5

		if area == '0000000':
			areaurl = gnis['1890467']
		elif area[0:2] != '00' and area[2:7] == '00000':
			ret = gnism.get(area[0:2])
			if ret is None:
				logging.critical("FIPSMap returned None for state {0}".format(area[0:2]))
				ret = '-1'
			areaurl = gnis[ret]
		elif area[0:2] != '00' and area[2:7] != '00000':
			#logging.debug("skipping record: nonmetro area {0}".format(area))
			return (None,)*5
		else:
			areaurl = cbsa[area[2:7]]

		(indurl,ownurl) = OESGraph.parse_industry(industry, indm)
		if indurl is None:
			#logging.debug("skipping record: industry_code {0}".format(industry))
			return (None,)*5

		socurl = OESGraph.parse_occupation(occupation)
		if socurl is None:
			logging.warning("skipping record: occupation_code {0}".format(occupation))
			return (None,)*5

		return areaurl,indurl,ownurl,socurl,datatype

	##
	# TODO: use NAICS ownership code
	#
	def build(self, f, gnism, indm):
		g = self.g
		csv_reader = csv.reader(f, delimiter='\t', skipinitialspace=True)
		next(csv_reader)

		for n,row in enumerate(csv_reader, 1):
			if n % 10000 == 0:
				logging.debug("Processing {0}".format(n))

			series = row[0].strip()
			year = row[1].strip()
			period = row[2].strip()
			value = row[3].strip()
			footnotes = row[4].strip()

			assert period == 'A01'

			areaurl,indurl,ownurl,socurl,datatype = OESGraph.parse_series(series, gnism, indm)
			if datatype is None:
				continue

			url = oes['_'.join([series,year,period])]
			g.add((url, rdflib.RDF.type, obstype))
			g.add((url, areaprop, areaurl))
			g.add((url, indprop, indurl))
			g.add((url, ownprop, ownurl))
			g.add((url, socprop, socurl))
			g.add((url, freqprop, freqvala))
			g.add((url, tpprop, rdflib.Literal(year, datatype=dtgy)))
			if datatype == '01':
				g.add((url, rdflib.RDF.type, emptype))
				g.add((url, peopvalprop, rdflib.Literal(value, datatype=dtnni)))
			elif datatype == '02':
				g.add((url, rdflib.RDF.type, empsemtype))
				g.add((url, percvalprop, rdflib.Literal(value, datatype=dtd)))
			elif datatype == '04':
				g.add((url, rdflib.RDF.type, wagemeanatype))
				g.add((url, curvalprop, rdflib.Literal(value, datatype=dtnni)))
			elif datatype == '05':
				g.add((url, rdflib.RDF.type, wagsemtype))
				g.add((url, percvalprop, rdflib.Literal(value, datatype=dtd)))
			elif datatype == '13':
				g.add((url, rdflib.RDF.type, wagemedatype))
				g.add((url, curvalprop, rdflib.Literal(value, datatype=dtnni)))

	##
	#
	#
	def serialize(self, *args, **kwargs):
		self.g.serialize(*args, **kwargs)

if __name__ == '__main__':
	main()

