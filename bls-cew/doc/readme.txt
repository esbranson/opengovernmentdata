readme.txt                                              Revised June 27, 2013




             QUARTERLY CENSUS OF EMPLOYMENT AND WAGES PROGRAM        
                              (QCEW PROGRAM)   
                                        
                        ** FTP DATA FILES OVERVIEW **                       
                      




    - TABLE OF CONTENTS -
    


    SECTION 1: PUBLICATION UPDATES AND CHANGES......Descriptions of changes and 
                                                    updates related to data files
                                                    published by the QCEW program.


    SECTION 2: PUBLICATION HISTORY..................Historical list summarizing 
                                                    QCEW's data-file activity.
                                                    Starting with the most recent
                                                    publication activity.

    SECTION 3: FILES AND FOLDER STRUCTURE...........General description of files,
                                                    formats, folder structure,
                                                    and zip-archive contents.


    Contact the QCEW Program:
    
         Web-mail: http://data.bls.gov/cgi-bin/forms/cew?/cew/home.htm
            Phone: (202)-691-6567








***********************************************************************************

    SECTION 1: PUBLICATION UPDATES AND CHANGES

***********************************************************************************


This section briefly describes updates and changes to files representing  
Quarterly Census of Employment and Wages (QCEW) data.  Updates are posted 
chronologically from newest to oldest.


-----------------------------------------------------------------------------------
- SEP 2011 -  

On September 29, 2011, the QCEW program released initial, first quarter 2011 data
and revised 2010 data.

QCEW data for 2011 and later are classified according to the 2012 version of the 
North American Industry Classification System (NAICS).  QCEW data from 2007 through 
2010 are classified according to the 2007 version of NAICS. QCEW data from 1990 
through 2006 are classified according to the 2002 version of NAICS.  

The 2012 update to the North American Industry Classification System (NAICS) 
contained a substantial number of changes. This update included more changes than 
the previous NAICS 2007 update. However, like the 2007 revision, the vast majority 
of industries were unchanged with regard to content, code, or title.  NAICS 2012 
changes include: the breakout of industries from the prior definitions; the 
collapse or combining of industries from the prior definitions; the movement of 
scope of activity from one industry to another; the assignment of new industry 
codes; and changing the titles of industries.

The QCEW program has prepared an updated industry title file, industry.map,
to reflect the NAICS 2012 industry codes and titles. The file includes industry 
codes and titles for the NAICS 2007 and NAICS 2002 codes that are not part of 
NAICS 2012.  Those title records are listed in the file as "NAICS07" and 
"NAICS02" records respectively.  Users will generally be able to use this 
title file for NAICS-based QCEW data.

In addition to releasing data, the QCEW program made changes to the structure of
the FTP folders containing historical NAICS and SIC data. In prior releases, NAICS 
data files were contained in area-based sub-directories residing in a parent 
directory for a given year. To simplify archiving these historical data files, 
each of the area-based sub-directories containing ENB files are now contained in 
one annual zip-archive. These new zip-archives conform to the following naming 
convention: "YEAR.all.enb.zip" where YEAR represents a given year of data. For 
example, ENB data files for 1990 are stored in the 1990 directory in the zip-archive
named "1990.all.enb.zip" 

The high-level county files are contained in a separate zip-archive that conforms 
to the following naming convention: "YEAR.all.county_high_level.zip" where YEAR 
represents a given year of data. For example, high-level county files for 1990 
are stored in the 1990 directory in the zip-archive named
"1990.all.county_high_level.zip"

This simplified zip-archive structure has been applied to all years of data. 
However, as a convenience to data users, the current- and prior-year directories
have both the new zip-archive files as well as files stored in the old, area-based
sub-directory layout. 

When the most recent year does not have all quarters available, END flat files 
will be present in a single archive instead of ENB files. For example, for first
quarter 2011, END flat files are stored in a zip archive named "2011.q1-q1.end.zip" 
Note that the "q1-q1" portion of the zip archive's name represents the range of 
quarters contained within. So, if the latest quarter of data available were third 
quarter 2011, the zip archive would be named "2011.q1-q3.end.zip" where "q1-q3" 
represents the three quarters of END files contained within the zip-archive. The 
same quarterly designation is used with the high-level county files. 
(EX: 2011.q1-q3.hlcn.zip) 

The historical SIC data within the SIC directory, in the sub-directories
1997 through 2000 have been archived by year using the following naming 
convention: "sic.YEAR.all.ewb.zip" where YEAR represents the corresponding year. 


-----------------------------------------------------------------------------------
- JUN 2011 -

