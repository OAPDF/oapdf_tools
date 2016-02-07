#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys,gc,glob
import re,difflib,time,random,copy

######## PDFHandle class
# maybe use cStringIO.StringIO instead
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

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
#from cStringIO import StringIO
#from pdfminer.converter import XMLConverter, HTMLConverter
#from pdfminer.pdfdocument import PDFDocument
#from pdfminer.pdfparser import PDFParser
#from pdfminer.pdfdevice import PDFDevice, TagExtractor
#from pdfminer.cmapdb import CMapDB
#from pdfminer.image import ImageWriter

class PDFHandle(object):
	'''A PDF Handle class to read contains'''
	def __init__(self):
		# debug option
		self.setdebug(0)
		#only first page
		self.pagenos=set([0])
		self.pageno = 1
		self.outfp = stdmodel()
		self.codec = 'utf-8'
		self.showpageno = True
		self.scale = 1
		self.password = ''
		self.maxpages = 0
		self.rotation = 0
		self.imagewriter = None
		self.laparams = LAParams()		
	# ResourceManager facilitates reuse of shared resources such as fonts and images so that 
	# large objects are not allocated multiple times.
		#### This will cause some problem when set to default True.
		self.caching = False
		self.rsrcmgr = PDFResourceManager(caching=self.caching)

		# Important Main converter for pdf file
		self.device = TextConverter(self.rsrcmgr, self.outfp, codec=self.codec, 
			laparams=self.laparams, imagewriter=self.imagewriter)

	def setdebug(self,value):
		'''Set Debug Information. Especially when init'''
		# debug option
		self.debug = 0
		PDFResourceManager.debug = self.debug
		PDFPageInterpreter.debug = self.debug
		#PDFDocument.debug = self.debug
		#PDFParser.debug = self.debug
		#CMapDB.debug = self.debug
		#PDFDevice.debug = self.debug	

	def FastCheck(self,fname):
		'''Fast check whether has page one'''
		fp = file(fname, 'rb')
		try:
			for page in PDFPage.get_pages(fp, set([0]), maxpages=1, 
				password=self.password, caching=self.caching, check_extractable=True):
				break
			fp.close()
			return True
		except:
			fp.close()
			print "Error Reading PDF page number..",fname
			return False

	def GetPageNumber(self,fname):
		'''Get total page number of PDF'''
		fp = file(fname, 'rb')
		try:
			pageno=0
			for page in PDFPage.get_pages(fp, set(), maxpages=0, 
				password=self.password, caching=self.caching, check_extractable=True):
				pageno+=1
			fp.close()
			return pageno
		except:
			fp.close()
			print "Error Reading PDF page number.."
			return 0

	def GetSinglePage(self,fname,pageno=1):
		'''Get Single Page contents of PDF, return string
		Default first page'''	
		fp = file(fname, 'rb')
		try:
			interpreter = PDFPageInterpreter(self.rsrcmgr, self.device)
			for page in PDFPage.get_pages(fp, set([pageno-1]), maxpages=self.maxpages, 
				password=self.password, caching=self.caching, check_extractable=True):

				page.rotate = (page.rotate+self.rotation) % 360
				interpreter.process_page(page)
			fp.close()
			outstr=self.outfp.get()
			self.outfp.reset()
			return outstr 
		except:
			fp.close()
			return ""

	def GetPages(self,fname,pagenos=[1]):
		'''Get Several Page contents of PDF, return string
		Default first page'''	
		fp = file(fname, 'rb')
		try:
			interpreter = PDFPageInterpreter(self.rsrcmgr, self.device)

			for page in PDFPage.get_pages(fp, set([i-1 for i in pagenos]), maxpages=self.maxpages, 
				password=self.password, caching=self.caching, check_extractable=True):

				page.rotate = (page.rotate+self.rotation) % 360
				interpreter.process_page(page)
			fp.close()
			outstr=self.outfp.get()
			self.outfp.reset()
			return outstr 
		except:
			fp.close()
			return ""

	def GetAllPages(self,fname):
		'''Get All Page contents of PDF, return string'''	
		fp = file(fname, 'rb')
		try:
			interpreter = PDFPageInterpreter(self.rsrcmgr, self.device)

			for page in PDFPage.get_pages(fp, set(), maxpages=self.maxpages, 
				password=self.password, caching=self.caching, check_extractable=True):

				page.rotate = (page.rotate+self.rotation) % 360
				interpreter.process_page(page)
			fp.close()
			outstr=self.outfp.get()
			self.outfp.reset()
			return outstr 
		except:
			fp.close()
			return ""		


if __name__ == "__main__":
	if (not os.path.exists("Done")):
		os.makedirs("Done")
	ph=PDFHandle()
	for f in glob.iglob("*.pdf"):
		if ph.FastCheck(f) :
			os.renames(f,"Done/"+f)
