#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

'''Module for DOI and journal record operation
Also include the journal pdf function'''

import os,re
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup

try:
	from .jrecord import Jrecord
	from .basic import normalizeString,strsimilarity,strdiff
except (ImportError,ValueError) as e:
	from jrecord import Jrecord
	from basic import normalizeString,strsimilarity,strdiff

timeout_setting=30


################# CrossRef records class #######################

class CRrecord(Jrecord):
	'''Simple CrossRef Record just for check doi+title'''
	def __init__(self):
		Jrecord.__init__(self)
		#new for crossref multi-value
		self.journals=[]
		self.issns=[]

	def reset(self):
		Jrecord.reset(self)
		del self.journals[:]
		del self.issns[:]

	def _getauthor(self,ainfo):
		if (len(ainfo)<1 or not isinstance(ainfo,list)):
			return []
		authors=[]
		for i in ainfo:
			authors.append(i.get("family",'')+", "+i.get("given",''))
		return authors

	def valid_doi(self,doi,fullparse=False):
		'''Valid DOI is OK in crossref, 
		return a CrossRef record itself. Default not parse all record'''
		if (self.getfromdoi(doi,fullparse=fullparse)):
			return self
		return None	

	def updatejrecord(self,jr):
		if (not isinstance(jr,Jrecord)):
			print "Not journal record object!"
			return False
		jr.journal=self.journal
		jr.title=self.title
		jr.authors=self.authors
		jr.year=self.year
		jr.volume=self.volume
		jr.issue=self.issue
		jr.pages=self.pages
		jr.issn=self.issn
		jr.doi=self.doi
		jr.urls=jr.urls+self.urls
		return True

	def getfromdoi(self, doi, fullparse=True):
		'''Get information from doi
		fullparse: will parse more information'''
		r=requests.get("http://api.crossref.org/works/"+doi,timeout=timeout_setting)
		if (r.status_code is 200):
			data=r.json()['message']
			self.title=data.get('title',[''])
			if (isinstance(self.title,list) and len(self.title)>0):
				self.title=self.title[0]
			elif (len(self.title) is 0):
				print "Strang blank title when crossref...: "+doi
				self.title=''
			self.year=str(data.get('issued',{'date-parts':[[1111,1,1]]}).get('date-parts',[[1111,1,1]])[0][0])
			self.volume=data.get('volume','')
			self.issue=data.get('issue','')
			self.pages=data.get('page','')
			self.doi=data.get('DOI','')
			if (fullparse):
				self.journals=data.get('container-title',[''])
				self.issns=data.get('ISSN',[''])
				if (len(self.journals)>=1): 
					self.journal=self.journals[0]
				else:
					self.journal=""
				if (len(self.issns)>=1): 
					self.issn=self.issns[0]
				else:
					self.issn=""
				self.authors=self._getauthor(data.get('author',[]))
				self.urls=[data.get('URL','')]

			return True
		else:
			print "Error doi by CrossRef: "+doi
			return False

	def getfromtitle(self,title,year="",volume="",issue="",pages="", \
		limit=3, offset=0, cutoff=0.1, fullparse=True,ignorecheminfo=True,doi="",prefix="",issn=""):
		'''Get information from journal title, better with year, volume, issue, pages information'''
		# Over max records try 
		if (offset>limit):
			return False
		# Cancel ISSN check because unreliable

		# search url
		if (issn and len(issn.strip()) is 9):
			url="http://api.crossref.org/journals/"+issn+"/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		elif (prefix):
			url="http://api.crossref.org/prefixes/"+prefix+"/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		else:	
			url="http://api.crossref.org/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		if (year):
			#some time year maybe +- 1
			url+="&filter=from-pub-date:"+str(int(year)-1)+"-06,until-pub-date:"+str(int(year)+1)+"-06"	
		#print url
		
		# search crossref
		r=requests.get(url,timeout=timeout_setting)
		if (r.status_code is 200):
			try:
				data=r.json()['message']['items'][0]
				# should better then cutoff
				if (float(data['score'])>cutoff):
					self.title=data.get('title',[''])[0]
					self.year=str(data.get('issued',{'date-parts':[[1111,1,1]]}).get('date-parts',[[1111,1,1]])[0][0])
					self.volume=data.get('volume','')
					self.issue=data.get('issue','')
					self.pages=data.get('page','')
					self.doi=data.get('DOI','')
					if (fullparse):
						self.journals=data.get('container-title',[''])
						self.issns=data.get('ISSN',[''])
						if (len(self.journals)>=1): 
							self.journal=self.journals[0]
						else:
							self.journal=""
						if (len(self.issns)>=1): 
							self.issn=self.issns[0]
						else:
							self.issn=""
						self.authors=self._getauthor(data.get('author',[]))
						self.urls=[data.get('URL','')]
					# check whether fitting to giving parameters
					if (year and year.strip()!=self.year.strip()): 
						# possible +- 1year
						if not (abs(int(year)-int(self.year)) is 1 and volume.strip()==self.volume.strip()):
							self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
								limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse,ignorecheminfo=ignorecheminfo)
					if (volume and volume.strip()!=self.volume.strip()): 
						self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
							limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse,ignorecheminfo=ignorecheminfo)
					if (pages and pages.strip().split('-')[0] !=self.pages.strip().split('-')[0]): 
						self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
							limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse,ignorecheminfo=ignorecheminfo)
					if (ignorecheminfo and data.get('container-title',[''])[0].lower() == "cheminform" ):
						self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
							limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse,ignorecheminfo=ignorecheminfo)
					return True
				# Low score, more try.
				else:
					return (self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
						limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse))
			except:
				print "Something error for finding "+title.encode('utf-8')
				return False
		else:
			print "Journal title can't be found: "+title.encode('utf-8')
			return False			

	def getfromtitledoi(self,title,doi, year="",volume="",issue="",pages="", \
		limit=3, offset=0, cutoff=0.1, fullparse=True,ignorecheminfo=True,prefix="",issn=""):
		'''Get information from journal title and doi, better with year, volume, issue, pages information'''
		# Over max records try 
		if (offset>limit):
			return False
		# Cancel ISSN check because unreliable

		# search url
		if (issn and len(issn.strip()) is 9):
			url="http://api.crossref.org/journals/"+issn+"/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		elif (prefix):
			url="http://api.crossref.org/prefixes/"+prefix+"/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		else:	
			url="http://api.crossref.org/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		if (year):
			#some time year maybe +- 1
			url+="&filter=from-pub-date:"+str(int(year)-1)+"-06,until-pub-date:"+str(int(year)+1)+"-06"	
		#print url
		
		# search crossref
		r=requests.get(url,timeout=timeout_setting)
		if (r.status_code is 200):
			try:
				for currentrecord in range(len(r.json()['message']['items'])):
					data=r.json()['message']['items'][currentrecord]
					# should better then cutoff
					if (float(data['score'])>cutoff):
						self.title=data.get('title',[''])[0]
						self.year=str(data['issued']['date-parts'][0][0])
						self.volume=data.get('volume','')
						self.issue=data.get('issue','')
						self.pages=data.get('page','')
						self.doi=data.get('DOI','')
						if (fullparse):
							self.journals=data.get('container-title',[''])
							self.issns=data.get('ISSN',[''])
							if (len(self.journals)>=1): 
								self.journal=self.journals[0]
							else:
								self.journal=""
							if (len(self.issns)>=1): 
								self.issn=self.issns[0]
							else:
								self.issn=""
							self.authors=self._getauthor(data.get('author',[]))
							self.urls=[data.get('URL','')]

						if (doi.strip()):
							if( strdiff(doi.strip(),self.doi)>=0.85):
								return True
						#else blank

						# check whether fitting to giving parameters
						if (year and year.strip()!=self.year.strip()): 
							# possible +- 1year
							if not (abs(int(year)-int(self.year)) is 1 and volume.strip()==self.volume.strip()):
								continue
						if (volume and volume.strip()!=self.volume.strip()): 
							continue
						if (pages and pages.strip().split('-')[0] !=self.pages.strip().split('-')[0]): 
							continue
						if (ignorecheminfo and data.get('container-title',[''])[0].lower() == "cheminform" ):
							continue
						return True
					# Low score, more try.
					else:
						continue
				return False
			except:
				print "Something error for finding "+title.encode('utf-8')
				return False
		else:
			print "Journal title can't be found: "+title.encode('utf-8')
			return False

	def gettotalresultfromlink(self,url,params=None):
		if (not params or not isinstance(params,dict)):params={}
		params['rows']='1'
		r=requests.get(url,params=params,timeout=timeout_setting)
		total=0
		if (r.status_code is 200):
			total = int(r.json()['message']['total-results'])
		return total