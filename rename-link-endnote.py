#! /usr/bin/env python
import sys,os,re,requests,difflib


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
	try:
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
	except:
		return ""

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


def doidiff(doi1, doi2):
	return difflib.SequenceMatcher(None, doi1, doi2).ratio()

######### Start working #########

# Read xml
fin=open(sys.argv[1])
text=fin.read()
fin.close()

fins=os.path.splitext(sys.argv[1])
fwxml=open(fins[0]+"_new"+fins[1],'w')

# Get information from xml
precord=re.compile(r"<record>.*?</record>")
pdoi=re.compile(r"(?<=<electronic-resource-num>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</electronic-resource-num>)")
ppdflink=re.compile(r"(?<=<pdf-urls><url>internal-pdf://)(?P<inner>.*?)(?=</url></pdf-urls>)")
datapath=re.search(r'(?<=<database)(?:.*?)(?<=path=")(?P<inner>.*?)(?=">)',text).group("inner")

startpart=re.search(r"<\?xml.*?<records>",text).group()
endpart="</records></xml>"
fwxml.write(startpart)

# Get the location of library saving pdf
datapath=datapath.replace('\\','\\\\')
datapaths=os.path.splitext(datapath);
pdfdir=datapaths[0]+".Data/PDF/"

# Valid from doi website

ptdoi=re.compile(r"<title>.*?</title>")
pldoi=re.compile(r'(?<=<a href=")http.*?(?=">)')

# Do with each record
for it in precord.finditer(text):
	fdoi=doixml=pdflink=""
	record=it.group()

	mdoi=pdoi.search(record)
	if (mdoi):
		doixml = mdoi.group("inner").lower().strip()
		dxml = doipattern.search(doixml)
		if (dxml): doixml= dxml.group()
	mpdflink=ppdflink.search(record)
	if (mpdflink):
		pdflink = mpdflink.group("inner")

	if (pdflink is ""):
		fwxml.write(record)
		continue

	notdoiinfile=False
	# If exist file, parse doi and compare to record doi
	# Only when file doi only one and similar/same to record doi, rename file in next step
	# Else, contain records and don't move file! 
	if (os.path.exists(pdfdir+pdflink)):
		#fdoi=getfiledoi(pdfdir+pdflink).lower();
		fdois=[ x.lower() for x in getfilepossibledoi(pdfdir+pdflink) ]
		if (not fdois and doixml is ""):
			print "Record DOI for "+pdflink+" is blank. Only rewrite record."
			fwxml.write(record)
			continue;
		elif (not fdois and doixml is not ""):
			print "File DOI for "+pdflink+" is blank. Use record doi "+doixml
			notdoiinfile=True
			#fwxml.write(record);continue;
		# doixml!="", find fdois
		else:
			if (doixml is "" ):
				if (len(fdois) is 1):
					print "Error Blank Record Doi, Use file doi: "+fdois[0]
					record=pdoi.sub(fdois[0],record)
					doixml=fdois[0]
				elif (len(fdois) >1):
					print "Error Blank Record Doi, too much file dois: "+str(fdois)
					fwxml.write(record);continue;
			elif (doixml not in fdois):
				if (len(fdois) is 1 and doidiff(fdois[0],doixml) >0.85 ):
					print "Error Record Doi "+doixml+", Use file doi: "+fdois[0]
					record=pdoi.sub(fdois[0],record)
					doixml=fdois[0]
				elif (len(fdois) is 1):
					print "Error Record Doi "+doixml+", but too different to file doi: "+fdois[0]
					fwxml.write(record);continue;
				else:
					print "Error Record Doi "+doixml+",too much file dois: "+str(fdois)
					fwxml.write(record);continue;

	# if doixml not blank, validate it in dx.doi.org
	doiweblink="http://dx.doi.org/"+doixml.strip()
	try:
		r=requests.get(doiweblink,allow_redirects=False)
		if (r.status_code is 404):
			print "Error doi link to dx.doi.org for "+doixml+" , Only rewrite record."
			fwxml.write(record)
			continue;
	except:
		fwxml.write(record)
		continue

	#dois=doixml.strip().split('/',1)
	## some doi has / in doi name...
	newdoi=doixml.replace("/","@")
	newlink=newdoi+".pdf"
	if (notdoiinfile): newlink="recorddoi/"+newlink

	# if valid doi move file
	try:
		if (os.path.exists(pdfdir+pdflink)): 
			if (pdflink != newlink and not os.path.exists(pdfdir+newlink)):
				os.renames(pdfdir+pdflink,pdfdir+newlink)
				fwxml.write(ppdflink.sub(newlink,record))
				continue
		# have been move before
		#elif (not os.path.exists(pdfdir+pdflink) and os.path.exists(pdfdir+newlink)):
		elif (os.path.exists(pdfdir+newlink)):
			print "Maybe "+pdflink+" have been moved to "+newlink
		else:
			#???? Have not found. ??? Rewrite...
			print "Can't find file: "+pdfdir+pdflink
		#use origin record
		fwxml.write(record)
	except:
		fwxml.write(record)
		continue

fwxml.write(endpart)
fwxml.close()