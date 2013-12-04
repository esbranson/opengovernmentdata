#!/usr/bin/python3 -uW all

import sys
import csv

import rdflib

qb = rdflib.Namespace('http://purl.org/linked-data/cube#')
sdmx_dimension = rdflib.Namespace('http://purl.org/linked-data/sdmx/2009/dimension#')
sdmx_measure = rdflib.Namespace('http://purl.org/linked-data/sdmx/2009/measure#')
sdmx_attribute = rdflib.Namespace('http://purl.org/linked-data/sdmx/2009/attribute#')
sdmx_code = rdflib.Namespace('http://purl.org/linked-data/sdmx/2009/code#')
gnis_code = rdflib.Namespace('http://data.example.com/usgs.gov/data/gnis#')
cbsa_code = rdflib.Namespace('http://data.example.com/omb.gov/data/cbsa#')
csa_code = rdflib.Namespace('http://data.example.com/omb.gov/data/csa#')
#usgs_gnis = rdflib.Namespace('http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:')
census = rdflib.Namespace('http://data.example.com/census.gov/data/census2010#')
census_onto = rdflib.Namespace('http://data.example.com/census.gov/ont/census2010#')
census_code = rdflib.Namespace('http://data.example.com/census.gov/ont/census2010code#')

dtd = rdflib.XSD.date
dtnni = rdflib.XSD.nonNegativeInteger
dts = rdflib.XSD.string

def graph_init():
	g = rdflib.Graph()
	g.bind('qb', qb)
	g.bind('sdmx-dimension', sdmx_dimension)
	g.bind('sdmx-measure', sdmx_measure)
	g.bind('sdmx-attribute', sdmx_attribute)
	g.bind('sdmx-code', sdmx_code)
	g.bind('census', census)
	g.bind('gnis', gnis_code)
	g.bind('census-onto', census_onto)
	return g

def convert_seg4(prefix='raw/us'):
	fgeo = open(prefix+'geo2010.sf1', errors='replace')
	fseg = open(prefix+'000042010.sf1', errors='replace')
	csvseg = csv.reader(fseg)
	g = graph_init()

	for ln,(lgeo,lseg) in enumerate(zip(fgeo,csvseg)):
		if ln % 1000 == 0:
			print('processed', ln)

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
			area = gnis_code[geo_countyns]
			arean = 'gnis'+geo_countyns
		elif geo_sumlev == '040': # state level
			area = gnis_code[geo_statens]
			arean = 'gnis'+geo_statens
		elif geo_sumlev == '310': # cbsa level
			area = cbsa_code[geo_cbsa]
			arean = 'cbsa'+geo_cbsa
			print('cbsa',geo_cbsa)
		elif geo_sumlev == '330': # csa level
			area = csa_code[geo_csa]
			arean = 'csa'+geo_csa
			print('csa',geo_csa)
		else:
			continue

		# see 6-2 and 6-15 footnotes, 4-9
		if geo_geocomp != '00':
			continue

		base_url = 'sf1_2012_'
		base_dim = 'P01200'
		for i in range(1,49+1):
			suffix = '{:02d}'.format(i)
			url = census[base_url+arean+'_P01200'+suffix]
			g.add((url, rdflib.RDF.type, census_onto['CensusObservation']))
			g.add((url, sdmx_dimension['refArea'], area))
			g.add((url, sdmx_dimension['timePeriod'], rdflib.Literal('2010-04-01', datatype=dtd)))
			g.add((url, census_onto['measure'], rdflib.Literal(base_dim+suffix, datatype=dts)))
			g.add((url, census_onto['people'], rdflib.Literal(lseg[4+71+73+i], datatype=dtnni)))

	fgeo.close()
	fseg.close()

	g.serialize('out/sf1_2010.ttl', format='turtle')

def main():
	prefix = sys.argv[1]
	convert_seg4(prefix)

if __name__ == '__main__':
	main()

