#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys,gc,glob
import re,difflib,time,random,copy

from oapdf.pdfhandler import PDFHandler
from oapdf.doi import DOI

def similarsize(s1,s2):
	i1=int(s1)
	i2=int(s2)
	if (i1 == i2):
		return 0
	if (abs(i1-i2)/float(min(i1,i2)) < 0.1):
		return 1
	else:
		return -1

if (not os.path.exists('Done')):
	os.makedirs('Done')

ph=PDFHandler()

nocheckpdf=False

targetdir='.'
workingdir=os.path.abspath('.')
if (len(sys.argv)>=2):
	nocheckpdf=True
	targetdir=sys.argv[1]

for fg in glob.iglob(targetdir+os.sep+'10.*.pdf'):
	fnamesplit=os.path.split(fg)
	doi=DOI(os.path.splitext(fnamesplit[1])[0])

	if (doi):
		fpath=fg.strip().split('@',1)
		fsize=os.path.getsize(fg)
		fname='Decoy/'+doi.prefix+os.sep+fnamesplit[1]
		printout=""
		if (not os.path.exists(fname)):
			if (nocheckpdf or ph.FastCheck(fg)):
				targetfname='Done'+os.sep+fnamesplit[1]
				try:
					os.renames(fg,targetfname)
				except:
					if (os.path.exists(targetfname)):
						if (similarsize(fsize,os.path.getsize(targetfname))>=0):
							os.remove(fg)
					else:					
						print "Move fail...",fg
			else:
				print 'File maybe wrong..',fg
		else:
			f=open(fname)
			for line in f:
				s=similarsize(fsize,line.strip())
				if ( s >= 0):
					os.remove(fg)
					printout=""
					break
				#elif ( s is 1 and int(fsize)<int(line.strip())):
				#	os.remove(fg)
				#	printout=""
				#	break				
				else:
					printout=fg+" now size: "+str(fsize)+"; in lib: "+line.strip()
			if (printout): print printout
			f.close()
	else:
		print "File is not in doi style!",fg

raw_input("Any key to End..")
