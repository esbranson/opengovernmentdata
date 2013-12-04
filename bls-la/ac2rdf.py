#!/usr/bin/python3 -uW all

import csv
import sys
import re

# http://geonames.usgs.gov/domestic/download_data.htm
def convert_fips2gnis(fn):
	f = open(fn)
	csv_reader = csv.reader(f, delimiter='|')

	# skip header
	next(csv_reader)

	gnlist = []
	for row in csv_reader:
		gnis = row[0]
		name = row[1]
#		clas = row[2] # 'Civil'
#		census_code = row[3] # '99' + county FIPS if county
		census_class = row[4]
		state_fips = row[7]
		county_fips = row[10]
		county = row[11]
		gnlist.append((gnis,name,census_class,state_fips,county_fips,county))

	f.close()
	return gnlist

# give 2 digit state+ 3 digit county fips, return gnis
#def search_codes_county(gnlist, fips_s, fips_c):
def search_fips2gnis_county(gnlist, fips_s, fips_c):
	items = []
	for item in gnlist:
		if item[3] == fips_s and item[4] == fips_c and len(item[2]) and item[2][0] in 'H':
			items.append(item[0])
	if len(items) == 1:
		return items[0]
	elif len(items) > 1:
		print('WARN county mult gnis', fips_s, fips_c, items)
		return items[0]

	# XXX it has cities too
	items = []
	for item in gnlist:
		if item[3] == fips_s and item[4] == fips_c and len(item[2]) and item[2][0] in 'C':
			items.append(item[0])
	if len(items) == 1:
		return items[0]
	elif len(items) > 1:
		print('WARN city mult gnis', fips_s, fips_c, items)
		return items[0]

	return None

# find city, return gnis
def search_fips2gnis_city(gnlist, name, ac, county=None):
	fips_s = ac[2:4]
	allmatches = []
	# find all with that name inside
	for item in gnlist:
		if re.search(name, item[1]) and item[3] == fips_s:
			allmatches.append(item)
	# see if there is only 1 incorporated city
	citymatches = []
	for m in allmatches:
#		if m[2][0] == 'P' or m[2][0] == 'C': #Census Class Codes for cities
		if m[2][0] in {'C','T','Z'}: # Townships, whatever Zs are
			citymatches.append(m)
	if len(citymatches) == 1:
#		print('city', ac, name, citymatches[0][0])
		return citymatches[0][0]
	elif len(citymatches) > 1:
		# county?
		if county:
			# XXX whatif multiple matches?
			for item in citymatches:
				if item[5] == county:
					return item[0]
		# XXX pick shortest name?
		shortest = citymatches[0]
		same = True
		last = citymatches[0][0]
		for m in citymatches[1:]:
			if len(m[1]) < len(shortest[1]):
				shortest = m
#			elif len(m[1]) == len(shortest[1]):
#				print('city wtf samelen', shortest, m)
			if same and m[0] == last: # if theyre all same gnis
				same = True
			else:
				same = False
			last = m[0]
		if not same:
			print('WARN city outof', ac, name, citymatches, 'pick', shortest)
		return shortest[0]
#	if '(' in name:
#		alt = name.split('(')[0].strip()
#		print('city alt', name, alt)
##		return search_codes_city(gnlist, alt, fips_s, ac)
#		return search_fips2gnis_city(gnlist, alt, county, fips_s, ac)
	return None

def convert_area(fn):
#	f = open('raw/la/la.area')
	f = open(fn)
	csv_reader = csv.reader(f, delimiter='\t')

	# skip header
	next(csv_reader)

	arealist = []
	for row in csv_reader:
		ac = row[1]
		name = row[2]
		typ = row[0] # see la.area_type
		arealist.append((ac,name,typ))

	f.close()
	return arealist