On June 30, 2011, along with the initial release of fourth quarter 2010 data,
the QCEW program released updated versions of the county high level files spanning
1990 through 2010. In addition to extending the time span, several other changes 
were introduced. For past quarterly releases, the QCEW program published 
these high-level county data in a single Excel file and in files separated by 
State. Starting with the June 2011 release, only the quarterly all-county files 
(up to four) and the annual all-county file will be available for a given year.
Files separated by State will no longer be available.

The county high level files now contain location quotients (LQs) in both the
quarterly and annual files. Quarterly files have LQs for the quarter's third month
of employment and the quarter's total quarterly wages. Annual files have LQs for 
the year's annual average employment and the year's annual total wages. These LQs 
are calculated based on total covered employment in all ownership sectors.  
In past releases, the LQs were calculated only for private industry levels and 
were based on total private employment and total private wages.  Since the LQs now
use base values derived from all ownerships and all industries, the files now have
LQs calculated for each ownership total.


-----------------------------------------------------------------------------------
- OCT 2010 -

On October 19, 2010, along with the initial release of first quarter 2010 data, 
the QCEW program released a beta version of CSV files containing QCEW data from 
1990 forward. Data in these new files were taken from existing ENB and END files. 
These new CSV files can be found on the FTP site here: 
ftp://ftp.bls.gov/pub/special.requests/cew/beta/  For more information regarding 
file-naming conventions and layouts please see the beta/readme.txt located here: 
ftp://ftp.bls.gov/pub/special.requests/cew/beta/readme.txt These beta formats and 
tools are not finalized.  Please send comments and suggestions to QCEWInfo@bls.gov.


-----------------------------------------------------------------------------------
- OCT 2009 -

On October 16, 2009, along with the initial release of first quarter 2009 data, an 
additional Excel formatting macro was uploaded to the FTP site within the DOCUMENT 
folder. A zip file named importxls.zip includes a workbook (importxls.xls) 
containing the formatting macro and a text file (readme.txt) containing the 
formatter's instructions. Unlike the makexls.xls formatting macro, this macro will 
handle data files that are too large for a single worksheet by creating additional
worksheets within the workbook to hold the extra data. In addition, the makexls.xls
macro has been updated to account for the larger worksheet row limit for users 
running Excel version 2007 or later, while still supporting earlier versions. 


-----------------------------------------------------------------------------------
- JUL 2009 -

In July 2009, the high-level county files were updated to include location 
quotients (LQs). Two location quotients columns were added to the annual average 
high level county files.  One was an employment LQ, and the second was a total wage
LQ.  These location quotients were calculated as a comparison of the percent of 
private sector activity (employment or total wages) in the particular industry of 
that row compared to the percent of private sector activity that same industry 
comprised of U.S. total private activity.  Additional information on QCEW data and 
location quotients can be found at: www.bls.gov/help/def/lq.htm.


-----------------------------------------------------------------------------------
- APR 2009 -

There were a number of changes to the high-level county files and folders. 
An April 2009 change included, in each folder, a single file that contained data 
for all counties in the country, each split into two Excel worksheets.  The first 
worksheet contains data for counties within the 50 states and the District of 
Columbia.  The second contains data for Puerto Rico and the Virgin Islands, rather 
than as archives of individual state files. Additional information on QCEW data and 
location quotients can be found at: www.bls.gov/help/def/lq.htm.


-----------------------------------------------------------------------------------
- JAN 2008 -

In January 2008, the QCEW program began releasing pre-formatted Excel files with 
data for the period beginning with first quarter 2007. These files contain top 
level industry aggregates for the nation, statewide, and for every county in the
country.  The zipped Excel files are stored in directories named 'county_high_level'
within the data directory for their year.  In that first iteration, the files were 
zipped both as individual files, and together representing a quarterly archive.  
They include labeled column headers and titles corresponding to area and industry 
codes.


-----------------------------------------------------------------------------------
- OCT 2007 -

In October 2007, the QCEW program released revised 2006 data and initial first 
quarter 2007 data. QCEW data classified according to the 2007 version of the North 
American Industry Classification System (NAICS), were released for the first time,
covering data from 2007 forward. The NAICS coded QCEW data 2006 and earlier periods 
were classified according to the 2002 version of NAICS.  The 2007 version update to 
NAICS was a relatively minor revision -- the vast majority of industries were 
unchanged with regard to content, code, or title.  NAICS 2007 did introduce a small 
number of substantive changes. These changes include: the breakout of industries 
from the prior definitions; the collapse or combining of industries from the prior 
definitions; the movement of scope of activity from one industry to another; the
assignment of new industry codes; and changing the titles of industries.  For the 
users of the QCEW data files described here, we have prepared an updated industry 
title file, industry.map, with NAICS 2007 industry codes and titles. That file 
included industry codes and titles for the small number of NAICS 2002 codes that 
are not part of NAICS 2007. Those title records were listed in the file as 
"NAICS02" records.  Users can generally use this title file for both pre 2007 
QCEW data and for 2007 and later data.  


