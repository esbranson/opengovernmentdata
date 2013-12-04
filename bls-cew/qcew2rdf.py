#!/usr/bin/python3 -u

##
# Quarterly QCEW data
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
	return gnmap[('COUNTY', fips_s, fips_c)] # XXX KeyError

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

def convert(gnmap, fnin, fnout=None, format='turtle'):
	g = init()
	f = open(fnin)
	csv_reader = csv.reader(f, doublequote=False)

	# get headers
	next(csv_reader)

	# vocab
	obstype = qb['Observation']
	emplvltype = bls_cew_onto['emplvlObservation']
	avgwwagetype = bls_cew_onto['avgwwageObservation']

	gnisprop = bls_cew_onto['gnis'] # rdfs:subPropertyOf sdmx-dimension:refArea
	indprop = bls_cew_onto['industryCode']
	ownprop = bls_cew_onto['ownershipCode']

	freqprop = sdmx_dimension['freq']
	tpprop = sdmx_dimension['timePeriod']

#	curprop = sdmx_attribute['currency'] # TODO put attributes in dataset model
#	salprop = sdmx_attribute['freqDetail']

	freqvalq = sdmx_code['freq-Q'] # see <http://sdmx.org/docs/1_0/SDMXCommon.xsd> TimePeriodType
	freqvalm = sdmx_code['freq-M']
#	freqvalw = sdmx_code['freq-W'] # as an attr for weekly salary by quarter
#	curval = rdflib.Literal('USD', datatype=rdflib.XSD.string) # ISO 4217

	peopvalprop = bls_cew_onto['people'] # rdfs:subPropertyOf sdmx-measure:obsValue
#	obsvalprop = sdmx_measure['obsValue']
	curvalprop = sdmx_measure['currency']

	dtgym = rdflib.XSD.gYearMonth
	dtnni = rdflib.XSD.nonNegativeInteger
	dti = rdflib.XSD.integer

	# maps to cache other URIs
	usgs_gnis_map = {}
	naics_ind_map = {}
	sic_own_map = {}

	splitn = itertools.count(1)
	for n,row in enumerate(csv_reader, 1):
		# XXX strip quotes
		fips_code = row[0]
		owner_code = row[1]
		industry_code = row[2]
#		agglvl_code = row[3]
#		size_code = row[4]
		year = row[5]
		qtr = row[6]
#		disclosure_code = row[7]
		qtrly_estabs_count = row[8]
		month1_emplvl = row[9]
		month2_emplvl = row[10]
		month3_emplvl = row[11]
		total_qtrly_wages = row[12]
#		taxable_qtrly_wages = row[13] # XXX ever non-zero?
#		qtrly_contributions = row[14] # XXX ever non-zero?
		avg_wkly_wage = row[15]
#		print('qcew', fips_code, owner_code, industry_code, year, qtr, qtrly_estabs_count, month1_emplvl, month2_emplvl, month3_emplvl, total_qtrly_wages, avg_wkly_wage)
#		continue

		# get gnis
		# XXX error check None return
		if fips_code[0] in {'U', 'C'}:
			# CSAs, MSAs, CMSAs, national, all MSAs, all but MSAs, all CMSAs
			# see ftp://ftp.bls.gov/pub/special.requests/cew/Document/layout.txt
			continue
		elif fips_code[2:5] in {'000','999'}:
			gnis = search_fips2gnis_state(gnmap, fips_code[0:2])
		else:
			gnis = search_fips2gnis_county(gnmap, fips_code[0:2], fips_code[2:5])

		#
		# do monthly employment levels
		#

		# date literals
		if qtr == '1':
			month1_date = year+'-01'
			month2_date = year+'-02'
			month3_date = year+'-03'
		elif qtr == '2':
			month1_date = year+'-04'
			month2_date = year+'-05'
			month3_date = year+'-06'
		elif qtr == '3':
			month1_date = year+'-07'
			month2_date = year+'-08'
			month3_date = year+'-09'
		elif qtr == '4':
			month1_date = year+'-10'
			month2_date = year+'-11'
			month3_date = year+'-12'

		# build URIs