##
# Return a normalized (for the NationalFedCodes file) name, along
# with a county (as a tuple) if needed.
#
def convert_areaname2fedcodesname(name):
	# XXX replacements
	name = name.replace('St.', 'Saint')

	# matching
	res = name.split(' city, ')
	if len(res) > 1:
		return 'City of '+res[0]

	res = name.split(' town, ')
	if len(res) > 1:
		return 'Town of '+res[0]

	res = name.split(' town (')
	if len(res) > 1:
		county = res[1].split(' County), ')[0]
		return 'Town of '+res[0], county

	res = name.split(' village, ')
	if len(res) > 1:
		return 'Village of '+res[0]

	res = name.split(' charter township, ')
	if len(res) > 1:
		return 'Charter Township of '+res[0]

	res = name.split(' charter township (')
	if len(res) > 1:
		county = res[1].split(' County), ')[0]
		return 'Charter Township of '+res[0], county

	res = name.split(' township, ')
	if len(res) > 1:
		return 'Township of '+res[0]

	res = name.split(' township (')
	if len(res) > 1:
		county = res[1].split(' County), ')[0]
		return 'Township of '+res[0], county

	res = name.split(' borough, ')
	if len(res) > 1:
		return 'Borough of '+res[0]

	res = name.split(' municipality, ')
	if len(res) > 1:
		return 'Municipality of '+res[0]

	res = name.split(' plantation, ')
	if len(res) > 1:
		return 'Plantation of '+res[0]

	res = name.split(' unorganized, ')
	if len(res) > 1:
		return 'Unorganized Territory of '+res[0]

	res = name.split(' gore, ')
	if len(res) > 1:
		return res[0]+' Gore'

	res = name.split(' grant, ')
	if len(res) > 1:
		return res[0]+' Grant'

	res = name.split(' location, ')
	if len(res) > 1:
		return res[0]+' Location'

	return None

# get LAUS area code <-> county FIPS mappings
def convert_lau2fips(fn):
	f = open(fn)
	csv_reader = csv.reader(f, delimiter='|')

	# skip headers
	for i in range(7):
		next(csv_reader)

	laudic = {}
	try:
		for row in csv_reader:
			ac = row[0].strip()
			fips_s = row[1].strip()
			fips_c = row[2].strip()
			laudic[ac] = (fips_s,fips_c)
	except IndexError: # end of table
		pass

	f.close()
	return laudic

##
# Return a LAUS Area Code to GNIS mapping dictionary.
#
def convert(arealist, laudic, gnlist):
	acgnis = {}
	for (n,(ac,acname,actyp)) in enumerate(arealist, 1):
		# skip dups
		if ac in acgnis:
			continue

		# get FIPS from LAUS area code
		if ac in laudic:
			fips_s,fips_c = laudic[ac]
			gnis = search_fips2gnis_county(gnlist, fips_s, fips_c)
			if gnis:
				acgnis[ac] = gnis
			else:
				print('FAIL county nognis', ac, fips_s, fips_c)
		# else try USGS DB for incorporated places
		elif actyp in {'F', 'G', 'H'}:
			name = convert_areaname2fedcodesname(acname)
			if name and isinstance(name, str):
				gnis = search_fips2gnis_city(gnlist, name, ac)
				if gnis:
					acgnis[ac] = gnis
				else:
					print('FAIL city nognis', ac, repr(name))
			elif name and isinstance(name, tuple):
				name,county = name
				gnis = search_fips2gnis_city(gnlist, name, ac, county)
				if gnis:
					acgnis[ac] = gnis
				else:
					print('FAIL citycounty nognis', ac, repr(name), repr(county))
			else:
				print('FAIL city noname', ac, acname)

		if not n%1000:
			print('INFO matched', n)

	return acgnis

def save_acgnis(acgnis, fn):
	f = open(fn, 'x')
	csv_writer = csv.writer(f, delimiter='\t')
	for k in acgnis:
		csv_writer.writerow((k,acgnis[k]))
	f.close()

usage="""Usage: conv_la_ac.py fedcodesfile areafile countyfile outfile"""

def main():
	if len(sys.argv) != 5:
		print('FAIL: not enough args')
		print(usage)
		sys.exit(1)
	codesfn = sys.argv[1]
	areafn = sys.argv[2]
	countyfn = sys.argv[3]
	outfn = sys.argv[4]

	arealist = convert_area(areafn)
	gnlist = convert_fips2gnis(codesfn)
	laudic = convert_lau2fips(countyfn)
	acgnis = convert(arealist, laudic, gnlist)
	save_acgnis(acgnis, outfn)

if __name__ == '__main__':
	main()

