#!/usr/bin/python3 -u

usage="""acew2rdf - convert the US BLS Census of Employment and Wages dataset into RDF

See <https://www.bls.gov/cew/>. Requires python3, python3-rdfllib and 
python3-bsddb3.

Usage:  geonames2rdf [options] *.annual.singlefile.csv GOVT_UNITS_*.txt
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
	singlefn = args[0] # *.annual.singlefile.csv
	govfn = args[1] # GOVT_UNITS_*.txt

	logging.info("Building FIPSMap")
	with open(govfn) as f:
		m = FIPS2GNISDict(f)

	logging.info("Building RDF")
	with open(singlefn) as f:
		g = CEWGraph()
		g.convert_acew(f, m)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
#
#
class CEWGraph(StatsGraph):
	ont_cew = rdflib.Namespace(StatsGraph.prefix + "labor-statistics-bureau/ont/cew#")
	cew_emplvl = ont_cew['EmplLvlObservation'] # rdfs:subClassOf qb:Observation
	#cew_avgwwage = ont_cew['AvgWWageObservation']
	cew_avgapay = ont_cew['AvgPayObservation']
	cew_ind = ont_cew['industry']
	cew_own = ont_cew['ownership']
	#cew_cur = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217
	cew_people = ont_cew['people'] # rdfs:subPropertyOf sdmx-measure:obsValue

	##
	#
	#
	def __init__(self):
		super().__init__()
		self.g.bind('cew-ont', self.ont_cew)

	##
	# Given the CEW area code, return the ID fragment and URL.
	# See <https://data.bls.gov/cew/doc/titles/area/area_titles.htm>.
	#
	# TODO What exceptions are possible here?
	#
	# @input code: The code representing the area.
	# @input m: The dictionary that maps FIPS IDs to GNIS IDs.
	# @return: The area URL (or ...?)
	#
	def decode_area2gnis(self, code, m):
		assert code is not None and len(code) >= 5 and m is not None

		if code[0:5] == 'US000':
			area = self.id_gnis['1890467'] # TODO not sure, maybe use 0
		elif code[0:5] == 'USCMS':
			area = self.id_csa['999']
		elif code[0:5] == 'USMSA':
			area = self.id_cbsa['9999']
		elif code[0:5] == 'USNMS':
			area = self.id_gnis['1'] # TODO not sure
		elif code[0:2] == 'CS':
			area = self.id_csa[code[2:5]]
		elif code[0] == 'C':
			area = self.id_cbsa[code[1:5]+'0']
		elif code[2:5] in {'000','999'}:
			area = self.id_gnis[m[(code[0:2], None)]] # XXX "Unknown Or Undefined" what is an areaRef for this?
		else:
			area = self.id_gnis[m[(code[0:2], code[2:5])]]

		return area

	##
	#
	#
	def convert_acew(self, f, m):
		csv_reader = csv.reader(f, doublequote=False)
		next(csv_reader)

		for n,row in enumerate(csv_reader, 1):
			if n % 10000 == 0:
				logging.debug("Processing {0}".format(n))

			area_code = row[0]
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

			area = self.decode_area2gnis(area_code, m)
			if area is None: # XXX this still valid?
				continue

			url = self.id_cew['-'.join(['emplvl',area_code,industry_code,owner_code,year])]
			self.g.add((url, rdflib.RDF.type, self.qb_obs))
			self.g.add((url, rdflib.RDF.type, self.cew_emplvl))
			self.g.add((url, self.sdmx_area, area))
			self.g.add((url, self.cew_ind, self.id_naics_ind[industry_code]))
			self.g.add((url, self.cew_own, self.id_naics_own[owner_code]))
			self.g.add((url, self.sdmx_freq, self.sdmx_freqa))
			self.g.add((url, self.sdmx_time, rdflib.Literal(year, datatype=rdflib.XSD.gYear)))
			self.g.add((url, self.cew_people, rdflib.Literal(annual_avg_emplvl, datatype=rdflib.XSD.nonNegativeInteger)))

			url = self.id_cew['-'.join(['avgapay',area_code,industry_code,owner_code,year])]
			self.g.add((url, rdflib.RDF.type, self.qb_obs))
			self.g.add((url, rdflib.RDF.type, self.cew_avgapay))
			self.g.add((url, self.sdmx_area, area))
			self.g.add((url, self.cew_ind, self.id_naics_ind[industry_code]))
			self.g.add((url, self.cew_own, self.id_naics_own[owner_code]))
			self.g.add((url, self.sdmx_freq, self.sdmx_freqa))
			self.g.add((url, self.sdmx_time, rdflib.Literal(year, datatype=rdflib.XSD.gYear)))
			self.g.add((url, self.sdmx_cur, rdflib.Literal(avg_annual_pay, datatype=rdflib.XSD.nonNegativeInteger)))

if __name__ == '__main__':
	main()