-----------------------------------------------------------------------------------
- OCT 2004 -

Beginning in October 2004, the new Metropolitan Statistical Area (MSA) 
definitions( OMB No.03-04 and update No.04-03), and the related Core Based 
Statistical Area (CBSA) definitions of Micropolitan Statistical Areas (MicroSA) 
and Combined Statistical Areas (CSA) have become standard area definitions in the
Quarterly Census of Employment and Wages (QCEW) program.  Previously released QCEW 
NAICS data files based on the old MSA definitions have been moved to an archival 
folder called oldmsa.

The following are web site addresses for the OMB bulletins regarding the June 2003 
MSA definitions, and the February and March 2004 revisions to those definitions.
http://www.whitehouse.gov/omb/bulletins_b03-04
http://www.whitehouse.gov/omb/bulletins_fy04_b04-03/


-----------------------------------------------------------------------------------
- SEP 2004 -

In September 2004, BLS released additional years of reconstructed, NAICS-based
data. Data for 1990 through 1997 were released at different times in September
2004.  The reconstructed data is similar in scope and coverage to the 2001-forward 
NAICS data. The reconstructed MSA data is based on the revised Metropolitan Area 
definitions announced by OMB in February and March of 2004.  No old MSA definition 
data will be produced for inclusion with the 1990-2000 reconstructed NAICS basis 
data files. Also, BLS updated the names of files representing 1998 and 1999 
reconstructed NAICS-based data to conform to the BLS convention of not using 
uppercase letters in file names posted on the BLS Web site. 

The 2002 and 2003 data files of previously released research series on the new 
MSA definitions for the year 2002 have become the official files reported here.
Their file names and contents have not changed, but their location in the file 
directory structure has changed to reflect their official status.  The 
corresponding files of 2003 data were removed, and updated files for the same 
period have been released in order to reflect the scheduled October 2004 release 
of revised 2003 data.  Note that the data for 2002 and 2003 for three special area
aggregations: the aggregation of  all MSAs;the aggregation of all CSAs (formerly 
of all CMSAs); and, the aggregation of all non-MSA counties, have been revised 
to reflect the new official area definitions.  


-----------------------------------------------------------------------------------
- JULY 2004 -

In July 2004, BLS released additional years of reconstructed, NAICS-based data. 
Data for 1998 and 1999 were released in July.  The reconstructed data is similar 
in scope and coverage to the 2001-forward NAICS data. The reconstructed MSA data 
is based on the revised Metropolitan Area definitions announced by OMB in February 
and March of 2004.  No old MSA definition data will be produced for inclusion with 
the 1990-2000 reconstructed NAICS basis data files.


-----------------------------------------------------------------------------------
- MAY 2004 -

In May 2004, BLS began the release of reconstructed NAICS based data.  Data for 
2000 were released in May 2004.  The reconstructed data is similar in scope 
and coverage to the 2001-forward NAICS data. The reconstructed MSA data is based 
on the revised Metropolitan Area definitions announced by OMB in February and 
March of 2004.  No old MSA definition data will be produced for inclusion with 
the 1990-2000 reconstructed NAICS basis data files. 

The 2001, 2002, and 2003 MSA data available from the QCEW program are now 
classified under the March 2004 (New) MSA definitions.  These are the same 
definitions as has been used for the data for 2004 released in 2004 and for the 
reconstructed historic NAICS based data for the years 1990 to 2000.  Only a few 
MSAs defined in the June 2003 definitions were affected by the February and March 
2004 definition changes.  Significantly more MicroSAs and CSAs were affected by 
those definition changes.

The following are web site addresses for the OMB bulletins regarding the June 2003 
MSA definitions, and the February and March 2004 revisions to those definitions.
http://www.whitehouse.gov/omb/bulletins_b03-04
http://www.whitehouse.gov/omb/bulletins_fy04_b04-03/


-----------------------------------------------------------------------------------
- SEP 2003 -

In September 2003, BLS began the release of research series data based on the new 
Metropolitan Statistical Area (MSA) definitions released by the Office of 
Management and Budget (OMB) in June of 2003 (these definitions were updated in 
February and March of 2004).  These research series data were released for 
reference years 2002 and 2003.

