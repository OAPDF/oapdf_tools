#! /usr/bin/env python
# 2016.1.10
#### Usage:
# put this script in a repository root directory and just run it 
# Move pdf to its prefix dir. 
# If file exists in dir, don't move it

import os,sys,glob

pdffiles=glob.glob("10.*.pdf")
for pdf in pdffiles:
	dois=pdf.split("@",1)
	if (not os.path.exists(dois[0])): 
		os.makedirs(dois[0])
	if (not os.path.exists(dois[0]+os.sep+pdf)):
		os.renames(pdf,dois[0]+os.sep+pdf)