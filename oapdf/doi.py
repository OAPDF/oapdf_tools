#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Last Update: 2016.1.28 - 2:15AM

'''DOI class '''

import os,sys,re,difflib
import requests

TIMEOUT_SETTING=30

################ DOI class ############################
class DOI(str):
	'''A class for standard DOI. 
	It should contain "10." and / or @, Else: it will be blank 
	if doi is quote, it will unquote when generate'''

	pdoi=re.compile("(?:\:|\\b)(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")
	def __new__(self,doi=""):
		'''Should be 10.*/ or 10.*@ 
		Normalize(lower,strip)
		Unquote it (@ to /)'''
		if "10." in doi:
			doi=doi.lower().strip()
			if ("/" in doi):
				return str.__new__(self,doi)
			elif("@" in doi):
				return str.__new__(self,requests.utils.unquote(doi.replace('@','/')))
			else:
				return str.__new__(self,"")
		else:
			return str.__new__(self,"")

	def __init__(self,doi=""):
		'''Generate prefix/suffix'''
		str.__init__(self)
		tmp=self.split('/',1)
		self.prefix=tmp[0]
		if (len(tmp)>1):
			self.suffix=tmp[1]
		else:
			self.suffix=""
		#article object
		self.crjson=None
		self._url=""
		self._pmid=""
		self._pmcid=""

	@property
	def url(self):
		'''Get URL property'''
		if not self._url:
			self._url=self.geturl()
		return self._url

	@property
	def pmid(self):
		'''Get PMID property'''
		if not self._pmid:
			self._pmid=self.getpmid()
		return self._pmid

	@property
	def pmcid(self):
		'''Get PMCID property'''
		if not self._pmcid:
			self._pmcid=self.getpmcid()
		return self._pmcid

	def quote(self,doi=None):
		'''Quote it to file name format'''
		if (not doi):
			return requests.utils.quote(self,'+/()').replace('/','@')
		else:
			return requests.utils.quote(doi,'+/()').replace('/','@')
	
	def unquote(self, doi):
		'''Only for outer string'''
		return requests.utils.unquote(doi.replace('@','/'))

	def diff(self,doi):
		'''Compare two doi string'''
		if (isinstance(doi,DOI)):
			return difflib.SequenceMatcher(None, self, doi).ratio()
		else:
			return difflib.SequenceMatcher(None, self, DOI(doi)).ratio()

	def decompose(self, url=True, outdir=True, length=5, doi=None):
		'''Decompose quoted doi to a list or a url string at most length for each
		Note that dir name can't end with '.', it will be delete here.
		Default, decompose to a outdir name
		If url, output url string (containing quoted doi name)
		If outdir, output string for directory of doi'''
		if (not doi):
			suffix=self.quote(self.suffix)
			lens=len(suffix)
			if (lens<=length):
				if outdir: 
					return self.prefix+"/"
				if (url):
					return self.prefix+"/"+self.prefix+"@"+suffix
				else:
					return [self.prefix,suffix]
			layer=(lens-1)/length
			dirurl=[self.prefix]
			for i in range(layer):
				item=suffix[i*length:(i+1)*length].rstrip('.')
				if (item[:4].lower() == 'con.'):
					item=item.replace('.','%2E',1)
				dirurl.append(item)
			if outdir: 
				return "/".join(dirurl)+"/"
			if (url):
				return "/".join(dirurl)+"/"+self.prefix+"@"+suffix
			else:
				dirurl.append(suffix[(lens-1)/length*length:])
				return dirurl
		else:
			return DOI(doi).decompose(url=url,outdir=outdir,length=length)

	def geturl(self,doi=None):
		'''Get the doi article url''' 
		if (not doi):
			doi=self
			if (self._url): return self._url
		else:
			doi=self.unquote(doi)
		r=requests.get("http://dx.doi.org/"+doi,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			self._url=r.url
			return r.url
		else:
			return ""

	def is_oapdf(self,doi=None):
		'''Check the doi is in OAPDF library'''
		doi = DOI(doi) if doi else self
		if (not doi):
			#r=requests.get('http://127.0.0.1/doilink/pages/'+self.decompose(url=True,outdir=False)+".html",timeout=0.3)
			urldir=self.decompose(url=True,outdir=False)
			try:
				r=requests.get('http://35.8.151.207/doilink/pages/'+urldir+".html",timeout=0.3)
				return (r.status_code is 200)
			except:
				r=requests.get("http://oapdf.github.io/doilink/pages/"+urldir+".html",timeout=TIMEOUT_SETTING)
				return (r.status_code is 200)

	def has_oapdf_pdf(self,doi=None):
		'''Check whether the doi has in OAPDF library'''
		doi = DOI(doi) if doi else self
		try:
			r=requests.get("http://oapdf.github.io/doilink/pages/"+self.prefix+"/path/"+self.quote()+".html",timeout=TIMEOUT_SETTING)
			return (r.status_code is 200)
		except Exception as e:
			print e
			return False

	def valid_doaj(self,doi=None):
		'''Valid the DOI is Open Access by DOAJ'''
		doi = self.unquote(doi) if doi else self
		try:
			r=requests.get('https://doaj.org/api/v1/search/articles/doi:'+doi,timeout=TIMEOUT_SETTING)
		except Exception as e:
			print e
			return False
		return r.json().get('total',0)>0

	def valid_doiorg(self,doi=None,geturl=False):
		'''Valid DOI is OK in dx.doi.org'''
		doi = self.unquote(doi) if doi else self
		r=requests.get("http://dx.doi.org/"+doi,allow_redirects=geturl,timeout=TIMEOUT_SETTING)
		if (geturl and r.status_code is 200): self.url=r.url
		return (r.status_code != 404)

	def gettitle(self,doi=None):
		'''Get the doi title, may be faster than valid_crossref'''
		doi = self.unquote(doi) if doi else self
		if not self.crjson: self.getcrossref()
		if (self.crjson):
			return self.crjson.get('message','{}').get('title',[''])[0]
		print "Error doi (DOI.gettile)! "+doi 
		return ""

	def getcrossref(self,doi=None):
		'''Return the json result of crossref api'''
		doi = self.unquote(doi) if doi else self
		r=requests.get("http://api.crossref.org/works/"+doi,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			self.crjson=r.json()
			return self.crjson
		print "Error doi (DOI.getcrossref)! "+doi
		self.crjson={} 
		return self.crjson

	def getbibtex(self,doi=None):
		'''Get the bibtex result *.bib file context'''
		doi = self.unquote(doi) if doi else self
		header={'Accept':'application/x-bibtex'}
		r=requests.get("http://dx.doi.org/"+doi,headers=header,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			return r.text
		print "Error doi (DOI.getbibtex)! "+doi 
		return ""

	def getendnote(self,doi=None):
		'''Get the endnote result *.ris file context'''
		doi = self.unquote(doi) if doi else self
		header={'Accept':'application/x-research-info-systems'}
		r=requests.get("http://dx.doi.org/"+doi,headers=header,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			return r.text
		print "Error doi (DOI.getendnote)! "+doi 
		return ""

	def getbibliography(self,style="",locale="",doi=None):
		'''Get the bibliography with given style'''
		doi = self.unquote(doi) if doi else self
		typestr="text/x-bibliography"
		if (style):
			typestr=typestr+"; style="+style
		if locale:
			typestr=typestr+"; locale="+locale
		header={'Accept':typestr}
		r=requests.get("http://dx.doi.org/"+doi,headers=header,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			return r.text
		print "Error doi (DOI.getbibliography)! "+doi 
		return ""

	def freedownload(self,doi=None):
		'''Is it open access or has free download url?'''
		doi = DOI(doi) if doi else self
		opprefix=['10.1371','10.3390',"10.3389","10.1186", "10.1093"]
		if (doi.prefix in opprefix):
			return True
		return doi.is_oapdf() or doi.valid_doaj()

	def getpmid(self,doi=None):
		'''Get PMID used in PubMed'''
		doi = DOI(doi) if doi else self
		if (self._pmid):return self._pmid
		params={"ids":doi,"format":"json"}
		r=requests.get("http://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/", params=params,timeout=TIMEOUT_SETTING)
		if (r.status_code is 200):
			rj=r.json().get('records',{[]})
			if (rj):
				self._pmid=rj[0].get('pmid','')
				self._pmcid=rj[0].get('pmcid','')
			return self._pmid
		print "No PMID or Error doi (DOI.getpmid)! "+doi 
		return ""

	def getpmcid(self,doi=None):
		'''Get PMCID used in PubMed Central'''
		doi = DOI(doi) if doi else self
		if (self._pmcid):return self._pmcid
		params={"ids":doi,"format":"json"}
		r=requests.get("http://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/", params=params,timeout=TIMEOUT_SETTING)		
		if (r.status_code is 200):
			rj=r.json().get('records',{[]})
			if (rj):
				self._pmid=rj[0].get('pmid','')
				self._pmcid=rj[0].get('pmcid','')
			return self._pmcid
		print "No PMID or Error doi (DOI.getpcmid)! "+doi 
		return ""

	def getfrompmid(self,pmid):
		'''Get DOI from PMID or PMCID'''
		params={"ids":pmid,"format":"json"}
		r=requests.get("http://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/", params=params,timeout=TIMEOUT_SETTING)		
		if (r.status_code is 200):
			rj=r.json().get('records',{[]})
			if (rj):
				doi=DOI(rj[0].get('doi',''))
				if (doi):
					doi._pmid=rj[0].get('pmid','')
					doi._pmcid=rj[0].get('pmcid','')
					return doi
		print "Error PMID/PMCID! "+pmid 
		return ""

	def getfrompmcid(self,pmcid):
		'''Get DOI from PMID/PMCID'''
		getfrompmcid=self.getfrompmid

	def publisherstyle(self,publisher,doi=None):
		'''Parse doi style whether it's from given publisher
		Support ACS, Wiley, AIP, Nature, Science, RSC, Springer, ScienceDirect'''
		doi = DOI(doi) if doi else self

		if (isinstance(publisher,str)):
			if publisher: publisher=publisher.lower().strip()
			if publisher == 'sciencedirect' or publisher=='elsevier':
				publisher='sd'
			
			if (doi.prefix=='10.1021' and (publisher =='acs' or publisher=='all')):
				return True
			elif ((doi.prefix=='10.1002' or doi.prefix=='10.1011') and (publisher =='wiley' or publisher=='all')):
				return True
			elif (doi.prefix=='10.1016' and (publisher =='sd' or publisher=='all')):
				return True
			elif (doi.prefix=='10.1007' and (publisher =='springer' or publisher=='all')):
				return True
			elif (doi.prefix=='10.1039' and (publisher =='rsc' or publisher=='all')):
				return True
			elif (doi.prefix=='10.1038' and (publisher =='nature' or publisher=='all')):
				return True	
			elif (doi.prefix=='10.1126' and (publisher =='science' or publisher=='all')):
				return True	
			elif (doi.prefix=='10.1063' and (publisher =='aip' or publisher=='all')):
				return True
		elif (isinstance(publisher,list) or isinstance(publisher,set)):
			for p in publisher:
				result=self.publisherstyle(p)
				if result:
					return True
		return False	

