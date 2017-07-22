#!/usr/bin/python3 -u

usage="""sf2rdf - convert the US Census Bureau Summary File datasets into RDF

See <https://www.bls.gov/cew/>. Requires python3, python3-rdfllib and 
python3-bsddb3.

Usage:  sf2rdf [options] *geo2010.sf1 *000*20*.sf1 [...]
Arguments:

	-o output	output file (default: stdout)
	-d			enable debugging
	-f fmt		use format for output file (default: turtle)
"""

import rdflib
import getopt
import csv
import sys
import logging

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geonames'))
from geonames2rdf import FIPS2GNISDict
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from stats import StatsGraph

##
# Driver function. Create FIPS-to-GNISID map, then create RDF data cube graph,
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
	geofn = args[0] # XXgeo2010.sf1

	logging.info("Creating RDF graph")
	g = SF1Graph()

	logging.info("Building RDF")
	for segfn in args[1:]: # XX000042010.sf1
		with open(segfn, errors='replace') as segf, open(geofn, errors='replace') as geof:
			g.convert_seg4(segf, geof)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
#
#
class SF1Graph(StatsGraph):
	id_sf1 = rdflib.Namespace(StatsGraph.prefix + "census-bureau/id/sf1/")
	ont_sf1 = rdflib.Namespace(StatsGraph.prefix + "census-bureau/ont/sf1#")
	sf1_code = ont_sf1['code']

	##
	#
	#
	def __init__(self):
		super().__init__()
		self.g.bind('sf1-ont', self.ont_sf1)

	##
	# Only works on segment 4, i.e., <ca000042010.sf1>.
	#
	def convert_seg4(self, segf, geof):
		seg_csv = csv.reader(segf)

		for n,(lgeo,lseg) in enumerate(zip(geof,seg_csv)):
			if n % 10000 == 0:
				logging.debug("Processing {0}".format(n))

			geo_sumlev = lgeo[8:11]
			geo_geocomp = lgeo[11:13]
			geo_logrecno = lgeo[18:25].strip()
			geo_pop100 = lgeo[318:327].strip()
			geo_statens = lgeo[373:381].lstrip('0')
			geo_countyns = lgeo[381:389].lstrip('0')
			geo_cbsa = lgeo[112:117]
			geo_csa = lgeo[124:127]
	#		geo_cousubns = lgeo[389:397].lstrip('0')
	#		geo_placens = lgeo[397:405].lstrip('0')
			seg_logrecno = lseg[4]
	#		seg_P0100001 = lseg[4+1]
	#		seg_P0110001 = lseg[4+71+1]
	#		seg_P0120001 = lseg[4+71+73+1]

			if geo_logrecno != seg_logrecno:
				print(ln, geo_sumlev,geo_logrecno,seg_logrecno)
	#		if geo_pop100 not in {seg_P0100001,seg_P0110001,seg_P0120001}:
	#			print(ln,seg_pop100,seg_P0100001,seg_P0110001,seg_P0120001)

			# see 4-9
			if geo_sumlev == '050': # county level
				area = self.id_gnis[geo_countyns]
				arean = 'gnis'+geo_countyns
			elif geo_sumlev == '040': # state level
				area = self.id_gnis[geo_statens]
				arean = 'gnis'+geo_statens
			elif geo_sumlev == '310': # cbsa level
				area = self.id_cbsa[geo_cbsa]
				arean = 'cbsa'+geo_cbsa
			elif geo_sumlev == '330': # csa level
				area = self.id_csa[geo_csa]
				arean = 'csa'+geo_csa
			else:
				continue

			# see 6-2 and 6-15 footnotes, 4-9
			if geo_geocomp != '00':
				continue

			for i in range(1,49+1):
				dim = 'P01200' + '{:02d}'.format(i)
				url = self.id_sf1['-'.join(['sf1','2012',dim,arean])]
				self.g.add((url, rdflib.RDF.type, self.ont_sf1['CensusObservation']))
				self.g.add((url, self.sdmx_dimension['refArea'], area))
				self.g.add((url, self.sdmx_dimension['timePeriod'], rdflib.Literal('2010-04-01', datatype=rdflib.XSD.date)))
				self.g.add((url, self.ont_sf1['measure'], rdflib.Literal(base_dim+suffix, datatype=rdflib.XSD.string)))
				self.g.add((url, self.ont_sf1['people'], rdflib.Literal(lseg[4+71+73+i], datatype=rdflib.XSD.nonNegativeInteger)))

if __name__ == '__main__':
	main()

