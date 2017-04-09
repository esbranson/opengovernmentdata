#!/usr/bin/python3 -u

##
# acew2rdf - convert the US BLS Census of Employment and Wages dataset into RDF
#

usage="""
acew2rdf - convert the US BLS Census of Employment and Wages dataset into RDF

See <https://www.bls.gov/cew/>.

Usage:  acew2rdf [options] GOVT_UNITS_*.txt *.annual.singlefile.csv [output]
Arguments:

	-d			enable debugging
	-f fmt		use format for output file (see RDFLib documentation)
	output		output file (default: stdout)
"""

import rdflib
import rdflib.plugins.sleepycat
import getopt
import csv
import tempfile
import sys
import itertools
import logging

bls_cew = rdflib.Namespace("http://data.bls.gov/dataset/cew/")
bls_cew_onto = rdflib.Namespace("http://data.bls.gov/ont/cew#")
usgs_gnis = rdflib.Namespace("http://data.usgs.gov/id/gnis/")
cbsa_code = rdflib.Namespace("http://data.omb.gov/id/cbsa/")
csa_code = rdflib.Namespace("http://data.omb.gov/id/csa/")
naics_ind = rdflib.Namespace("http://data.census.gov/id/naics-industry/")
naics_own = rdflib.Namespace("http://data.cenus.gov/id/naics-ownership/")
qb = rdflib.Namespace("http://purl.org/linked-data/cube#")
sdmx_dimension = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
sdmx_measure = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
sdmx_attribute = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
sdmx_code = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/code#")

# TODO: use rdfs:subPropertyOf
obstype = qb['Observation']
emplvltype = bls_cew_onto['EmplLvlObservation']
#avgwwagetype = bls_cew_onto['avgwwageObservation']
avgapaytype = bls_cew_onto['AvgPayObservation']
#gnisprop = bls_cew_onto['gnis']
areaprop = sdmx_dimension['refArea']
indprop = bls_cew_onto['industry']
ownprop = bls_cew_onto['ownership']
freqprop = sdmx_dimension['freq']
tpprop = sdmx_dimension['timePeriod']
#curprop = sdmx_attribute['currency'] # TODO: put attributes in dataset model
#salprop = sdmx_attribute['freqDetail']
freqvala = sdmx_code['freq-A'] # see <http://sdmx.org/docs/1_0/SDMXCommon.xsd> TimePeriodType
#freqvalw = sdmx_code['freq-W'] # as an attr for weekly salary by quarter
#curval = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217
peopvalprop = bls_cew_onto['people'] # rdfs:subPropertyOf sdmx-measure:obsValue
#obsvalprop = sdmx_measure['obsValue']
curvalprop = sdmx_measure['currency']
dtgy = rdflib.XSD.gYear
dtnni = rdflib.XSD.nonNegativeInteger
#dti = rdflib.XSD.integer

##
# Driver function. Create FIPS-to-GNISID map, then create feature RDF graph,
# then save graph.
#
def main():
	outf = sys.stdout.buffer
	outfmt = 'turtle'
	debuglvl = logging.INFO

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'df:')
	except getopt.GetoptError as e:
		logging.fatal('getopt error {}'.format(e))
		return 1

	if len(args) < 2:
		logging.fatal('need input files')
		return 1
	for opt, arg in opts:
		if opt in {'-d', '--debug'}:
			debuglvl = logging.DEBUG
		elif opt in {'-f', '--format'}:
			outfmt = arg
		else:
			logging.fatal('invalid flag {}'.format(opt))
			return 1

	govfn = args[0] # GOVT_UNITS_*.txt
	codesfn = args[1] # NationalFedCodes_*.txt
	if len(args) >= 3:
		outf = args[2]
	logging.basicConfig(format='{levelname}: {message}', style='{', level=debuglvl)

	logging.info("Building FIPSMap")
	m = FIPSMap()
	with open(govfn) as f:
		convert_fips2gnis(f, m)
	logging.info("Building RDF")

	with open(codesfn) as f, tempfile.TemporaryDirectory() as tmpdn:
		g = rdflib.Graph(rdflib.plugins.sleepycat.Sleepycat(tmpdn))
		g.bind('qb', qb)
		g.bind('sdmx-dimension', sdmx_dimension)
		g.bind('sdmx-measure', sdmx_measure)
		g.bind('sdmx-attribute', sdmx_attribute)
		g.bind('sdmx-code', sdmx_code)
		g.bind('cew', bls_cew)
		g.bind('cew-onto', bls_cew_onto)
		g.bind('gnis', usgs_gnis)
		g.bind('naics-ind', naics_ind)
		g.bind('naics-own', naics_own)
		convert_acew(g, f, m)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# A map (FIPS state numeric, FIPS county numeric) => GNIS ID.
