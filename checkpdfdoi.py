#! /usr/bin/env python

import sys,os,requests,re,glob

############ getfiledoi.py part 
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter

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
doipattern=re.compile("\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")

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

def getfilepossibledoi(fname):
	'''Get possible doi (list) from first page
	If not found, return []'''
	outs=GetFirstPage(fname)
	return doipattern.findall(outs)

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

####### End getfiledoi.py part #############


pdoiwebt=re.compile(r"<title>.*?</title>")
#pdoiweba=re.compile(r'(?<=<a href=")http.*?(?=">)')
def checkdoiweb(doi):
	'''Check whether valid doi by doi.org'''
	doi=doi.strip().lower()
	if (doi.find("10.")!=0):
		return False
	link="http://dx.doi.org/"+doi
	r=requests.get(link,allow_redirects=False)
	title=pdoiwebt.search(r.text).group().lower()
	if ("redirect" in title):
		return True
	return False


if __name__=="__main__":
	if (not os.path.exists("FailDOI")): os.makedirs("FailDOI")
	if (not os.path.exists("FailDOI/Unknown")): os.makedirs("FailDOI/Unknown")
	if (not os.path.exists("Done")): os.makedirs("Done")
	fglob=glob.iglob("10.*.pdf")
	for fname in fglob:
		fnamelist=os.path.splitext(fname)
		doi=fnamelist[0].replace('@','/').lower()
		#check rational doi
		if (not checkdoiweb(doi)):
			print "Error: Fail DOI: "+doi
			os.renames(fname,"FailDOI/"+fname)
			continue
		#check doi in file
		finddoi=getfilepossibledoi(fname)
		if (not doi in finddoi):
			print "Error: Fail find DOI "+doi+" in PDF: "+str(finddoi)
			os.renames(fname,"FailDOI/Unknown/"+fname)
		else:
			os.renames(fname,"Done/"+fname)