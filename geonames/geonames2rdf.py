#!/usr/bin/python3 -u

##
# geonames2rdf - convert the US BGN "federal codes" dataset into RDF
#

usage="""
geonames2rdf - convert the US BGN "federal codes" dataset into RDF

See <http://geonames.usgs.gov/domestic/download_data.htm> under "Topical
Gazetteers/Government Units" and "State Files with Federal Codes".

Usage:  geonames2rdf [options] GOVT_UNITS_*.txt NationalFedCodes_*.txt [output]
Arguments:

	-d			enable debugging
	-f fmt		use format for output file (see RDFLib documentation)
	output		output file (default: stdout)
"""

import csv
import rdflib
import sys
import getopt
import logging
import collections

gnis_ns = rdflib.Namespace("http://data.usgs.gov/id/gnis/")
gnisonto_ns = rdflib.Namespace('http://data.usgs.gov/ont/gnis#')
geo_ns = rdflib.Namespace('http://www.opengis.net/ont/geosparql#')

geofeat = geo_ns['Feature']
geohasgeom = geo_ns['hasGeometry']
geogeom = geo_ns['Geometry']
geoaswkt = geo_ns['asWKT']
geowkt = geo_ns['wktLiteral']
geowithin = geo_ns['sfWithin']
gnisfeat = gnisonto_ns['Feature']
gnisname = gnisonto_ns['featureName']
gnisfid = gnisonto_ns['featureID']
gniscls = gnisonto_ns['featureClass']
gnisfips55plc = gnisonto_ns['censusPlace']
gnisfips55cls = gnisonto_ns['censusClass']
gnisfips5_2n = gnisonto_ns['stateNumeric']
gnisfips5_2a = gnisonto_ns['stateAlpha']
gnisfips6_4 = gnisonto_ns['countyNumeric']
gnisgsa = gnisonto_ns['gsaLocation']
gnisopm = gnisonto_ns['opmLocation']

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

	logging.info("Building FIPS2GNISDict")
	with open(govfn) as f:
		m = FIPS2GNISDict(f)

	logging.info("Creating graph")
	g = rdflib.Graph()
	g.bind('gnis-ont', gnisonto_ns)
	g.bind('geo', geo_ns)

	logging.info("Adding states to graph")
	with open(govfn) as f:
		convert_fips2gnis(g, f)

	logging.info("Building RDF")
	with open(codesfn) as f:
		convert_fedcodes(g, f, m)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# A map from (FIPS state numeric, FIPS county numeric) => GNIS ID. The BGN
# Geographic Names Information System ID is the official geographic name
# identifier and is a better identifier than FIPS 5-2 codes for states and
# FIPS 6-4 codes for counties.
#
# TODO Add states.
#
class FIPS2GNISDict(collections.UserDict):
	##
	# Use BGN "Government Units" file to pre-build map of state/county
	# FIPS codes -> GNIS IDs.
	#
	# @input f: The BGN "Government Units" file.
	#
	def __init__(self, f):
		super().__init__()
		csv_reader = csv.reader(f, delimiter='|')
		next(csv_reader)
		for row in csv_reader:
			state = row[4]
			county = row[2]
			gnis = row[0]
			if county == '':
				county = None
			self[(state, county)] = gnis

	##
	# Use like a dictionary, where the key is a tuple (FIPS state, FIPS county),
	# and where the FIPS county may be None if for a state.
	#
	def __getitem__(self, key):
		if not (isinstance(key, tuple) and len(key) is 2 and isinstance(key[0], str) and (key[1] is None or isinstance(key[1], str))):
			raise KeyError(key)
		return super().__getitem__(key)

##
# Use BGN "Government Units" file to add states to graph because they aren't included
# in the NationalFedCodes_*.txt file.
#
# @input g: The Graph.
# @input f: The BGN "Government Units" file.
#
def convert_fips2gnis(g, f):
	csv_reader = csv.reader(f, delimiter='|')
	next(csv_reader)
	for row in csv_reader:
		if row[1] == 'STATE':
			url = gnis_ns[row[0]]
			g.add((url, rdflib.RDF.type, gnisfeat))
			g.add((url, rdflib.RDF.type, geofeat))
			g.add((url, gnisfid, rdflib.Literal(row[0], datatype=rdflib.XSD.string)))
			g.add((url, rdflib.RDFS.label, rdflib.Literal(row[6]))) # XXX: In English?
			g.add((url, gnisname, rdflib.Literal(row[9], datatype=rdflib.XSD.string)))
			g.add((url, gnisfips5_2n, rdflib.Literal(row[4], datatype=rdflib.XSD.string)))
			g.add((url, gnisfips5_2a, rdflib.Literal(row[5], datatype=rdflib.XSD.string)))

##
# Convert BGN "State Files with Federal Codes" file to RDF.
#
# @input g: An RDFLib Graph.
# @input f: The BGN "Government Units" file.
# @input m: A FIPS2GNISDict.
#
def convert_fedcodes(g, f, m):
	csv_reader = csv.reader(f, delimiter='|')
	next(csv_reader)

	for n,row in enumerate(csv_reader, 1):
		if row[2] not in {'Civil', 'Census', 'Populated Place'}:
			continue

		url = gnis_ns[row[0]]
		g.add((url, rdflib.RDF.type, gnisfeat))
		g.add((url, rdflib.RDF.type, geofeat))
		g.add((url, gnisfid, rdflib.Literal(row[0], datatype=rdflib.XSD.string)))
		g.add((url, rdflib.RDFS.label, rdflib.Literal(row[1]))) # XXX: In English?
		g.add((url, gnisname, rdflib.Literal(row[1], datatype=rdflib.XSD.string)))
		g.add((url, gniscls, rdflib.Literal(row[2], datatype=rdflib.XSD.string)))

		if len(row[3]):
			g.add((url, gnisfips55plc, rdflib.Literal(row[3], datatype=rdflib.XSD.string)))
		if len(row[4]):
			g.add((url, gnisfips55cls, rdflib.Literal(row[4], datatype=rdflib.XSD.string)))
		if len(row[5]):
			g.add((url, gnisgsa, rdflib.Literal(row[5], datatype=rdflib.XSD.string)))
		if len(row[6]):
			g.add((url, gnisopm, rdflib.Literal(row[6], datatype=rdflib.XSD.string)))

		# If its a county equivalent, use county properties and link to encompassing state,
		# otherwise link to county.
		if len(row[4]) and (row[4][0] == 'H' or row[4] == 'C7'):
			state_gnis = m[(row[7], None)]
			g.add((url, geowithin, gnis_ns[state_gnis]))
			g.add((url, gnisfips6_4, rdflib.Literal(row[10], datatype=rdflib.XSD.string)))
		else:
			county_gnis = m[(row[7], row[10])]
			g.add((url, geowithin, gnis_ns[county_gnis]))

		# TODO: Get geometries from US Census Bureau.
		#g.add((furl, geohasgeom, gurl))
		#g.add((gurl, rdflib.RDF.type, geogeom))
		#g.add((gurl, geoaswkt, rdflib.Literal('POINT ('+row[13]+' '+row[12]+')', datatype=geowkt)))

		if n % 10000 == 0:
			logging.debug("Processed {0}".format(n))

if __name__ == '__main__':
	main()