#		uri1 = 'emplvl_'+gnis+'_'+month1_date+'_'+industry_code+'_'+owner_code
#		uri2 = 'emplvl_'+gnis+'_'+month2_date+'_'+industry_code+'_'+owner_code
#		uri3 = 'emplvl_'+gnis+'_'+month3_date+'_'+industry_code+'_'+owner_code
#		if fips_code[2:5] in {'999'}: # XXX not located within county?
#			uri1 = 'emplvl_'+gnis+'u_'+month1_date+'_'+industry_code+'_'+owner_code
#			uri2 = 'emplvl_'+gnis+'u_'+month2_date+'_'+industry_code+'_'+owner_code
#			uri3 = 'emplvl_'+gnis+'u_'+month3_date+'_'+industry_code+'_'+owner_code
		gniss=gnis
		if fips_code[2:5] in {'999'}: # XXX not located within county?
#			baseuri = 'emplvl_{}u_{}_{}_{}'
			gniss+='u'
#		else:
#			baseuri = 'emplvl_{}_{}_{}_{}'
#		uri1 = baseuri.format(gnis,industry_code,owner_code,month1_date)
#		uri2 = baseuri.format(gnis,industry_code,owner_code,month2_date)
#		uri3 = baseuri.format(gnis,industry_code,owner_code,month3_date)
		uri1 = '_'.join(['emplvl',gniss,industry_code,owner_code,month1_date])
		uri2 = '_'.join(['emplvl',gniss,industry_code,owner_code,month2_date])
		uri3 = '_'.join(['emplvl',gniss,industry_code,owner_code,month3_date])

		# URI maps XXX else rdflib won't prefix them XXX still wont
		try:
			usgs_gnis_m = usgs_gnis_map[gnis]
		except KeyError:
			usgs_gnis_m = usgs_gnis[gnis]
			usgs_gnis_map[gnis] = usgs_gnis_m
		try:
			naics_ind_m = naics_ind_map[industry_code]
		except KeyError:
			naics_ind_m = naics_ind[industry_code]
			naics_ind_map[industry_code] = naics_ind_m
		try:
			sic_own_m = sic_own_map[owner_code]
		except KeyError:
			sic_own_m = sic_own[owner_code]
			sic_own_map[owner_code] = sic_own_m

		# add data
		g.add((bls_cew[uri1], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri1], rdflib.RDF.type, emplvltype))
		g.add((bls_cew[uri1], gnisprop, usgs_gnis_m))
#		g.add((bls_cew[uri1], gnisprop, usgs_gnis[gnis]))
#		g.add((bls_cew[uri1], indprop, naics_ind[industry_code]))
#		g.add((bls_cew[uri1], ownprop, sic_own[owner_code]))
		g.add((bls_cew[uri1], indprop, naics_ind_m))
		g.add((bls_cew[uri1], ownprop, sic_own_m))
		g.add((bls_cew[uri1], freqprop, freqvalm))
		g.add((bls_cew[uri1], tpprop, rdflib.Literal(month1_date, datatype=dtgym)))
		g.add((bls_cew[uri1], peopvalprop, rdflib.Literal(month1_emplvl, datatype=dtnni)))

		g.add((bls_cew[uri2], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri2], rdflib.RDF.type, emplvltype))
		g.add((bls_cew[uri2], gnisprop, usgs_gnis_m))
#		g.add((bls_cew[uri2], gnisprop, usgs_gnis[gnis]))
#		g.add((bls_cew[uri2], indprop, naics_ind[industry_code]))
#		g.add((bls_cew[uri2], ownprop, sic_own[owner_code]))
		g.add((bls_cew[uri2], indprop, naics_ind_m))
		g.add((bls_cew[uri2], ownprop, sic_own_m))
		g.add((bls_cew[uri2], freqprop, freqvalm))
		g.add((bls_cew[uri2], tpprop, rdflib.Literal(month2_date, datatype=dtgym)))
		g.add((bls_cew[uri2], peopvalprop, rdflib.Literal(month2_emplvl, datatype=dtnni)))

		g.add((bls_cew[uri3], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri3], rdflib.RDF.type, emplvltype))
		g.add((bls_cew[uri3], gnisprop, usgs_gnis_m))
