#!/usr/bin/python3 -u

##
# 
#

import rdflib
import rdflib.plugins.sleepycat
import tempfile

##
#
#
class StatsGraph:
	prefix = "https://ld.data.gov/"
	id_gnis = rdflib.Namespace(prefix + "geographic-names-board/id/gnis/")
	id_oes = rdflib.Namespace(prefix + "labor-statistics-bureau/id/oes/")
	id_lau = rdflib.Namespace(prefix + "labor-statistics-bureau/id/lau/")
	id_cew = rdflib.Namespace(prefix + "labor-statistics-bureau/id/cew/")
	id_soc = rdflib.Namespace(prefix + "management-and-budget-office/id/soc/")
	id_cbsa = rdflib.Namespace(prefix + "management-and-budget-office/id/cbsa/")
	id_csa = rdflib.Namespace(prefix + "management-and-budget-office/id/csa/")
	id_naics_ind = rdflib.Namespace(prefix + "census-bureau/id/naics-industry/")
	id_naics_own = rdflib.Namespace(prefix + "census-bureau/id/naics-ownership/")
	qb = rdflib.Namespace("http://purl.org/linked-data/cube#")
	sdmx_dimension = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
	sdmx_measure = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
	sdmx_attribute = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
	sdmx_code = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/code#")
	# TODO: use rdfs:subPropertyOf
	qb_obs = qb['Observation']
	sdmx_area = sdmx_dimension['refArea']
	sdmx_freq = sdmx_dimension['freq']
	sdmx_time = sdmx_dimension['timePeriod']
	sdmx_freqa = sdmx_code['freq-A'] # see <http://sdmx.org/docs/1_0/SDMXCommon.xsd> TimePeriodType
	sdmx_freqm = sdmx_code['freq-M']
	sdmx_freqw = sdmx_code['freq-W']
	sdmx_freqq = sdmx_code['freq-Q']
	sdmx_obs = sdmx_measure['obsValue']
	sdmx_cur = sdmx_measure['currency']
	sdmx_adj = sdmx_attribute['adjustDetail']

	def __init__(self):
		with tempfile.TemporaryDirectory() as tmpdn:
			self.g = rdflib.Graph(rdflib.plugins.sleepycat.Sleepycat(tmpdn))
		#self.g.bind('oes', self.id_oes)
		#self.g.bind('gnis', self.id_gnis)
		#self.g.bind('cbsa', self.id_cbsa)
		#self.g.bind('naics-ind', self.id_naics_ind)
		#self.g.bind('naics-own', self.id_naics_own)
		#self.g.bind('soc', self.id_soc)
		#self.g.bind('lau', self.id_lau)
		self.g.bind('qb', self.qb)
		self.g.bind('sdmx-dimension', self.sdmx_dimension)
		self.g.bind('sdmx-measure', self.sdmx_measure)
		self.g.bind('sdmx-attribute', self.sdmx_attribute)
		self.g.bind('sdmx-code', self.sdmx_code)

	##
	#
	#
	def serialize(self, *args, **kwargs):
		self.g.serialize(*args, **kwargs)