The following are web site addresses for the OMB bulletins regarding the June 2003 
MSA definitions, and the February and March 2004 revisions to those definitions.
http://www.whitehouse.gov/omb/bulletins_b03-04
http://www.whitehouse.gov/omb/bulletins_fy04_b04-03/


-----------------------------------------------------------------------------------
- JAN 2003 -

In January 2003, files correlated to the quarterly news releases were introduced 
to this directory.  These files were in a new format and had an extension of .ENC. 
As of November 2003, those files have been removed, and, a new format developed,
one with an extension of .END.  This new format, as well as the .ENB format, still
in use, are described in the layout.txt document.  Files in the .END format, a 
single quarter format will only be made available for data years for which 
complete year .ENB files have not been released.  


-----------------------------------------------------------------------------------
- OCT 2002 -

In October 2002, BLS released files of preliminary 2001 data.  At that time, the 
file directory structure was revised because of the NAICS introduction, but the 
1997 to 2000 data based on the 1987 Standard Industrial Classification System were
not revised.  Users of the SIC based data will note a broad similarity between the 
NAICS based files, and their structures and formats.  The file extension .ENB is 
used to distinguish between NAICS based files, which use that extension, and the 
extension .EWB which is used with SIC based files.  Users are cautioned to remember 
to use the appropriate industry code file for the data they are using.


-----------------------------------------------------------------------------------












***********************************************************************************

    SECTION 2: PUBLICATION HISTORY

***********************************************************************************


----------+---------------+--------------------------------------------------------
Month-Year| Publication   | Publication Information
          | Year-Qtr      |
----------+---------------+--------------------------------------------------------
          |               |
          |               |
JUN 2013  | 2011-4 *NEW*  | Revised first, second, and third quarter 2012, and
          |               | initial fourth quarter 2012 and annual average 2012
          |               | data were released. 
          |               |	
MAR 2013  | 2012-3        | Revised first and second quarter 2012 data, and initial 
          |               | third quarter 2012 data were released.
          |               |
JAN 2013  | 2012-2        | Released revised first quarter 2012 data, and initial
          |               | second quarter 2012 data.
          |               |
SEP 2012  | 2012-1        | Released final 2011 data. Released initial first 
          |               | quarter 2012.
          |               |
JUN 2012  | 2011-4        | Revised first, second, and third quarter 2011, and
          |               | initial fourth quarter 2011 and annual average 2011 
          |               | data were released. 
          |               |
MAR 2012  | 2011-3        | Revised first and second quarter 2011 data, and initial 
          |               | third quarter 2011 data were released.
          |               |
JAN 2012  | 2011-2        | Released revised first quarter 2011 data, and initial
          |               | second quarter 2011 data.
          |               |
SEP 2011  | 2011-1        | Released final 2010 data. Released initial first 
          |               | quarter 2011 data based on new NAICS 2012 definitions. 
          |               | Simplified the NAICS and SIC historical flat-file 
          |               | archives.
          |               |
JUN 2011  | 2010-4        | Revised first, second, and third quarter 2010, and
          |               | initial fourth quarter 2010 and annual average 2010 
          |               | data were released. Updated versions of the pre-
          |               | formatted Excel files were released covering data 
          |               | from 1990 through 2010.                     
          |               |
MAR 2011  | 2010-3        | Revised first and second quarter 2010, and initial 
          |               | third quarter 2010 data were released.
          |               |
JAN 2011  | 2010-2        | Revised first quarter 2010, and initial second 
          |               | quarter 2010 data were released.
          |               |
OCT 2010  | 2010-1        | Revised 2009 quarterly and annual data were released.  
          |               | Initial first quarter 2010 data were released.
          |               | Beta version of CSV-Formatted QCEW data files released
          |               |
JUL 2010  | 2009-4        | Revised first, second, and third quarter 2009, and 
          |               | initial fourth quarter 2009 and annual average 2009 
          |               | data were released.                    
          |               |
APR 2010  | 2009-3        | Revised first and second quarter 2009, and initial 
          |               | third quarter 2009 data were released.
          |               |
JAN 2010  | 2009-2        | Revised first quarter 2009, and initial second quarter
          |               | 2009 data were released.
          |               |
OCT 2009  | 2009-1        | 2007 high-level county Excel files were converted to
          |               | the  conventions introduced in July 2009 for the 2008 
          |               | files. Revised 2008 quarterly and annual data were 
          |               | released. Initial first quarter 2009 data were 
          |               | released. An additional Excel formatting macro 
          |               | importxls.xls was released.
          |               |
JUL 2009  | 2008-4        | Revised first, second, and third quarter 2008, and 
          |               | initial fourth quarter 2008 and annual average 2008 
          |               | data were released.  Annual average high-level county 
          |               | Excel files expanded to include two location quotient 
          |               | fields. 
          |               |
