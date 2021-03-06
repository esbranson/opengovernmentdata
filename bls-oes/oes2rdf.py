#!/usr/bin/python3 -u

usage="""oes2rdf - convert US BLS Occupational Employment Statistics dataset into RDF

See <https://www.bls.gov/oes/>. Requires python3, python3-rdfllib and 
python3-bsddb3.

Usage:  oes2rdf [options] oe.data.1.AllData oe.industry GOVT_UNITS_*.txt

	-o output	output file (default: stdout)
	-d			enable debugging
	-f fmt		use format for output file (default: turtle)
"""

import rdflib
import getopt
import csv
import tempfile
import sys
import logging
import collections

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geonames'))
from geonames2rdf import FIPS2GNISDict
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import stats

##
# Driver function. Create FIPS-to-GNISID map, then create RDF data cube graph,
# then save graph.
#
def main():
	outf = sys.stdout.buffer
	outfmt = 'turtle'
	debuglvl = logging.INFO

	logging.basicConfig(format='{levelname}/{funcName} {message}', style='{', level=debuglvl)

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'ho:df:')
	except getopt.GetoptError as e:
		logging.fatal('getopt error {}'.format(e))
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
			logging.fatal('invalid flag {}'.format(opt))
			print(usage, file=sys.stderr)
			return 1
	if len(args) < 3:
		logging.fatal('need input files')
		print(usage, file=sys.stderr)
		return 1

	logging.getLogger().setLevel(debuglvl)
	datafn = args[0] # oe.data.0.Current
	indfn = args[1] # oe.industry
	govfn = args[2] # GOVT_UNITS_*.txt

	logging.info("Building FIPS->GNIS dictionary")
	with open(govfn) as f:
		gnism = FIPS2GNISDict(f)

	logging.info("Building industry->NAICS dictionary")
	with open(indfn) as f:
		indm = IndustryMap(f)

	logging.info("Building RDF")
	g = OESGraph()
	with open(datafn) as f:
		g.build_data(f, gnism, indm)

	logging.info("Saving RDF")
	g.serialize(outf, format=outfmt)

##
# Use oe.industry file to pre-build map of industry codes to -> NAICS codes.
#
# TODO: Deal with the national level with ownership codes.
#
# @input f: The oe.industry file.
#
class IndustryMap(collections.UserDict):
	def __init__(self, f):
		super().__init__()
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
			self.data[code] = (ind,own)

##
# Represent a OES graph.
#
class OESGraph(stats.StatsGraph):
	#data_oes = rdflib.Namespace("http://data.bls.gov/dataset/oes/")
	ont_oes = rdflib.Namespace("http://data.bls.gov/ont/oes#")
	oes_emp = ont_oes['EmplObservation'] # rdfs:subClassOf qb:Observation
	oes_empsem = ont_oes['EmplSEMObservation'] # rdfs:subClassOf qb:Observation
	oes_wagemeana = ont_oes['WageMeanAnnualObservation'] # rdfs:subClassOf qb:Observation
	oes_wagemeda = ont_oes['WageMedianAnnualObservation'] # rdfs:subClassOf qb:Observation
	oes_wagsem = ont_oes['WageSEMObservation'] # rdfs:subClassOf qb:Observation
	oes_series = ont_oes['series']
	oes_ind = ont_oes['industry']
	oes_own = ont_oes['ownership']
	oes_soc = ont_oes['occupation']
	oes_people = ont_oes['people'] # rdfs:subPropertyOf sdmx-measure:obsValue
	oes_rse = ont_oes['percentRelStdErr'] # rdfs:subPropertyOf sdmx-measure:obsValue
	#curval = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217

	##
	#
	#
	def __init__(self):
		super().__init__()
		self.g.bind('oes-ont', self.ont_oes)

	##
	# Parse oe.data file and build OESGraph.
	#
	# TODO: Don't skip any record types.
	#
	# @input f: The data file, e.g., <oe.data.0.Current>.
	# @input gnism: A dictionary mapping FIPS IDs to GNIS IDs, i.e., a FIPS2GNISDict.
	# @input indm: A dictionary mapping industry codes to NAICS codes, i.e., a IndustryMap.
	#
	def build_data(self, f, gnism, indm):
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

			# XXX: Don't know what other periods mean.
			assert period == 'A01'
			# XXX: Need to remove this.
			if year != '2016':
				continue

			areaurl,indurl,ownurl,socurl,datatype = self.parse_series_id(series, gnism, indm)
			if datatype is None:
				continue

			url = self.id_oes['-'.join([series,year,period])]
			self.g.add((url, rdflib.RDF.type, self.qb_obs))
			self.g.add((url, self.sdmx_area, areaurl))
			self.g.add((url, self.oes_series, self.id_oes[series]))
			self.g.add((url, self.oes_ind, indurl))
			self.g.add((url, self.oes_own, ownurl))
			self.g.add((url, self.oes_soc, socurl))
			self.g.add((url, self.sdmx_freq, self.sdmx_freqa))
			self.g.add((url, self.sdmx_time, rdflib.Literal(year, datatype=rdflib.XSD.gYear)))
			if datatype == '01':
				self.g.add((url, rdflib.RDF.type, self.oes_emp))
				self.g.add((url, self.oes_people, rdflib.Literal(value, datatype=rdflib.XSD.nonNegativeInteger)))
			elif datatype == '02':
				self.g.add((url, rdflib.RDF.type, self.oes_empsem))
				self.g.add((url, self.oes_rse, rdflib.Literal(value, datatype=rdflib.XSD.decimal)))
			elif datatype == '04':
				self.g.add((url, rdflib.RDF.type, self.oes_wagemeana))
				self.g.add((url, self.sdmx_cur, rdflib.Literal(value, datatype=rdflib.XSD.nonNegativeInteger)))
			elif datatype == '05':
				self.g.add((url, rdflib.RDF.type, self.oes_wagsem))
				self.g.add((url, self.oes_rse, rdflib.Literal(value, datatype=rdflib.XSD.decimal)))
			elif datatype == '13':
				self.g.add((url, rdflib.RDF.type, self.oes_wagemeda))
				self.g.add((url, self.sdmx_cur, rdflib.Literal(value, datatype=rdflib.XSD.nonNegativeInteger)))

	##
	# Parse the series_id field. Return None if we should skip record.
	#
	# TODO: Don't skip nonmetropolitan areas.
	#
	def parse_series_id(self, s, gnism, indm):
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
			areaurl = self.id_gnis['1890467']
		elif area[0:2] != '00' and area[2:7] == '00000':
			areaurl = self.id_gnis[gnism[(area[0:2], None)]]
		elif area[0:2] != '00' and area[2:7] != '00000':
			# TODO
			logging.debug("skipping record: nonmetro area {0}".format(area))
			return (None,)*5
		else:
			areaurl = self.id_cbsa[area[2:7]]

		ind,own = indm[industry]
		indurl = self.id_naics_ind[ind]
		ownurl = self.id_naics_own[own]
		socurl = self.id_soc[s[0:2]+'-'+s[2:6]]

		return areaurl,indurl,ownurl,socurl,datatype

if __name__ == '__main__':
	main()

