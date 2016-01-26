#! /usr/bin/env python
# Author: Hom, 2015.12.20
# Purpose: To find the doi number in first page of pdf
# Usage: python script.py pdffile [pdffile2 pdffile3 ...]
#
# Require pdfminer module 
#    To install pdfminer: pip install pdfminer

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter

import sys,os,re

class stdmodel(object):
	'''a class to model stdout for pdfminer file parameter
	Can get context use get() method'''

	# saved string
	_str=""

	def __str__(self):
		return self._str

	def reset(self):
		'''Reset the saved string'''
		self._str=""
	def get(self):
		'''Get the saved string'''
		return self._str

	def write(self,line):
		'''model write method of file'''
		self._str+=line

	def open(self,*args):
		'''model open method of file'''
		self._str=""

	def close(self):
		'''model close method of file'''
		self._str=""

	def read(self):
		'''model read method of file'''
		return self._str

#	def writeline(self,lines):
#		pass
#	def readline(self):
#		pass
#	def readlines(self):
#		pass

####### Setup for pdfminer ############

# debug option
debug = 0
PDFDocument.debug = debug
PDFParser.debug = debug
CMapDB.debug = debug
PDFResourceManager.debug = debug
PDFPageInterpreter.debug = debug
PDFDevice.debug = debug

#only first page
pagenos=set([0])
pageno = 1

#outfp = sys.stdout
outfp = stdmodel()

codec = 'utf-8'
showpageno = True
scale = 1
password = ''
maxpages = 0
rotation = 0
imagewriter = None
laparams = LAParams()

# ResourceManager facilitates reuse of shared resources
# such as fonts and images so that large objects are not
# allocated multiple times.
#### This will cause some problem when set to default True.
caching = False
rsrcmgr = PDFResourceManager(caching=caching)

# Important Main converter for pdf file
device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
                               imagewriter=imagewriter)

####### Functions for read doi ############

def GetFirstPage(fname):
	'''Get First Page contents of PDF, return string'''	
	fp = file(fname, 'rb')
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	for page in PDFPage.get_pages(fp, pagenos,
	                              maxpages=maxpages, password=password,
	                              caching=caching, check_extractable=True):
		page.rotate = (page.rotate+rotation) % 360
		interpreter.process_page(page)
	fp.close()
	outstr=outfp.get()
	outfp.reset()
	return outstr 

# avoid repeat generate doipattern
doipattern=re.compile("\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?!\|[\"&\'<>])\S)+)(?:\+|\\b)")

def getdoi(instr):
	'''Get DOI number of input string'''
	match=doipattern.search(instr)
	if (match):
		return match.group()
	else:
		return ""

def getfiledoi(fname):
	'''Get DOI number from first page of PDF. 
	If not found, return "" '''
	outs=GetFirstPage(fname)
	return getdoi(outs)

def doirenamefile(fname, doi):
	'''Rename file based on doi number'''
	realdoi=getdoi(doi)
	if ( realdoi is not "" ):
		fnames=os.path.split(os.path.abspath(fname))
		newname=realdoi.replace("/","@")+".pdf"
		if (os.path.exists(fnames[0]+os.sep+newname)):
			print 'Same name? for '+fname+" doi: "+realdoi
			return
		os.renames(fname, 
			fnames[0]+os.sep+newname)
	#else don't rename it	

def mainusage():
	'''Print usage'''
	print 'usage: %s [-r] [-d] pdffile ...' % sys.argv[0]
	exit(100)

if __name__=="__main__":
	import getopt
	try:
		(opts, args) = getopt.getopt(sys.argv[1:], 'rd')
	except getopt.GetoptError:
		mainusage()
	if not args: mainusage()

	# -r : rename file
	rename_=False
	# -d : only output doi name
	onlydoi_=False
	for (k, v) in opts:
		if k == '-r': rename_=True
		if k == '-d': onlydoi_=True

	# Perform for each file
	for fname in args:
		#fname=sys.argv[1]
		#fnamelist=os.path.splitext(fname)

		doi=getfiledoi(fname);
		if (rename_):
			doirenamefile(fname,doi)
			if (onlydoi_):
				print doi
		else:
			if (onlydoi_):
				print doi
			else:
				print fname+" "+"Found: "+doi