APR 2009  | 2008-3        | Revised first and second quarter 2008, and initial 
          |               | third quarter 2008 data were released. A new, high-
          |               | level county Excel file containing all high-level 
          |               | state and county data for third quarter 2008 was 
          |               | released. This new file replaces the zipped collection 
          |               | of state-based high-level county files. 
          |               |
JAN 2009  | 2008-2        | Revised first quarter 2008, and initial second quarter 
          |               | 2008 data were released.
          |               |
OCT 2008  | 2008-1        | Revised 2007 quarterly and annual data were released.  
          |               | Initial first quarter 2008 data were released.
          |               |
JUL 2008  | 2007-4        | Revised first, second, and third quarter 2007, and 
          |               | initial fourth quarter 2007 and annual average 2007 
          |               | data were released.  
          |               |
APR 2008  | 2007-3        | Revised first and second quarter 2007, and initial 
          |               | third quarter 2007 data were released.  
          |               |
JAN 2008  | 2007-2        | Revised first quarter 2007, and initial second 
          |               | quarter 2007 data were released. New, pre-formatted 
          |               | Excel files were released which contain high-level 
          |               | state and county level data.
          |               |
OCT 2007  | 2007-1        | Revised 2006 quarterly and annual data were released.  
          |               | Initial first quarter 2007 data were released.
          |               |
JUL 2007  | 2006-4        | Revised first, second, and third quarter 2006, and 
          |               | initial fourth quarter 2006 and annual average 2006 
          |               | data were released. 
          |               |
APR 2007  | 2006-3        | Revised first and second quarter 2006, and initial
          |               | third quarter 2006 data were released.                              
          |               |
JAN 2007  | 2006-2        | Revised first quarter 2006, and initial second quarter
          |               | 2006 data were released.  
          |               |
OCT 2006  | 2006-1        | Revised 2005 quarterly and annual data were released.  
          |               | Initial first quarter 2006 data were released.
          |               |
JUL 2006  | 2005-4        | Revised first, second, and third quarter 2005, and 
          |               | initial fourth quarter 2005 and annual average 2004 
          |               | data were released. 
          |               |
APR 2006  | 2005-3        | Revised first and second quarter 2005, and initial 
          |               | third quarter 2005 data were released.                              
          |               | 
JAN 2006  | 2005-2        | Revised first quarter 2005, and initial second quarter
          |               | 2005 data were released.  
          |               |
OCT 2005  | 2005-1        | Revised 2004 quarterly and annual data were released.  
          |               | Initial first quarter 2005 data were released. 
          |               |
JUL 2005  | 2004-4        | Revised first, second, and third quarter 2004, and 
          |               | initial fourth quarter 2004 and annual average 2004
          |               | data were released.  
          |               |
APR 2005  | 2004-3        | Revised first and second quarter 2004, and initial 
          |               | third quarter 2004 data were released.  
          |               |
JAN 2005  | 2004-2        | Revised first quarter 2004, and initial second quarter 
          |               | 2004 data were released.  Data on the New MSA 
          |               | definitions for 2001 were released.  Data for 2002 and 
          |               | 2003 for new MSAs were updated to comply with the March
          |               | 2004 updated new MSA definitions.  As a result, all 
          |               | NAICS based data for MSAs for the period from 1990 
          |               | forward are based on the March 2004 MSA definitions.
          |               |
OCT 2004  | 2004-1        | Revised 2003 quarterly and annual data were released.  
          |               | Initial first quarter 2004 data were released.  New 
          |               | MSA definitions become standard.  Data for 2004 first 
          |               | quarter were released without establishment count 
          |               | suppressions.  This implements a new policy for the 
          |               | QCEW program.
          |               |
SEP 2004  | Reconstructed | 1990 and 1991 quarterly and annual data, reconstructed 
          | NAICS history | NAICS basis, full detail.  Corrected county level 
          |               | files for 1993 and 1995 (some states). New MSA Areas
          |               | only.
          |               |
SEP 2004  | Reconstructed | 1992, 1993, 1994, and 1995 quarterly and annual data, 
          | NAICS history | reconstructed NAICS basis, full detail.  New MSA Areas
          |               | only.
          |               |
SEP 2004  | Reconstructed | 1996 and 1997 quarterly and annual data, reconstructed 
          | NAICS history | NAICS basis, full detail.  New MSA Areas only.
          |               |
SEP 2004  | Reconstructed | 1998 and 1999 quarterly and annual data, file name 
          | NAICS history | changes.
          |               |
