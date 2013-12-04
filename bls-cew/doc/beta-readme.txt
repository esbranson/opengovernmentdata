readme.txt                                               Revised June 28, 2012
Covers: QCEW CSV files (BETA)
Folder: ftp://ftp.bls.gov/pub/special.requests/cew/beta/


Starting with the first quarter 2010 release, The QCEW program began
publishing CSV formatted files containing data from 1990 through the 
latest period available. These files represent a new format under 
consideration as a replacement for the current ENB and END file formats. 
These files were developed to better serve user requests. Data are stored 
in zip archives by area, industry, size, and as a single file. Data by 
area provide users with all industry/ownership data for a given area. 
Data by industry provide users with all area/ownership data for a given 
industry. Size data provide all available size data for the first quarter
of a reference year. All data in a single file provide users a simple 
way to import QCEW data into a database or statistical program. These 
four categories, data by area, data by industry, data by size, and data
in a single file, are stored in zipped archives. With the exception of the 
single file, the CSV formatted files include titles as well as codes on 
each record.


-- Location --

These archives are stored in the beta directory located here:
ftp://ftp.bls.gov/pub/special.requests/cew/beta/


-- Folder Structure --

There are seven zipped archives for each reference year for which 
all four quarters of data are available. For Example, for 2001 these
seven archives exist:

    1) 2001.q1-q4.by_area.zip
    2) 2001.q1-q4.by_industry.zip
    3) 2001.q1-q4.singlefile.zip

    4) 2001.annual.by_area.zip
    5) 2001.annual.by_industry.zip
    6) 2001.annual.singlefile.zip

    7) 2001.q1.by_size.zip

If all four quarters of a reference year are not published, there will be
only four zipped archives available. For example, suppose the latest
published data represented data for second quarter 2015. The following 
four archives would be available:

    1) 2015.q1-q2.by_area.zip
    2) 2015.q1-q2.by_industry.zip
    3) 2015.q1-q2.singlefile.zip

    7) 2015.q1.by_size.zip

Note that the annual archives (files 4,5,and 6) are not available 
because the entire year's data are not available. The name of each 
archive will reflect the newest quarter available. For example, 
"2015.q1-q2.by_area.zip" contains "q1-q2" which can be interpreted as 
data for first quarter through second quarter 2015 broken down by area.


-- Quarterly Data --

The first three archives listed above contain quarterly data. Within the
quarterly data files, each record contains data for a single quarter.
Each record contains its identifying codes and titles, (area, ownership, 
industry, size, and aggregation level) and the data for that quarter. 
The single file does not contain titles. File structure details can 
be found here: 
ftp://ftp.bls.gov/pub/special.requests/cew/beta/layouts/quarterly_layout.txt

"2001.q1-q4.by_area.zip"
This archive contains area files that represent 2001 quarterly data. 
The name of this archive reflects the data available. Each area is represented 
in a separate file. Each area file's name starts with year and quarters
it contains, followed by the FIPS code and the title of the area 
itself. For Example, "2001.q1-q4 01000 (Alabama -- Statewide).csv" 
contains every quarterly record at the state level for Alabama for 2001. 

"2001.q1-q4.by_industry.zip" 
This archive contains industry files that represent 2001 quarterly data. 
The name of this archive reflects the data available. Each industry is 
represented  in a separate file. Each industry file's name starts with the 
year and quarters it contains, followed by with the industry code (NAICS) 
and title of the industry itself. For Example:"2001.q1-q4 10 (Total, All 
industries).csv" contains the quarterly totals for every area/ownership 
combination published. And,"2001.q1-q4 31-33 (Manufacturing).csv" contains 
every record published under the NAICS sector Manufacturing. 

"2001.q1-q4.singlefile.zip" 
This archive contains one file representing all quarterly data published 
for 2001. The name of this archive reflects the data available. The file 
name is the same as the zip-archive's name: "2001.q1-q4.singlefile.csv" 
This file is designed with the power-user in mind: Those who wish
to import data into a database or statistical program. Unlike
the "by area" and "by industry" files, this file does not contain
titles, only codes (area, ownership, industry, size, and aggregation 
level) Codes and their corresponding titles can be found at:
ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/


-- Annual Data --

The second three archives contain annual data. Each record 
contains its identifying codes and titles. (area, ownership, industry,
size, and aggregation level) The singlefile does not contain
titles. File structure details can be found here:
ftp://ftp.bls.gov/pub/special.requests/cew/beta/layouts/annual_layout.txt

"2001.annual.by_area.zip"
This archive contains area files that represent 2001 annual data. 
This archive is only present if an entire year's worth of data are 
available. Each area is represented in a  separate file. Each area file's 
name starts with year it contains, followed by the FIPS code and the title 
of the area itself. For Example, "2001.annual 01000 (Alabama -- Statewide).csv" 
contains every annual record for the state of Alabama for 2001. 

"2001.annual.by_industry.zip" 
This archive contains industry files that represent 2001 annual data. 
This archive is only present if an entire year's worth of data are 
available. Each industry is represented in a separate file. Each industry 
file's name starts with the year it contains, followed by with the industry 
code (NAICS) and title of the industry itself. For Example:
"2001.annual 10 (Total, All industries).csv" contains the quarterly
totals for every area/ownership combination published. And,
"2001.annual 31-33 (Manufacturing).csv" contains every record published under
the NAICS sector Manufacturing.

"2001.annual.singlefile.zip"
This archive contains one file representing all annual data published 
for 2001. This archive is only present if an entire year's worth of data 
are available. The file name is the same as the zip-archive's name: 
"2001.annual.singlefile.csv" This file is designed with the power-user in 
mind: Those who wish to import data into a database or statistical program. 
Unlike the "by area" and "by industry" files, this file does not contain
titles, only codes (area, ownership, industry, size, and aggregation 
level) Codes and their corresponding titles can be found at:
ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/


-- Establishment Size Data -- 

The seventh archive represents data organized by establishment size, 
published for the first quarter of each year. Each record contains 
its identifying codes and titles. (area, ownership industry, size, 
and aggregation level) The  naming convention is slightly different 
that other quarterly archives because these data are only published 
in the first quarter of each year. "2001.q1.by_size.zip" holds a 
single file "2001.q1.by_size.csv" which contains all size data published. 
Unlike the other quarterly files, this file contains only first quarter 
records. Each record contains the same fields as the other quarterly 
files. However, there are no second, third, or fourth quarter records. 
The size file's structure is the same as other quarterly files. 
File structure details can be found here:
ftp://ftp.bls.gov/pub/special.requests/cew/beta/layouts/quarterly_layout.txt

For Data organized by firm size, see Business Employment Dynamics (BED)
Here: http://www.bls.gov/bdm/bdmfirmsize.htm









