#!/usr/bin/python3 -u

usage="""lau2rdf - convert US BLS Local Area Unemployment Statistics data into RDF

See <https://www.bls.gov/lau/>. Requires python3, python3-rdfllib and 
python3-bsddb3.

Usage:  lau2rdf [options] acgnisfile infile

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

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'geonames'))
from geonames2rdf import FIPSMap
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
from stats import StatsGraph

def open_acgnis(acgnisfn):
	acgnis = {}
	f = open(acgnisfn)
	csv_reader = csv.reader(f, delimiter='\t')
	for row in csv_reader:
		acgnis[row[0]] = row[1]
	return acgnis

qb = rdflib.Namespace("http://purl.org/linked-data/cube#")
sdmx_dimension = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
sdmx_measure = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
sdmx_attribute = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
sdmx_code = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/code#")
bls_la = rdflib.Namespace("http://data.bls.gov/data/la#")
bls_la_onto = rdflib.Namespace("http://data.bls.gov/ont/la#")
#usgs_fips_c = rdflib.Namespace("http://data.usgs.gov/data/geonames/fips-county/")
#usgs_gnis = rdflib.Namespace("http://data.usgs.gov/data/geonames/gnis/")
usgs_gnis = rdflib.Namespace("http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:")

def init():
	# convert
	g = rdflib.Graph()
	g.bind('qb', qb)
	g.bind('sdmx-dimension', sdmx_dimension)
	g.bind('sdmx-measure', sdmx_measure)
	g.bind('sdmx-attribute', sdmx_attribute)
	g.bind('sdmx-code', sdmx_code)
	g.bind('bls-la', bls_la)
	g.bind('bls-la-onto', bls_la_onto)
#	g.bind('usgs-fips-c', usgs_fips_c)
	g.bind('usgs-gnis', usgs_gnis)
	return g

def convert(infn, outfn, g, acgnis, fmt='turtle'):
#	f = open('raw/la/la.data.12.Colorado')
	f = open(infn)
	csv_reader = csv.reader(f, delimiter='\t')

	# get headers
#	heads = next(csv_reader)
	next(csv_reader)

	# vocab
#	obstyp = qb['Observation']
	tunemplobs = bls_la_onto['TotalUnemploymentObservation'] # rdfs:subClassOf qb:Observation
	templobs = bls_la_onto['TotalEmploymentObservation']
	tlfobs = bls_la_onto['TotalLaborForceObservation']
	runemplobs = bls_la_onto['RatioUnemploymentToLaborForceObservation']

#	sidprop = bls_la_onto['sid']
	acprop = bls_la_onto['area']
	gnisprop = bls_la_onto['gnis']
#	indprop = bls_la_onto['indicator']
#	adjprop = bls_la_onto['processing']
	freqprop = sdmx_dimension['freq']
	tpprop = sdmx_dimension['timePeriod']
	adjprop = sdmx_attribute['adjustDetail']

#	tunempl = bls_la_onto['totalUnemployment']
#	templ = bls_la_onto['totalEmployment']
#	tlf = bls_la_onto['totalLaborForce']
#	runempl = bls_la_onto['ratioUnemploymentToLaborForce']
#	rempl = bls_la_onto['RatioEmploymentToLaborForce']

	seasval = bls_la_onto['seasonal']
	freqvalm = sdmx_code['freq-M']
	freqvaly = sdmx_code['freq-A']

	rate = bls_la_onto['percent']
	count = bls_la_onto['people'] # rdfs:subPropertyOf sdmx-measure:obsValue

	dts = rdflib.XSD.string

	for n,row in enumerate(csv_reader, 1):
		sid = row[0].strip() #series_id
		year = row[1].strip()
		period = row[2].strip()
		value = row[3].strip()
#		fn = row[4].strip() # footnote_codes

#		survey = sid[0:2]
		seas = sid[2] # S=Seasonally Adjusted U=Unadjusted
		ac = sid[3:11] # area_code
		meas = sid[11:13] # measure_code
		if len(sid) > 13:
			ex = sid[13:]
		else:
			ex = ''

		# XXX skip rest for now
		if ac not in acgnis:
			continue

		# XXX not available. footcode 'N'
		if value == '-':
			continue

		# XXX duplicates?
		if len(ex):
			continue

		ac_typ = ac[0:2]
		ac_fips = ac[2:4]
#		ac_rest = ac[2:8]

		# date
		if period == 'M13':
			date = rdflib.Literal(year, datatype=rdflib.XSD.gYear)
			freqval = freqvaly
		else:
			date = rdflib.Literal(year+'-'+period.lstrip('M'), datatype=rdflib.XSD.gYearMonth)
			freqval = freqvalm

		# type
		if meas == '03':
			typ = 'runempl'
			valtyp = rate
			obstypval = runemplobs
			dt = rdflib.XSD.decimal
		elif meas == '04':
			typ = 'tunempl'
			valtyp = count
			obstypval = tunemplobs
			dt = rdflib.XSD.nonNegativeInteger
		elif meas == '05':
			typ = 'templ'
			valtyp = count
			obstypval = templobs
			dt = rdflib.XSD.nonNegativeInteger
		elif meas == '06':
			typ = 'tlf'
			valtyp = count
			obstypval = tlfobs
			dt = rdflib.XSD.nonNegativeInteger
		else:
			print('WARN: UNK meas')
			valtyp = sdmx_dimension['obsValue']
			indval = rdflib.Literal(value)

		# build URI
#		ref = sid+'_'+year+'_'+period+'_'+meas
		ref = '_'.join([typ,sid,year,period])

		# add data
#		g.add((bls_la[ref], rdflib.RDF.type, obstyp))
		g.add((bls_la[ref], rdflib.RDF.type, obstypval))
#		g.add((bls_la[ref], acprop, rdflib.Literal(ac, datatype=dts)))
		g.add((bls_la[ref], freqprop, freqval))
		g.add((bls_la[ref], tpprop, date))
		g.add((bls_la[ref], valtyp, rdflib.Literal(value, datatype=dt)))

		# get FIPS from LAUS area code
		if ac in acgnis:
			gnis = acgnis[ac]
			g.add((bls_la[ref], gnisprop, usgs_gnis[gnis]))

		# seasonality
		if seas == 'S':
			g.add((bls_la[ref], adjprop, seasval))
		elif seas == 'U':
			pass
		else:
			print('WARN: UNK adjustment')

		# logging
		if n % 1000 == 0:
			print('processed', n)

	f.close()

	print('writing')
#	g.serialize('derp.ttl', format='turtle')
#	g.serialize(outfn, format=fmt)
	fo = open(outfn, 'xb')
	g.serialize(fo, format=fmt)
	fo.close()

#	return g

def main():
	if len(sys.argv) != 4:
		print('FATAL: not enough args')
		print(usage)
		sys.exit(1)
	acgnisfn, infn, outfn = sys.argv[1], sys.argv[2], sys.argv[3]
	if outfn.endswith('nt'):
		fmt = 'nt'
	elif outfn.endswith('ttl'):
		fmt = 'turtle'
	else:
		print('FATAL: unkown format', repr(outfn))
		sys.exit(1)
	print('opening', acgnisfn)
	acgnis = open_acgnis(acgnisfn)
	print('doing', infn, outfn)
	g = init()
	convert(infn, outfn, g, acgnis, fmt)

if __name__ == '__main__':
	main()