JUL 2004  | Reconstructed | 1998 and 1999 quarterly and annual data, reconstructed  
          | NAICS history | NAICS basis, full detail.  New MSA Areas only.
          |               |
JUL 2004  | 2003-4        | 2003 quarterly data (revised) and 2003 annual data, 
          |               | all preliminary, full detail.
          |               |
MAY 2004  | Reconstructed | 2000 quarterly and annual data, reconstructed NAICS 
          | NAICS history | basis, full detail.  New MSA Areas only.
          |               |
APR 2004  | 2003-3        | 2003 quarters 1 & 2 revised, and 2003 quarter 3 data,
          |               | preliminary, full detail.  Subdirectory structure 
          |               | revised.
          |               |
JAN 2004  | 2003-2        | 2003 quarter 1 data revised, and 2003 quarter 2 data,
          |               | preliminary, full detail.
          |               |
          |               |
NOV 2003  | 2003-1        | 2002 quarterly and annual data, revised, and 2003 
          |               | quarter 1 data, preliminary, full detail.
          |               |
SEP 2003  | 2002-4        | 2002 quarterly data (revised) and 2002 annual data, 
          |               | all preliminary, full detail.
          |               | 
JUL 2003  | 2002-4        | 2002 quarters 1, 2, & 3 revised & 2002 quarter 4 
          |               | preliminary (partial detail)
          |               |
APR 2003  | 2002-3        | 2002 quarters 1 & 2 revised & 2002 quarter 3 
          |               | preliminary (partial detail)
          |               |
FEB 2003  | 2002-2        | 2002 quarter 1 revised & 2002 quarter 2 preliminary
          |               | (partial detail)
          |               |
JAN 2003  | 2002-1        | 2002 quarter 1 data (partial detail)
          |               |
NOV 2002  | 2001          | Revised 2001 data
          |               |
OCT 2002  | 2001          | Preliminary 2001 data.
          |               | 
----------+---------------+--------------------------------------------------------








***********************************************************************************

    SECTION 3: FILES AND FOLDER STRUCTURE

***********************************************************************************


The QCEW FTP site has several types of files available which are stored in different 
directories covering data from 1975 forward. This section is broken down into two 
parts. NAICS-based data from 1990 forward is detailed first and the historical SIC-
based data covering 1975 to 2000 is covered second.



-------------------------------------------------------------------------------------
PERIOD COVERED: 1990 - Current

CLASSIFICATION: 2011-Current : 2012 North American Industry Classification System 

                2007-2010    : 2007 North American Industry Classification System 

                2001-2006    : 2002 North American Industry Classification System 
                
                1990-2000    : 2002 North American Industry Classification System 
                               (Reconstructed from 1990-2000 data classified under SIC)

   DESCRIPTION: NAICS-based data from 1990-2000 were reconstructed using SIC-based 
                data from the same period. NAICS 2002 codes were used for the 
                reconstruction. Data from 2001-2006 are based on NAICS 2002. Data 
                from 2007-2010 are based on NAICS 2007. Data from 2011 forward are 
                based on NAICS 2012. 
                
                Data are stored in ENB files, END files, Excel files (.xls), and 
                comma-delimited files (.csv).  All data are available in ENB and 
                CSV files.  Some high-level data are available in pre-formatted Excel 
                files.  In general, data are available for NAICS industries by County, 
                by State, by MSA, by MicroSA, by CSA and for the Nation. Data 
                stratified by establishment size class ("size data") are available for 
                the first quarter of each year.  Data formats and storage locations 
                are detailed below in the section titled "FILE DESCRIPTIONS".

REFERENCE FILES:
    
    Area Code List
    ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/area.map
    ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/area_titles.csv
    
    Industry Code List
    ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/industry.map
    ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/industry_titles.csv
    
    Ownership Code List
    ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/ownershp.map
    ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/ownership_titles.csv
    
    Size Categories
    ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/size.map
    ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/size_titles.csv
    
    Aggregation Level Codes
    ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/agglevel.map
    ftp://ftp.bls.gov/pub/special.requests/cew/beta/titles/agglvl_titles.csv
    
    
    
