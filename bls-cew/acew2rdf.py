#!/usr/bin/python3 -u

##
# annual QCEW data
#

import rdflib
import csv
import sys
import itertools

# http://geonames.usgs.gov/domestic/download_data.htm
def convert_fips2gnis():
	f = open('../geonames/raw/GOVT_UNITS_20130602.txt')
	csv_reader = csv.reader(f, delimiter='|')

	# skip header
	next(csv_reader)

	# parse 
	gnmap = {}
	for row in csv_reader:
		gnis = row[0]
		typ = row[1]
		fips_c = row[2]
		fips_s = row[4]
#		print('gnmap', gnis, typ, fips_s, fips_c)
		gnmap[(typ,fips_s,fips_c)] = gnis

	return gnmap

# give 2 digit state + 3 digit county fips, return gnis
def search_fips2gnis_county(gnmap, fips_s, fips_c):
	return ('COUNTY', fips_s, fips_c) in gnmap and gnmap[('COUNTY', fips_s, fips_c)] or None

# give 2 digit state fips, return gnis
def search_fips2gnis_state(gnmap, fips_s):
	return gnmap[('STATE', fips_s, '')] # XXX KeyError

qb = rdflib.Namespace("http://purl.org/linked-data/cube#")
sdmx_dimension = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/dimension#")
sdmx_measure = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/measure#")
sdmx_attribute = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
sdmx_code = rdflib.Namespace("http://purl.org/linked-data/sdmx/2009/code#")
bls_cew = rdflib.Namespace("http://data.example.com/bls.gov/data/cew#")
bls_cew_onto = rdflib.Namespace("http://data.example.com/bls.gov/ont/cew#")
usgs_gnis = rdflib.Namespace("http://data.example.com/usgs.gov/data/gnis#")
cbsa_code = rdflib.Namespace("http://data.example.com/omb.gov/data/cbsa#")
csa_code = rdflib.Namespace("http://data.example.com/omb.gov/data/csa#")
#usgs_gnis = rdflib.Namespace("http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:")
naics_ind = rdflib.Namespace("http://data.example.com/census.gov/data/naics-industry#")
naics_own = rdflib.Namespace("http://data.example.com/cenus.gov/data/naics-ownwership#")

def init():
	g = rdflib.Graph()
	g.bind('qb', qb)
	g.bind('sdmx-dimension', sdmx_dimension)
	g.bind('sdmx-measure', sdmx_measure)
	g.bind('sdmx-attribute', sdmx_attribute)
	g.bind('sdmx-code', sdmx_code)
	g.bind('bls-cew', bls_cew)
	g.bind('bls-cew-onto', bls_cew_onto)
	g.bind('gnis', usgs_gnis)
	g.bind('naics-ind', naics_ind)
	g.bind('naics-own', naics_own)
	return g

def convert(gnmap, fnin, fnout=None, fmt='turtle'):
	g = init()
	f = open(fnin)
	csv_reader = csv.reader(f, doublequote=False)

	# get headers
	next(csv_reader)

	# vocab
	obstype = qb['Observation']
	emplvltype = bls_cew_onto['EmplLvlObservation']
#	avgwwagetype = bls_cew_onto['avgwwageObservation']
	avgapaytype = bls_cew_onto['AvgPayObservation']

#	gnisprop = bls_cew_onto['gnis'] # rdfs:subPropertyOf sdmx-dimension:refArea
	areaprop = sdmx_dimension['refArea']
	indprop = bls_cew_onto['industryCode']
	ownprop = bls_cew_onto['ownershipCode']

	freqprop = sdmx_dimension['freq']
	tpprop = sdmx_dimension['timePeriod']

#	curprop = sdmx_attribute['currency'] # TODO put attributes in dataset model
#	salprop = sdmx_attribute['freqDetail']

	freqvala = sdmx_code['freq-A'] # see <http://sdmx.org/docs/1_0/SDMXCommon.xsd> TimePeriodType
#	freqvalw = sdmx_code['freq-W'] # as an attr for weekly salary by quarter
#	curval = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217

	peopvalprop = bls_cew_onto['people'] # rdfs:subPropertyOf sdmx-measure:obsValue
#	obsvalprop = sdmx_measure['obsValue']
	curvalprop = sdmx_measure['currency']

	dtgy = rdflib.XSD.gYear
	dtnni = rdflib.XSD.nonNegativeInteger