#		g.add((bls_cew[uri3], gnisprop, usgs_gnis[gnis]))
#		g.add((bls_cew[uri3], indprop, naics_ind[industry_code]))
#		g.add((bls_cew[uri3], ownprop, sic_own[owner_code]))
		g.add((bls_cew[uri3], indprop, naics_ind_m))
		g.add((bls_cew[uri3], ownprop, sic_own_m))
		g.add((bls_cew[uri3], freqprop, freqvalm))
		g.add((bls_cew[uri3], tpprop, rdflib.Literal(month3_date, datatype=dtgym)))
		g.add((bls_cew[uri3], peopvalprop, rdflib.Literal(month3_emplvl, datatype=dtnni)))

		#
		# do quarterly average weekly wages
		#

		# date literals
		if qtr == '1':
			date = year+'-01'
		elif qtr == '2':
			date = year+'-04'
		elif qtr == '3':
			date = year+'-07'
		elif qtr == '4':
			date = year+'-10'

		# build URI
#		uri = 'avgwwage_'+gnis+'_'+date+'_'+industry_code+'_'+owner_code
		uri = '_'.join(['avgwwage',gnis,industry_code,owner_code,date])

		# add data
		g.add((bls_cew[uri], rdflib.RDF.type, obstype))
		g.add((bls_cew[uri], rdflib.RDF.type, avgwwagetype))
		g.add((bls_cew[uri], gnisprop, usgs_gnis_m))
#		g.add((bls_cew[uri], gnisprop, usgs_gnis[gnis]))
#		g.add((bls_cew[uri], indprop, naics_ind[industry_code]))
#		g.add((bls_cew[uri], ownprop, sic_own[owner_code]))
		g.add((bls_cew[uri], indprop, naics_ind_m))
		g.add((bls_cew[uri], ownprop, sic_own_m))
		g.add((bls_cew[uri], freqprop, freqvalq))
		g.add((bls_cew[uri], tpprop, rdflib.Literal(date, datatype=dtgym)))
		g.add((bls_cew[uri], curvalprop, rdflib.Literal(avg_wkly_wage, datatype=dti)))

		# logging
		if n % 1000 == 0:
			print('processed', n)

		# cache control (purging)
		if n % 40000 == 0:
			usgs_gnis_map = {}
			if fnout:
				g.serialize(fnout+'.'+str(next(splitn)), format=format)
			g = init()

#		# test control
#		if n % 10000 == 0:
#			break

	f.close()

	if fnout:
#		g.serialize(fnout, format=format)
		g.serialize(fnout+'.'+str(next(splitn)), format=format)

q = """
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX bls-cew: <http://data.bls.gov/data/cew#>
PREFIX bls-cew-onto: <http://data.bls.gov/ont/cew#>
PREFIX usgs-gnis: <http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:>

SELECT DISTINCT ?val ?date ?gnis
WHERE
{
	?uri rdf:type bls-cew-onto:emplvlObservation ;
		bls-cew-onto:gnis ?gnis ;
		bls-cew-onto:industryCode ?naics ;
		bls-cew-onto:ownershipCode ?sic ;
		bls-cew-onto:people ?val ;
		sdmx-dimension:timePeriod ?date .
} ORDER BY ?date ?gnis
"""

def query(g, gnislist, industrylist, ownershiplist=['5']):
	import matplotlib.pyplot as plt
	import datetime
	for gnis,ind,own in itertools.product(gnislist,industrylist,ownershiplist):
		print('doing gnis', gnis)
		gnis_uri = rdflib.URIRef('http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:'+gnis)
		ind_uri = rdflib.URIRef('http://data.census.gov/data/naics/industry#'+ind)
		sic_uri = rdflib.URIRef('http://data.bls.gov/data/sic-own#'+own)
		x, fx = [], []
		for row in g.query(q, initBindings={'gnis': gnis_uri, 'naics': ind_uri, 'sic': sic_uri}):
			print(row['date'], row['val'])
			y,d = str(row['date']).split('-')
			x.append(datetime.date(int(y),int(d),1))
			fx.append(row['val'])
		plt.plot(x,fx)
	plt.show()

def main():
	gnmap = convert_fips2gnis()
#	convert(gnmap, 'raw/2012.q1-q4.singlefile.csv', 'test/2012.ttl', format='turtle')
	convert(gnmap, 'raw/2012.q1-q4.singlefile.csv', 'test/2012.nt', format='nt')
#	g = init()
#	g.parse('test/co.nt', format='nt')
#	g.parse('test/ca.nt', format='nt')
#	g.parse('test/2012.nt.1', format='nt')
#	query(g, ['198131', '2409757'], ['21', '23'])
#	query(g, ['1779775'], ['21', '23'])

if __name__ == '__main__':
	main()