FILE DESCRIPTIONS:
     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        File Type: County High Level Excel Files (.xls)

      Time Period: 1990-Current
      Area Detail: National, by MSA, by State, by County,
  Industry Detail: Total, Total by Ownership, private sector by Domain, and Supersector.
  
      Unique Data: These files contain Location Quotients (LQ) for third-month employment
                   and total quarterly wages. Location Quotients are also calculated
                   for annual employment and wage data. 
            
             NOTE: The county high-level files are pre-formatted Excel Workbooks.
                   Formatting includes print-layouts, categorical titles,
                   and data display formatting. Microsoft Excel, or an Excel-
                   compatible program is required to use these files.
                   
   Root Directory: ftp://ftp.bls.gov/pub/special.requests/cew/
         
          Storage: From 1990 forward there is a single zip archive for each year that
                   contains all of the available high-level Excel files. When accessing
                   the root directory you will see folders for each year. Each folder 
                   contains, among other things, one zip archive containing the county
                   high-level Excel files. If data exists for an entire year, then there 
                   will be five files contained within the zip archive: One Excel file for 
                   each of the four quarters and one Excel file representing annual 
                   averages. When an entire year's worth of data is present, the zip 
                   archive uses the following naming convention: 
                   [YEAR].all.county_high_level.zip, where "[YEAR]" represents the four-
                   digit year. If only part of a year's data are available then the 
                   quarters available will be present in the file name using the 
                   convention "[YEAR].q1-q[R].county_high_level.zip", where "[YEAR]" 
                   represents the four-digit year and "[R]" represents the most recent 
                   quarter available.   

     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        File Type: BETA Files (Comma-Delimited Files (.CSV) )

      Time Period: 1990-Current
      Area Detail: National, by MSA, by State, by County, by CSA, by MicroSA and by
                   Size. (Size data available for first quarter of each year)
  Industry Detail: Totals, Ownership, Domain, Supersector, NAICS Sector, 
                   NAICS 3-Digit, NAICS 4-Digit, NAICS 5-Digit, and NAICS 6-Digit. 
                   
   Root Directory: ftp://ftp.bls.gov/pub/special.requests/cew/beta/                 
  
          Storage: These files represent a new format under consideration as a 
                   replacement for the current ENB and END file formats. These files 
                   were developed to better serve user requests. Data are stored in zip 
                   archives by area, industry, size, and as a single file. The  
                   "data by area" files provide users with all industry/ownership data 
                   for a given area. The "data by industry" files provide users with all 
                   area/ownership data for a given industry. The "data by size" files 
                   provide all available size data for the first quarter of a reference 
                   year. The "data in single file" files provide users a simple way to 
                   import QCEW data into a database or statistical program. These four 
                   categories, "data by area", "data by industry", "data by size", and 
                   "data in a single file", are stored in zipped archives. With the 
                   exception of the "data in a single file" category, the CSV formatted 
                   files include codes as well as titles on each record. The 
                   "data in a single file" files exclude titles.

                   There are seven zipped archives for each reference year for which 
                   all four quarters of data are available. There are three quarterly 
                   archives and three annual archives. two by area, two by industry and 
                   two single files. There is one size file representing first quarter.
                   If all four quarters of a reference year are not available, there 
                   will be only four zipped archives: quarterly by area, by industry, 
                   and as a single file; and; one size file representing first quarter.
                   For more information on these archives please see the readme.txt file
                   listed below under "Documentation".
   
    Documentation: ftp://ftp.bls.gov/pub/special.requests/cew/beta/readme.txt
     File Layouts: ftp://ftp.bls.gov/pub/special.requests/cew/beta/layouts/quarterly_layout.txt
                   ftp://ftp.bls.gov/pub/special.requests/cew/beta/layouts/annual_layout.txt
  
             NOTE: CSV files typically open directly into Microsoft Excel, and can be
                   easily imported by other statistical and database software.

     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        File Type: ENB/END Files 

      Time Period: 1990-Current
      Area Detail: National, by MSA, by State, by County, by CSA, by MicroSA and by
                   Size. (Size data available for first quarter of each year)
  Industry Detail: Totals, Ownership, Domain, Supersector, NAICS Sector, 
                   NAICS 3-Digit, NAICS 4-Digit, NAICS 5-Digit, and NAICS 6-Digit. 

   Root Directory: ftp://ftp.bls.gov/pub/special.requests/cew/
                   
          Storage: The collection of ENB files are stored in a single zip archive for
                   each year from 1990 forward. When accessing the root directory
                   you will see folders for each year. Each folder contains, among 
                   other things, one zip archive that contains the collection of ENB 
                   files for that year. Zip archives use the following naming 
                   convention: "[YEAR].all.enb.zip" where "[YEAR]" represents the 
                   four-digit year. For example, ENB files for 1998 are stored in 
                   the zip archive named "1998.all.enb.zip" For the two most-recent
                   years, ENB files are also zipped separately and stored in their
                   containing area-detail directories. 
                   
                   If an entire year's worth of data is not yet available, then 
                   you'll see END files published instead of ENB files. END files
                   store data in a quarterly format and are present for the most-recent
                   year if all four of its quarters have yet to be published. Like the
                   ENB files, the collection of END files are stored in a single zip
                   archive for the most recent year. The most current year's folder 
                   will contain, among other things, one zip archive that contains 
                   the collection of END files for the available quarters. These
                   END zip archives use the following naming convention:
                   "[YEAR].q1-q[R].end.zip" where "[YEAR]" represent the four-digit
                   year and "[R]" represents the most-recent quarter of data 
                   available. For example, suppose the most recent quarter of data 
                   available was second quarter 2015. END files would be stored in 
                   the zip archive named "2015.q1-q2.end.zip". For the most-recent 
                   year, END files are also zipped separately and stored in their 
                   corresponding area-detail directories. END files are only present
                   if an entire year of data has yet to be published. 

    Documentation: ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/
     File Layouts: ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/layout.txt
       Converters:
             
             NOTE: Each of the following converters is 
                   zipped along with its instructions.
                   All work for both END and ENB formats.
             
             For Excel
             ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/makexls.zip
             ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/importxls.zip
            
             For Access
             ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/mkaccessXP.zip
             ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/mkaccess97.zip
             
             For SAS
             ftp://ftp.bls.gov/pub/special.requests/cew/DOCUMENT/makesas.zip
             

