#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

'''Module for DOI and journal record operation
Also include the journal pdf function'''

import os,sys,re,glob
import time,random,gc
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup

try:
	from .doi import DOI
	from .crrecord import CRrecord
	from .basic import normalizeString,strsimilarity,strdiff
except (ImportError,ValueError) as e:
	from doi import DOI
	from crrecord import CRrecord
	from basic import normalizeString,strsimilarity,strdiff

############# Endnote relate libraray ##############

class EndnoteXML(object):
	def __init__(self,fname):
		if (fname):
			f=open(fname)
			self.content=re.sub(r'</?style.*?>','',f.read())
			f.close()
		else:
			self.content=""
		self.soup=BeautifulSoup(self.content,'html.parser')
		self.records=self.soup.records.contents
		self.length=len(self.records)
		
		for i in range(self.length):
			self.checktag(i,'titles')
			self.checktag(i,'authors')
			self.checktag(i,'urls')
			if (self.records[i].find('related-urls') is None):
				self.addtag(i,'related-urls','',parent='urls')
			if (self.records[i].find('pdf-urls') is None):
				self.addtag(i,'pdf-urls','',parent='urls')			
			self.checktag(i,'dates')
			self.setdoi(i,self.getdoi(i))

	#def __repr__(self):
	#	return self.soup.encode()

	def __str__(self):
		return self.soup.encode()

	def reset(self,fname):
		self.__init__(fname)

	def read(self,fname):
		self.__init__(fname)

	def reads(self,s):
		self.content=s
		self.soup=BeautifulSoup(self.content,'html.parser')
		self.records=self.soup.records.contents
		self.length=len(self.records)
		for i in range(self.length):
			self.checktag(i,'titles')
			self.checktag(i,'authors')
			self.checktag(i,'urls')
			if (self.records[i].find('related-urls') is None):
				self.addtag(i,'related-urls','',parent='urls')
			if (self.records[i].find('pdf-urls') is None):
				self.addtag(i,'pdf-urls','',parent='urls')
			self.checktag(i,'dates')
			self.setdoi(i,self.getdoi(i))

	def writes(self,encoding='utf-8'):
		return self.soup.encode(encoding=encoding)

	def write(self,fname,encoding='utf-8'):
		f=open(fname,'w')
		f.write(self.writes(encoding=encoding))
		f.close()

	def getrecord(self,num):
		if (num>=self.length):
			return None
		return self.records[num]

	def checktag(self,num,tag):
		if self.records[num].find(tag) is None:
			self.addtag(num,tag,value='')

	def addtag(self,num,tag,value=None,parent=None):
		'''value can be string, tag'''
		a=self.soup.new_tag(tag)
		if value: a.string=value
		if parent:
			self.records[num].find(parent).append(a)
		else:
			self.records[num].append(a)

	def gettag(self,num,tag,parent=None,obj=False):
		if parent:
			if self.records[num].find(parent):
				if self.records[num].find(parent).find(tag):
					if (obj):
						return self.records[num].find(parent).find(tag)
					else:
						return self.records[num].find(parent).find(tag).string
				else:
					return ''
			else:
				return ''
		else:
			if self.records[num].find(tag):
				if (obj):
					return self.records[num].find(tag)
				else:
					return self.records[num].find(tag).string
			else:
				return ''

	def settag(self,num,tag,value,parent=None):
		if parent:
			if self.records[num].find(parent):
				if self.records[num].find(parent).find(tag):
					self.records[num].find(parent).find(tag).string=value
				else:
					self.addtag(num,tag,parent=parent,value=value)
			else:
				a=self.soup.new_tag(tag)
				a.string=value
				self.addtag(num,parent,parent=None,value=a)
		else:
			if self.records[num].find(tag):
				self.records[num].find(tag).string=value
			else:
				self.addtag(num,tag,parent=None,value=value)	

	def getpath(self):
		db=self.soup.findChild("database")
		if (db):
			return os.path.splitext(db['path'])[0]+'.Data'
		else:
			return ""

	def getdoi(self,num):
		doistr=self.gettag(num,"electronic-resource-num")
		if (doistr):
			doiindex=doistr.find('10.')
		else:
			doiindex=-1
		if (doiindex >=0):
			return doistr[doiindex:].lower().strip()
		else:
			return ""

	def setdoi(self,num,value):
		self.settag(num,"electronic-resource-num",value)

	def gettitle(self,num):
		return self.gettag(num,"title")

	def settitle(self,num,value):
		self.settag(num,"title",value)

	def getjournalfull(self,num):
		return self.gettag(num,'secondary-title')

	def getyear(self,num):
		return self.gettag(num,'year','dates')

	def setyear(self,num,value):
		self.settag(num,'year',value,'dates')

	def getvolume(self,num):
		return self.gettag(num,'volume')

	def setvolume(self,num,value):
		self.settag(num,'volume',value)

	def getissue(self,num):
		return self.gettag(num,'number')

	def setissue(self,num,value):
		self.settag(num,'number',value)

	def getpages(self,num):
		return self.gettag(num,'pages')

	def setpages(self,num,value):
		self.settag(num,'pages',value)

	def getnotes(self,num):
		return self.gettag(num,'notes')

	def setnotes(self,num,value):
		self.settag(num,'notes',value)

	def geturl(self,num):
		urls=self.gettag(num,'related-urls',obj=True)
		if (urls):
			return [ i.string for i in urls.find_all('url') ]
		else:
			return []

	def seturl(self,num,value):
		'''Note that it will clean all the url!'''
		if (self.soup.find('related-urls') is not None):
			urls=self.gettag(num,'related-urls',obj=True)
			if (urls):
				urls.clear()
		else:
			self.addtag(num,'related-urls',parent='urls')
		self.addtag(num,'url',value,'related-urls')

	def addurl(self,num,value,first=False):
		urls=self.gettag(num,'related-urls',obj=True)
		a=self.soup.new_tag('url')
		a.string=value
		if (urls):
			if (not first):
				urls.append(a)
			else:
				urls.insert(0,a)
		else:
			self.settag(num,'related-urls',a,'urls')

	def getpdf(self,num):
		urls=self.gettag(num,'pdf-urls',obj=True)
		if (urls):
			return [ i.string for i in urls.find_all('url') ]
		else:
			return []

	def setpdf(self,num,value):
		'''Note that it will clean all the url!'''
		if (self.soup.find('pdf-urls') is not None):
			urls=self.gettag(num,'pdf-urls',obj=True)
			if (urls):
				urls.clear()
		else:
			self.addtag(num,'pdf-urls',parent='urls')
		self.addtag(num,'url',value,'pdf-urls')

	def setpdfs(self,num,value):
		'''Note that it will clean all the url!'''
		if (self.soup.find('pdf-urls') is not None):
			urls=self.gettag(num,'pdf-urls',obj=True)
			if (urls):
				urls.clear()
		else:
			self.addtag(num,'pdf-urls',parent='urls')
		for url in value:
			self.addtag(num,'url',url,'pdf-urls')

	def addpdf(self,num,value,first=False):
		urls=self.gettag(num,'pdf-urls',obj=True)
		a=self.soup.new_tag('url')
		a.string=value
		if (urls):
			if (not first):
				urls.append(a)
			else:
				urls.insert(0,a)
		else:
			self.addtag(num,'pdf-urls',a,'urls')

	def finddoi(self,num,prefix='',issn=''):
		title=self.gettitle(num)
		doi=DOI(self.getdoi(num))
		if (not prefix):
			prefix = doi.split('/',1)[0] if doi else ""
		volume= self.getvolume(num)
		journal=self.getjournalfull(num)
		year=self.getyear(num) 
		pages=self.getpages(num)
		self.cr=CRrecord()
		# The origin doi maybe true. Find in crossref
		if ( doi and self.cr.getfromdoi(doi,fullparse=False) and self.cr.doi):
			# Further check title
			if (strdiff(doi,self.cr.doi)>=0.85 and \
			strsimilarity(normalizeString(title),normalizeString(self.cr.title))>0.75):
				return doi
			if( volume and pages ):
				ops=pages.split('-')
				crps=self.cr.pages.split('-')
				if (len(ops)>0 and len(crps)>0 and ops[0]==crps[0] and volume==self.cr.volume):
					return doi
			if( year and pages ):
				ops=pages.split('-')
				crps=self.cr.pages.split('-')
				if (len(ops)>0 and len(crps)>0 and ops[0]==crps[0] and year==self.cr.year):
					return doi
			print "Origin DOI:",doi,"may be true but record strange..Try title"

		keyword=title+" "+journal+" "+year+" "+pages+" "+volume
		if (self.cr.getfromtitledoi(keyword,doi,year=year,limit=10,fullparse=False,prefix=prefix)):
			if (doi):
				if( prefix == self.cr.doi.split('/')[0] and strdiff(doi,self.cr.doi)>=0.85):
					return self.cr.doi
				else:
					print "Error for origin doi: "+doi+"; found: "+self.cr.doi
					return ""
			return self.cr.doi
		if (doi):
			if( strdiff(doi,self.cr.doi)>=0.85):
				return self.cr.doi
			else:
				print "Error2 for origin doi: "+doi+"; found: "+self.cr.doi
				return ""
		else:
			return ""

	def preprocess(self):
		pass

	def cleannote(self,num):
		note=self.getnotes(num)
		notel=note.lower()
		if ("time" in notel):
			self.setnotes(num,notel[notel.find('time'):])

	def cleanallpdf(self,exceptOAPDF=True):
		'''Clean PDF record or except OAPDF record'''
		for i in range(self.length):
			if (not exceptOAPDF):
				self.setpdf(i,'')
			else:
				for pdf in self.getpdf(i):
					if "internal-pdf://OAPDF/" in pdf:
						self.setpdf(i,pdf)
						break

	def process(self,fname="",cleannote=False,prefix='',issn='',start=0):
		epath=self.getpath()
		print "Output",self.length,"to",epath+os.sep+fname
		for i in range(start,self.length):
			try:
				#if (i%100 is 0):
				#	print
				#	print "Doing:",i+1,
				#else:
				#	print i+1,

				pdfs=self.getpdf(i)
				urls=self.geturl(i)
				# Fast consider as record process before
				for pdf in pdfs:
					if "internal-pdf://OAPDF/" in pdf:
						continue
				for url in urls:
					if "http://oapdf.sourceforge.net/cgi-bin/" in url:
						continue

				if (cleannote):
					self.cleannote(i)

				doistr=self.gettag(i,"electronic-resource-num")
				if (doistr[:4]=='chk:'):
					doi=DOI(self.getdoi(i))
				else:
					doi=DOI(self.finddoi(i,prefix=prefix,issn=issn))
				oapdflink=""
				if (doi):
					self.setdoi(i,"chk: "+doi)
					if (doi.is_oapdf()):
						oapdflink="http://oapdf.sourceforge.net/cgi-bin/doipage.cgi?doi="+doi

				newpdfs=[]
				for pdf in pdfs:
					pdfpath=pdf.replace("internal-pdf://",epath+os.sep+"PDF"+os.sep)
					relpath=pdf.replace("internal-pdf://","")
					# should never happen
					if (relpath == doi.quote()+".pdf"):
						newpdfs.append(pdf)
						continue
					if (doi):
						if (os.path.exists(pdfpath)):
							try:
								os.renames(pdfpath,epath+os.sep+"PDF"+os.sep+doi.quote()+".pdf")
								newpdfs.append("internal-pdf://"+doi.quote()+".pdf")
							except:
								print "Can't rename:",pdf,'to',doi.quote()+".pdf"
								newpdfs.append(pdf)
								continue
						else:
							print "Maybe error for the record",doi,"with pdf path:",pdf,'; Try finding..',
							pdfdir=os.path.split(pdfpath)[0]
							if (os.path.exists(pdfdir)):
								fs=glob.glob(pdfdir+os.sep+'*.pdf')
								if (len(fs)==1):
									try:
										os.renames(fs[0],epath+os.sep+"PDF"+os.sep+doi.quote()+".pdf")
										newpdfs.append("internal-pdf://"+doi.quote()+".pdf")
										print "Find",fs[0],'and rename!'
									except:
										print "Can't rename:",fs[0],'to',doi.quote()+".pdf"
										newpdfs.append(pdf)
										continue
								else:
									print "Can't find.."
									newpdfs.append(pdf)
									continue
							else:
								newpdfs.append(pdf)
								continue
					else:
						print "Blank doi for file:",pdf
						newpdfs.append(pdf)
						continue
				if (oapdflink):
					newpdfs.append("internal-pdf://OAPDF/"+doi.quote()+".pdf")
				self.setpdfs(i,newpdfs)
				# Set the urls
				if (oapdflink and oapdflink not in urls):
					self.addurl(i,oapdflink,first=True)
			except Exception as e:
				print "Error at ", i, 'since: ',e
				#return 1
		if fname:
			self.write(fname)
		return 0