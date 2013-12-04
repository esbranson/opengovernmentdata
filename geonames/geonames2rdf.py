#!/usr/bin/python3 -uW all

# http://geonames.usgs.gov/domestic/download_data.htm

import csv
import rdflib

gnis_ns = rdflib.Namespace("http://data.example.com/usgs.gov/data/gnis#")
#gnis_ns = rdflib.Namespace("http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:3:::NO::P3_FID:")
gnisgeo_ns = rdflib.Namespace('http://data.example.com/usgs.gov/data/geom#')
gnisonto_ns = rdflib.Namespace('http://data.example.com/usgs.gov/onto/geonames#')
geo_ns = rdflib.Namespace('http://www.opengis.net/ont/geosparql#')

geofeat = geo_ns['Feature']
geohasgeom = geo_ns['hasGeometry']
geogeom = geo_ns['Geometry']
geoaswkt = geo_ns['asWKT']
geowkt = geo_ns['wktLiteral']
geowithin = geo_ns['sfWithin']
gnisfeat = gnisonto_ns['GeonameFeature']
gnisname = gnisonto_ns['name']
gnisfid = gnisonto_ns['fid']
gnisfips55plc = gnisonto_ns['fips55place']
gnisfips55cls = gnisonto_ns['fips55class']
gnisfips5_2n = gnisonto_ns['fips5-2num']
gnisfips5_2a = gnisonto_ns['fips5-2alpha']
gnisfips6_4 = gnisonto_ns['fips6-4']
gnisgsa = gnisonto_ns['gsa']
gnisopm = gnisonto_ns['opm']

def graph_init():
	g = rdflib.Graph()
	g.bind('geo', geo_ns)
	g.bind('geonames-onto', gnisonto_ns)
	g.bind('geonames', gnisgeo_ns)
	return g

def convert_fips2gnis(infn):
	f = open(infn)
	csv_reader = csv.reader(f, delimiter='|')
	g = graph_init()

	# skip header
	next(csv_reader)

	# parse
	gnmap = {}
	for row in csv_reader:
		fid = row[0]
		typ = row[1]
		fips_c = row[2]
		fips_sn = row[4]
		fips_sa = row[5]
		fips_s_name = row[6]
		fips_s_lname = row[9]
#		print('gnmap', gnis, typ, fips_s, fips_c)
		gnmap[(typ,fips_sn,fips_c)] = fid
		if typ == 'STATE':
			furl = gnis_ns[fid]
			g.add((furl, rdflib.RDF.type, gnisfeat))
#			g.add((furl, rdflib.RDF.type, geofeat)) # XXX make implied through entailment?
			g.add((furl, rdflib.RDFS.label, rdflib.Literal(fips_s_name)))
			g.add((furl, gnisname, rdflib.Literal(fips_s_lname, datatype=rdflib.XSD.string)))
			g.add((furl, gnisfid, rdflib.Literal(fid, datatype=rdflib.XSD.string)))
			g.add((furl, gnisfips5_2a, rdflib.Literal(fips_sa, datatype=rdflib.XSD.string)))
			g.add((furl, gnisfips5_2n, rdflib.Literal(fips_sn, datatype=rdflib.XSD.string)))

	f.close()

	return g, gnmap

# give 2 digit state + 3 digit county fips, return gnis
def search_fips2gnis_county(gnmap, fips_s, fips_c):
	return gnmap[('COUNTY', fips_s, fips_c)] # XXX KeyError

# give 2 digit state fips, return gnis
def search_fips2gnis_state(gnmap, fips_s):
	return gnmap[('STATE', fips_s, '')] # XXX KeyError

def convert_fedcodes(g, f2g, infn, outfn, fmt='turtle'):
	f = open(infn)
	csv_reader = csv.reader(f, delimiter='|')

	# skip headers
	next(csv_reader)

	# convert
#	g = graph_init()
	for n,row in enumerate(csv_reader, 1):
		fid = row[0]
		name = row[1]
		cls = row[2] # http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:8:4151779970585687
		fips55plc = row[3]
		fips55cls = row[4] # http://geonames.usgs.gov/pls/gnispublic/f?p=gnispq:6:447020433485622
		gsa = row[5]
		opm = row[6]
		fips5_2n = row[7]
		fips5_2a = row[8]
		seq = row[9]
		fips6_4 = row[10]
		# county_name = row[11]
		prim_lat = row[12] # Decimal degrees, NAD 83
		prim_long = row[13] # Decimal degrees, NAD 83

		if cls not in {'Civil', 'Census', 'Populated Place'}:
			continue

		furl = gnis_ns[fid]
#		gurl = gnisgeo_ns['geoname_'+fid+'_geom']
		wkt = 'POINT ('+prim_long+' '+prim_lat+')'

#		print(fid,fips55cls,repr(wkt),name)

		g.add((furl, rdflib.RDF.type, gnisfeat))
#		g.add((furl, rdflib.RDF.type, geofeat)) # XXX make implied through entailment?
		g.add((furl, rdflib.RDFS.label, rdflib.Literal(name)))
		g.add((furl, gnisname, rdflib.Literal(name, datatype=rdflib.XSD.string)))
		g.add((furl, gnisfid, rdflib.Literal(fid, datatype=rdflib.XSD.string)))
		if len(fips55plc):
			g.add((furl, gnisfips55plc, rdflib.Literal(fips55plc, datatype=rdflib.XSD.string)))
		if len(fips55cls):
			g.add((furl, gnisfips55cls, rdflib.Literal(fips55cls, datatype=rdflib.XSD.string)))
		if len(gsa):
			g.add((furl, gnisgsa, rdflib.Literal(gsa, datatype=rdflib.XSD.string)))
		if len(opm):
			g.add((furl, gnisopm, rdflib.Literal(opm, datatype=rdflib.XSD.string)))
		if len(fips55cls) and (fips55cls[0] == 'H' or fips55cls == 'C7'): # if its a county or not within a county
			state_gnis = search_fips2gnis_state(f2g, fips5_2n)
			g.add((furl, geowithin, gnis_ns[state_gnis]))
			if len(fips6_4):
				g.add((furl, gnisfips6_4, rdflib.Literal(fips6_4, datatype=rdflib.XSD.string)))
		else:
			county_gnis = search_fips2gnis_county(f2g, fips5_2n, fips6_4)
			g.add((furl, geowithin, gnis_ns[county_gnis]))

#		g.add((furl, geohasgeom, gurl))
#
#		g.add((gurl, rdflib.RDF.type, geogeom))
#		g.add((gurl, geoaswkt, rdflib.Literal(wkt, datatype=geowkt)))

		if n % 1000 == 0:
			print('processed', n)

	f.close()

	f = open(outfn, 'xb')
	g.serialize(f, format=fmt)
	f.close()

def main():
	g, f2g = convert_fips2gnis('raw/GOVT_UNITS_20130602.txt')
	convert_fedcodes(g, f2g, 'raw/NationalFedCodes_20130602.txt', 'out/fedcodes_20130602.ttl', 'turtle')

if __name__ == '__main__':
	main()