-------------------------------------------------------------------------------------





-------------------------------------------------------------------------------------
PERIOD COVERED: 1975 - 2000

CLASSIFICATION: Standard Industry Classification System (SIC)
   
   DESCRIPTION: Data based on the Standard Industry Classification system. Data are 
                stored in EWB files and DBF files. Data are available by County,
                by State, by MSA, and for the Nation. Data stratified by establishment 
                size class ("size data") are available for first quarter of each year
                from 1997 through 2000. Data are located in the directories and files 
                detailed below under "FILE DESCRIPTIONS" 

REFERENCE FILES:
    
    SIC Industry Codes 
    ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/industry.map
    
    Area Codes
    ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/area.map

    Ownership Codes
    ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/ownershp.map

    Size Categories
    ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/size.map
    
    
FILE DESCRIPTIONS:

     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        File Type: EWB Files
      Time Period: 1997-2000
      Area Detail: National, by MSA, by State, by County, and by Size.
  Industry Detail: Total, Ownership, SIC Division, 2-digit, 3-digit, and 4-digit SIC  

   Root Directory: ftp://ftp.bls.gov/pub/special.requests/cew/SIC/ 
  
          Storage: The collection of EWB files are stored in a single zip archive for
                   each year from 1997 through 2000. When accessing the root directory
                   you will see folders for each year. Each folder contains one zip 
                   archive that contains the collection of EWB files for that year.
                   Zip archives use the following naming convention: 
                   "sic.[YEAR].all.ewb.zip" where "[YEAR]" represents the four-digit
                   year. For example, EWB files for 1998 are stored in the zip 
                   archive named "sic.1998.all.ewb.zip"
                   
    Documentation: ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/
      File Layout: ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/layout.txt
       Converters:
             
             Instructions
             ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/convertr.txt
             
             For Excel
             ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/makexls.zip
             
             For Access
             ftp://ftp.bls.gov/pub/special.requests/cew/SIC/document/mkaccess.zip

     
     
     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        File Type: DBF Files
      Time Period: 1975-2000
      Area Detail: National, by MSA, by State, by County, and by Size 
                   (Size data available for first quarter of 1997-2000.)
  Industry Detail: Total, Ownership, SIC Division, 2-digit,3-digit, and 4-digit SIC                 

   Root Directory: ftp://ftp.bls.gov/pub/special.requests/cew/SIC/history/                   
                   
          Storage: DBF files are zipped and stored in directories based on the data's 
                   area detail. There are folders for county, metropolitian statistical 
                   areas (metro), state, and national data. Within each of these folders
                   you'll see zipped DBF files representing data for multiple years. The 
                   zipped files have a two-letter prefix denoting their area detail. For 
                   example, county data are stored in zip archives that begin with "ct". 
                   The next six characters represent the time period contained within the
                   DBF. For example, the zip archive "st751814.zip" contains state-wide 
                   data from first quarter 1975 ("751") through fourth quarter 1981.("814")
                   Files with annual averages are labeled with the same two-letter prefix,
                   followed by "aa" to denote annual averages, followed by four digits
                   representing the first and last year in the file. For example, 
                   "msaa8892.zip" contains annual averages for MSAs from 1988 through
                   1992. 
                   
    Documentation: ftp://ftp.bls.gov/pub/special.requests/cew/SIC/history/readme.txt
                   ftp://ftp.bls.gov/pub/special.requests/cew/SIC/history/contents.txt
       Converters: See readme.txt

-------------------------------------------------------------------------------------            
            