#	dti = rdflib.XSD.integer

	splitn = itertools.count(1)
	for n,row in enumerate(csv_reader, 1):
		# logging
		if n % 1000 == 0:
			print('processed', n)

		# cache control (purging)
		if n % 500000 == 0:
			if fnout:
				sfnout = fnout+'.'+str(next(splitn))
				print('serializing', sfnout)
				g.serialize(sfnout, format=fmt)
			g = init()

#		# test control
#		if n % 10000 == 0:
#			break

		# XXX strip quotes
		fips_code = row[0]
		owner_code = row[1]
		industry_code = row[2]
#		agglvl_code = row[3]
#		size_code = row[4]
		year = row[5]
		qtr = row[6]
		disclosure_code = row[7]
#		annual_avg_estabs_count = row[8]
		annual_avg_emplvl = row[9]
#		total_annual_wages = row[10]
#		taxable_annual_wages = row[11]
#		annual_contributions = row[12]
#		annual_avg_wkly_wage = row[13]
		avg_annual_pay = row[14]

		assert qtr == 'A'
		if disclosure_code == 'N':
			continue
		if owner_code not in {'0','5'}:
			continue
		if industry_code[:2] != '10' and len(industry_code) > 2 and '-' not in industry_code:
			continue

		# get gnis
		# XXX error check None return
		if fips_code[0] == 'U':
			# CSAs, MSAs, CMSAs, national, all MSAs, all but MSAs, all CMSAs
			# see ftp://ftp.bls.gov/pub/special.requests/cew/Document/layout.txt
			continue
		elif fips_code[0:2] == 'CS':
			area = csa_code[fips_code[2:5]]
			aid = 'csa'+fips_code[2:5]
		elif fips_code[0] == 'C':
			area = cbsa_code[fips_code[1:5]+'0']
			aid = 'cbsa'+fips_code[1:5]+'0'
		elif fips_code[2:5] in {'000','999'}:
			aid = search_fips2gnis_state(gnmap, fips_code[0:2])
			area = usgs_gnis[aid]
			if fips_code[2:5] in {'999'}: # XXX not located within county?
				aid+='u'
				continue # XXX what is an areaRef for this?
		else:
			aid = search_fips2gnis_county(gnmap, fips_code[0:2], fips_code[2:5])
			if aid is None:
				print('fail countygnis', fips_code[0:2], fips_code[2:5])
				continue
			area = usgs_gnis[aid]

		# build URI
		uri = '_'.join(['emplvl',aid,industry_code,owner_code,year])

		# add data
#		g.add((bls_cew[uri], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri], rdflib.RDF.type, emplvltype))
		g.add((bls_cew[uri], areaprop, area))
		g.add((bls_cew[uri], indprop, naics_ind[industry_code]))
		g.add((bls_cew[uri], ownprop, naics_own[owner_code]))
		g.add((bls_cew[uri], freqprop, freqvala))
		g.add((bls_cew[uri], tpprop, rdflib.Literal(year, datatype=dtgy)))
		g.add((bls_cew[uri], peopvalprop, rdflib.Literal(annual_avg_emplvl, datatype=dtnni)))

		# build URI
		uri = '_'.join(['avgapay',aid,industry_code,owner_code,year])

		# add data
#		g.add((bls_cew[uri], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri], rdflib.RDF.type, avgapaytype))
		g.add((bls_cew[uri], areaprop, area))
		g.add((bls_cew[uri], indprop, naics_ind[industry_code]))
		g.add((bls_cew[uri], ownprop, naics_own[owner_code]))
		g.add((bls_cew[uri], freqprop, freqvala))
		g.add((bls_cew[uri], tpprop, rdflib.Literal(year, datatype=dtgy)))
		g.add((bls_cew[uri], curvalprop, rdflib.Literal(avg_annual_pay, datatype=dtnni)))

	f.close()

	if fnout:
#		g.serialize(fnout, format=fmt)
		g.serialize(fnout+'.'+str(next(splitn)), format=fmt)

	return g

def main():
	infn = sys.argv[1]
	outfn = sys.argv[2]

	if outfn.rsplit('.',1)[-1] == 'nt':
		fmt = 'nt'
	elif outfn.rsplit('.',1)[-1] == 'ttl':
		fmt = 'turtle'
	else:
		print('fatal: unknown format', outfn.rsplit('.',1)[-1])

	gnmap = convert_fips2gnis()
#	convert(gnmap, 'raw/2012.annual.singlefile.csv', 'out/2012.ttl', fmt='turtle')
#	convert(gnmap, 'raw/2012.annual.singlefile.csv', 'out/2012.nt', fmt='nt')
	convert(gnmap, infn, outfn, fmt)

if __name__ == '__main__':
	main()