#
class FIPSMap:
	def __init__(self):
		self.m = {}
	def add(self, gnisid, fips_sn, fips_cn=''):
		self.m[(fips_sn, fips_cn)] = gnisid
	def get(self, fips_sn, fips_cn=''):
		return (fips_sn, fips_cn) in self.m and self.m[(fips_sn, fips_cn)] or None

##
# Use BGN "Government Units" file to pre-build map of state/county
# FIPS codes -> GNIS IDs.
#
# @input f: The BGN "Government Units" file.
# @input m: A FIPSMap.
#
def convert_fips2gnis(f, m):
	csv_reader = csv.reader(f, delimiter='|')
	next(csv_reader)
	for row in csv_reader:
		m.add(row[0], row[4], row[2])

##
# Given the CEW area code, return the GNIS ID and a URL fragment, 
# or (None,None) if we're to skip.
#
# See <https://data.bls.gov/cew/doc/titles/area/area_titles.htm>.
#
# TODO: Don't skip U series.
#
def convert_area2gnis(fips_code, m):
	# XXX error check None return
	if fips_code[0] == 'U':
		area = None
		aid = None
	elif fips_code[0:2] == 'CS':
		area = csa_code[fips_code[2:5]]
		aid = 'csa'+fips_code[2:5]
	elif fips_code[0] == 'C':
		area = cbsa_code[fips_code[1:5]+'0']
		aid = 'cbsa'+fips_code[1:5]+'0'
	elif fips_code[2:5] in {'000','999'}:
		aid = m.get(fips_code[0:2])
		area = usgs_gnis[aid]
		if fips_code[2:5] in {'999'}: # XXX not located within county?
			aid+='u'
			#continue # XXX what is an areaRef for this?
	else:
		aid = m.get(fips_code[0:2], fips_code[2:5])
		if aid is None:
			logging.warning("({0},{1}) is no state,county".format(fips_code[0:2], fips_code[2:5]))
			area = None
		else:
			area = usgs_gnis[aid]
	return area,aid

##
#
#
def convert_acew(g, f, m):
	csv_reader = csv.reader(f, doublequote=False)
	next(csv_reader)

	for n,row in enumerate(csv_reader, 1):
		# XXX strip quotes
		fips_code = row[0]
		owner_code = row[1]
		industry_code = row[2]
		#agglvl_code = row[3]
		#size_code = row[4]
		year = row[5]
		qtr = row[6]
		disclosure_code = row[7]
		#annual_avg_estabs_count = row[8]
		annual_avg_emplvl = row[9]
		#total_annual_wages = row[10]
		#taxable_annual_wages = row[11]
		#annual_contributions = row[12]
		#annual_avg_wkly_wage = row[13]
		avg_annual_pay = row[14]

		assert qtr == 'A'
		if disclosure_code == 'N':
			continue
		if owner_code not in ('0','5'):
			continue
		#if industry_code[:2] != '10' and len(industry_code) > 2 and '-' not in industry_code:
		#	continue

		area,aid = convert_area2gnis(fips_code, m)
		if area is None or aid is None:
			continue

		url = bls_cew['_'.join(['emplvl',aid,industry_code,owner_code,year])]
		g.add((url, rdflib.RDF.type, obstype))
		g.add((url, rdflib.RDF.type, emplvltype))
		g.add((url, areaprop, area))
		g.add((url, indprop, naics_ind[industry_code]))
		g.add((url, ownprop, naics_own[owner_code]))
		g.add((url, freqprop, freqvala))
		g.add((url, tpprop, rdflib.Literal(year, datatype=dtgy)))
		g.add((url, peopvalprop, rdflib.Literal(annual_avg_emplvl, datatype=dtnni)))

		url = bls_cew['_'.join(['avgapay',aid,industry_code,owner_code,year])]
		g.add((url, rdflib.RDF.type, obstype))
		g.add((url, rdflib.RDF.type, avgapaytype))
		g.add((url, areaprop, area))
		g.add((url, indprop, naics_ind[industry_code]))
		g.add((url, ownprop, naics_own[owner_code]))
		g.add((url, freqprop, freqvala))
		g.add((url, tpprop, rdflib.Literal(year, datatype=dtgy)))
		g.add((url, curvalprop, rdflib.Literal(avg_annual_pay, datatype=dtnni)))

		if n % 1000 == 0:
			logging.debug("Processed {0}".format(n))

if __name__ == '__main__':
	main()

