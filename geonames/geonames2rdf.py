#!/usr/bin/python3 -u

usage="""geonames2rdf - convert the US BGN "federal codes" dataset into RDF

See <http://geonames.usgs.gov/domestic/download_data.htm> under "Topical
Gazetteers/Government Units" and "State Files with Federal Codes".

Usage:  geonames2rdf [options] GOVT_UNITS_*.txt NationalFedCodes_*.txt
Arguments:

	-o output	output file (default: stdout)
	-d			enable debugging
	-f fmt		use format for output file (default: turtle)
"""

import csv
import rdflib
import sys
import getopt
import logging
import collections

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from stats import StatsGraph

##
# Driver function. Create FIPS-to-GNISID map, then create feature RDF graph,
# then save graph.
#
def main():
	outf = sys.stdout.buffer
	outfmt = 'turtle'
	debuglvl = logging.INFO

	logging.basicConfig(format='{levelname} {funcName}/l{lineno}: {message}', style='{', level=debuglvl)

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
	if len(args) < 2:
		logging.fatal('Need input files')
		print(usage, file=sys.stderr)
		return 1

	logging.getLogger().setLevel(debuglvl)
	govfn = args[0] # GOVT_UNITS_*.txt
	codesfn = args[1] # NationalFedCodes_*.txt

	logging.info("Building FIPS2GNISDict")
	with open(govfn) as f:
		m = FIPS2GNISDict(f)

	logging.info("Creating graph")
	g = GeonamesGraph()

	logging.info("Adding states to graph")
	with open(govfn) as f:
		g.convert_fips2gnis(f)

	logging.info("Building RDF")
	with open(codesfn) as f:
		g.convert_fedcodes(f, m)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# A map from (FIPS state numeric, FIPS county numeric) => GNIS ID. The BGN
# Geographic Names Information System ID is the official geographic name
# identifier and is a better identifier than FIPS 5-2 codes for states and
# FIPS 6-4 codes for counties.
#
# Use like a dictionary, where the key is a tuple (FIPS state, FIPS county),
# and where the FIPS county may be None if for a state.
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
# Represent a BGN GNIS geonames graph.
#
class GeonamesGraph(StatsGraph):
	ont_gnis = rdflib.Namespace("http://data.usgs.gov/ont/gnis#")
	ont_geo = rdflib.Namespace('http://www.opengis.net/ont/geosparql#')
	geo_feat = ont_geo['Feature']
	geo_hasgeom = ont_geo['hasGeometry']
	geo_geom = ont_geo['Geometry']
	geo_aswkt = ont_geo['asWKT']
	geo_wkt = ont_geo['wktLiteral']
	geo_within = ont_geo['sfWithin']
	gnis_feat = ont_gnis['Feature']
	gnis_name = ont_gnis['featureName']
	gnis_fid = ont_gnis['featureID']
	gnis_cls = ont_gnis['featureClass']
	gnis_fips55plc = ont_gnis['censusPlace']
	gnis_fips55cls = ont_gnis['censusClass']
	gnis_fips5_2n = ont_gnis['stateNumeric']
	gnis_fips5_2a = ont_gnis['stateAlpha']
	gnis_fips6_4 = ont_gnis['countyNumeric']
	gnis_gsa = ont_gnis['gsaLocation']
	gnis_opm = ont_gnis['opmLocation']

	##
	#
	#
	def __init__(self):
		super().__init__()
		self.g.bind('gnis-ont', self.ont_gnis)
		self.g.bind('geo', self.ont_geo)

	##
	# Use BGN "Government Units" file to add states to graph because they aren't included
	# in the NationalFedCodes_*.txt file.
	#
	# @input g: The Graph.
	# @input f: The BGN "Government Units" file.
	#
	def convert_fips2gnis(self, f):
		csv_reader = csv.reader(f, delimiter='|')
		next(csv_reader)
		for row in csv_reader:
			if row[1] == 'STATE':
				url = self.id_gnis[row[0]]
				self.g.add((url, rdflib.RDF.type, self.gnis_feat))
				self.g.add((url, rdflib.RDF.type, self.geo_feat))
				self.g.add((url, self.gnis_fid, rdflib.Literal(row[0], datatype=rdflib.XSD.string)))
				self.g.add((url, rdflib.RDFS.label, rdflib.Literal(row[6]))) # XXX: In English?
				self.g.add((url, self.gnis_name, rdflib.Literal(row[9], datatype=rdflib.XSD.string)))
				self.g.add((url, self.gnis_fips5_2n, rdflib.Literal(row[4], datatype=rdflib.XSD.string)))
				self.g.add((url, self.gnis_fips5_2a, rdflib.Literal(row[5], datatype=rdflib.XSD.string)))

	##
	# Convert BGN "State Files with Federal Codes" file to RDF.
	#
	# @input g: An RDFLib Graph.
	# @input f: The BGN "Government Units" file.
	# @input m: A FIPS2GNISDict.
	#
	def convert_fedcodes(self, f, m):
		csv_reader = csv.reader(f, delimiter='|')
		next(csv_reader)

		for n,row in enumerate(csv_reader, 1):
			if n % 10000 == 0:
				logging.debug("Processing {0}".format(n))

			if row[2] not in {'Civil', 'Census', 'Populated Place'}:
				continue

			url = self.id_gnis[row[0]]
			self.g.add((url, rdflib.RDF.type, self.gnis_feat))
			self.g.add((url, rdflib.RDF.type, self.geo_feat))
			self.g.add((url, self.gnis_fid, rdflib.Literal(row[0], datatype=rdflib.XSD.string)))
			self.g.add((url, rdflib.RDFS.label, rdflib.Literal(row[1]))) # XXX: In English?
			self.g.add((url, self.gnis_name, rdflib.Literal(row[1], datatype=rdflib.XSD.string)))
			self.g.add((url, self.gnis_cls, rdflib.Literal(row[2], datatype=rdflib.XSD.string)))

			if len(row[3]):
				self.g.add((url, self.gnis_fips55plc, rdflib.Literal(row[3], datatype=rdflib.XSD.string)))
			if len(row[4]):
				self.g.add((url, self.gnis_fips55cls, rdflib.Literal(row[4], datatype=rdflib.XSD.string)))
			if len(row[5]):
				self.g.add((url, self.gnis_gsa, rdflib.Literal(row[5], datatype=rdflib.XSD.string)))
			if len(row[6]):
				self.g.add((url, self.gnis_opm, rdflib.Literal(row[6], datatype=rdflib.XSD.string)))

			# If its a county equivalent, use county properties and link to encompassing state,
			# otherwise link to county.
			if len(row[4]) and (row[4][0] == 'H' or row[4] == 'C7'):
				state_gnis = m[(row[7], None)]
				self.g.add((url, self.geo_within, self.id_gnis[state_gnis]))
				self.g.add((url, self.gnis_fips6_4, rdflib.Literal(row[10], datatype=rdflib.XSD.string)))
			else:
				county_gnis = m[(row[7], row[10])]
				self.g.add((url, self.geo_within, self.id_gnis[county_gnis]))

			# TODO: Get geometries from US Census Bureau.
			#self.g.add((furl, self.geo_hasgeom, gurl))
			#self.g.add((gurl, rdflib.RDF.type, self.geo_geom))
			#self.g.add((gurl, self.geo_aswkt, rdflib.Literal('POINT ('+row[13]+' '+row[12]+')', datatype=self.geo_wkt)))

if __name__ == '__main__':
	main()
