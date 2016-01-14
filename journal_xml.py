#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os,sys,re,requests,difflib
# from xml.sax.saxutils import unescape
import HTMLParser

class jrecord(object):
	'''Basic journal record information'''
	def __init__(self):
		self.journal=""
		self.title=""
		self.authors=[]
		self.year=""
		self.volume=""
		self.issue=""
		self.pages=""
		self.doi=""
		self.issn=""
		self.urls=[]
		self.pdf=""
		self.abstract=""
		self.note=""
		
	def __repr__(self):
		return self.title+" | "+self.journal+" | "+self.year+" | "+self.pages

	def __str__(self):
		return self.__repr__()

class jcrossref(jrecord):
	'''Class for CrossRef json record based on jrecord'''
	def __init__(self):
		self.journal=""
		self.title=""
		self.authors=[]
		self.year=""
		self.volume=""
		self.issue=""
		self.pages=""
		self.doi=""
		self.issn=""
		self.urls=[]
		self.pdf=""
		self.abstract=""
		self.note=""
		#new 
		self.journal=[]
		self.issns=[]

	def _getauthor(self,ainfo):
		if (len(ainfo)<1 or not isinstance(ainfo,list)):
			return []
		authors=[]
		for i in ainfo:
			authors.append(i.get("family",'')+", "+i.get("given",''))
		return authors

	def getfromdoi(self,doi):
		r=requests.get("http://api.crossref.org/works/"+doi)
		if (r.status_code is 200):
			data=r.json()['message']
			self.journal=data['container-title'][0]
			self.title=data.get('title',[''])[0]
			self.authors=self._getauthor(data.get('author',[]))
			self.year=str(data['issued']['date-parts'][0][0])
			self.volume=data.get('volume','')
			self.issue=data.get('issue','')
			self.pages=data.get('page','')
			self.issn=data['ISSN'][0]
			self.doi=data['DOI']
			self.urls=[data.get('URL','')]
			self.journals=data['container-title']
			self.issns=data['ISSN']
			return True
		else:
			print "Error doi!"
			return False

	def getfromtitle(self,title,issn="",year="",offset=0, cutoff=0.9):
		url="http://api.crossref.org/works?query="+requests.utils.quote(title)+"&rows=1&offset="+str(offset)
		if (issn and year):
			url+="&filter=issn:"+issn+",from-pub-date:"+year+"-01,until-pub-date:"+year+"-12"
		elif (issn):
			url+="&filter=issn:"+issn
		elif (year):
			url+="&filter=from-pub-date:"+year+"-01,until-pub-date:"+year+"-12"

		r=requests.get(url)
		if (r.status_code is 200):
			try:
				data=r.json()['message']['items'][0]
				if (float(data['score'])>cutoff):
					self.journal=data['container-title'][0]
					self.title=data['title'][0]
					self.authors=self._getauthor(data['author'])
					self.year=str(data['issued']['date-parts'][0][0])
					self.volume=data.get('volume','')
					self.issue=data.get('issue','')
					self.pages=data.get('page','')
					self.issn=data['ISSN'][0]
					self.doi=data['DOI']
					self.urls=[data.get('URL','')]
					self.journals=data['container-title']
					self.issns=data['ISSN']
					return True
				else:
					print "Not enough similarity for title: "+title
					return False
			except:
				# Sometimes issn may be wrong
				if (issn):
					return self.getfromtitle(title,issn="",year=year,offset=offset,cutoff=cutoff)
				print "Something error for finding "+title
				return False
		else:
			print "Journal title can't be found: "+title
			return False

	def updatejrecord(self,jr):
		if (not isinstance(jr,jrecord)):
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

def notetimescited(record):
	n=records.note
	return re.sub(".*?(?=Times Cited)", n, flag=re.I)

class endnotexml(object):
	"""Endnote XML processor"""
	_precord=re.compile(r"<record>(?P<inner>.*?)</record>")
	#_pdatabase=re.compile(r'<database.*?>(?P<inner>.*?)</database>')
	_ppreinfo=re.compile(r'<database.*?>.*?</ref-type>')
	_pjournal=re.compile(r"(?<=<full-title>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</full-title>)")
	_ptitle=re.compile(r"(?<=<title>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</title>)")
	_pauthor=re.compile(r"(?<=<author>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</author>)")
	_pyear=re.compile(r"(?<=<year>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</year>)")
	_pvolume=re.compile(r"(?<=<volume>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</volume>)")
	_pissue=re.compile(r"(?<=<number>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</number>)")
	_ppages=re.compile(r"(?<=<pages>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</pages>)")
	_pdoi=re.compile(r"(?<=<electronic-resource-num>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</electronic-resource-num>)")
	_pissn=re.compile(r"(?<=<isbn>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</isbn>)")
	_pabstract=re.compile(r"(?<=<abstract>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</abstract>)")
	_pnote=re.compile(r"(?<=<notes>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</notes>)")
	_ppdf=re.compile(r"<pdf-urls><url>internal-pdf://(?P<inner>.*?)</url></pdf-urls>")
	_pauthors=re.compile(r"(?<=<authors>)(?P<inner>.*?)(?=</authors>)")
	_pauthor=re.compile(r"(?<=<author>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</author>)")
	_purls=re.compile(r"(?<=<related-urls>)(?P<inner>.*?)(?=</related-urls>)")
	_purl=re.compile(r"(?<=<url>)(?:<style.*?>)?(?P<inner>.*?)(?:</style>)?(?=</url>)")

	def __init__(self,filename=None, records=""):
		#self.database=""
		self.preinfo=""
		self.records=[]
		if (filename):
			self.readfile(filename);
			return
		if (records):
			self.read(records)

	def __len__(self):
		return len(self.records)

	def __iter__(self):
		return self.records.__iter__()

	def __repr__(self):
		sout=""
		for i in self.records:
			sout+=i.__repr__()+"; "
		return sout
	def __str__(self):
		return self.write()

	def __getitem__(self,i):
		return self.records.__getitem__(i);

	def __delitem__(self,i):
		return self.records.__delitem__(i);

	def __setitem__(self,i,y):
		return self.records.__setitem__(i,y);

	def parsetag(self,record,pattern):
		'''Use a re pattern to parse a record and return its value'''
		p=pattern.search(record)
		if (p):
			return p.group("inner")
		else:
			return ""
	def parsetags(self,record,pattern,subpattern):
		'''Use a re pattern to parse a record containing multi-value. Return all values in list'''
		p=pattern.search(record)
		if (p):
			return subpattern.findall(p.group("inner"))
		else:
			return []

	def parserecord(self,record, parsed=False):
		'''Parse a record for endnote xml
		Only parse the first attribute it catch
		return a record'''

		if not parsed:
			record=self._precord.search(record).group("inner")
		r=jrecord()
		r.journal=self.parsetag(record,self._pjournal)
		r.title=self.parsetag(record,self._ptitle)
		r.year=self.parsetag(record,self._pyear)
		r.volume=self.parsetag(record,self._pvolume)
		r.issue=self.parsetag(record,self._pissue)
		r.pages=self.parsetag(record,self._ppages)
		r.doi=self.parsetag(record,self._pdoi)
		r.issn=self.parsetag(record,self._pissn)
		r.abstract=self.parsetag(record,self._pabstract)
		r.note=self.parsetag(record,self._pnote)
		r.pdf=self.parsetag(record,self._ppdf)
		r.authors=self.parsetags(record,self._pauthors,self._pauthor)
		r.url=self.parsetags(record,self._purls,self._purl)
		return r

	def addrecord(self,record):
		'''Add a record to current records'''
		if (isinstance(record,jrecord)):
			self.records.append(record)
		else:
			print "Not a journal record object!"

	def read(self,records):
		'''Read records string and parse it'''
		self.preinfo=self._ppreinfo.search(records).group()
		for it in self._precord.finditer(records):
			if (it):
				self.records.append(self.parserecord(it.group("inner"),parsed=True))

	def readfile(self,filename):
		'''Read contains from a file and parse it'''
		if (os.path.exists(filename)):
			f=open(filename)
			self.read(f.read())
			f.close()
		else:
			raise "Error file input!"

	def getrecord(self,index):
		'''Get record with index id (start from 0)'''
		return records[index]

	def write(self,record=None):
		'''Output all/given record[s] to a string
		record support all(None or not given), list (int) and int'''
		sout=""
		if (record is not None):
			if (isinstance(record,list)):
				for i in record:
					sout+=self.write(i)
			elif (isinstance(record, int)):
				r=self.records[record]
				sout+='<record>'+self.preinfo
				sout+='<contributors><authors>'
				for author in r.authors:
					sout+="<author>"+author+'</author>'
				sout+='</authors></contributors><titles>'
				sout+='<title>'+r.title+'</title>'
				sout+='<secondary-title>'+r.journal+'</secondary-title>'
				sout+='<pages>'+r.pages+'</pages>'
				sout+='<volume>'+r.volume+'</volume>'
				sout+='<number>'+r.issue+'</number>'
				sout+='<dates><year>'+r.year+'</year></dates>'
				sout+='<isbn>'+r.issn+'</isbn>'
				sout+='<abstract>'+r.abstract+'</abstract>'
				sout+='<notes>'+r.note+'</notes>'
				sout+='<urls><related-urls>'
				for url in r.url:
					sout+='<url>'+url+'</url>'
				sout+='</related-urls></urls>'
				sout+='<pdf-urls><url>internal-pdf://'+r.pdf+'</url></pdf-urls>'
				sout+='<electronic-resource-num>'+r.doi+'</electronic-resource-num>'
				sout+='</related-urls></urls>'
				sout+='</record>'
		else:
			# write all
			sout+='<?xml version="1.0" encoding="UTF-8" ?><xml><records>'
			for i in range(len(self.records)):
				sout+=self.write(i)
			sout+='</records></xml>'

		return sout

	def writefile(self,filename):
		'''Write out the current endnote xml to a file'''
		f=open(filename,'w')
		f.write(self.write())
		f.close()

	def cleanpdf(self):
		'''Clean the pdf information in all records'''
		for r in self.records:
			r.pdf=""

	def normdoi(self):
		'''Normailize doi information in all records'''
		for r in self.records:
			p=r.doi.find("10.")
			r.doi=r.doi[p:].strip().lower()
	
	def primeurl(self,urlfunc):
		'''Use a urlfunc to add the url as the prime url
		url function use a record as argument and return a url string'''
		for r in self.records:
			r.url=[urlfunc(r)]+r.url

class babelxml(object):
	pass

def strdiff(str1, str2):
	return difflib.SequenceMatcher(None, str1, str2).ratio()

def removeunicode(s):
	out=""
	for i in range(len(s)):
		if (ord(s[i])<=128):
			out+=s[i]
	return str(out)

def updateEXMLbyCrossRef(xmlfname,issn=None,blankdoi=True, pageupdate=True):
	'''Check and update Endnote XML record based on CrossRef information
	Search based on journal title.
	issn: None: use record issn; False:don't use issn; Other:search based on issn
	blankdoi: Update blank doi based on search
	pageupdate: Update pages record'''
	exml=endnotexml()
	# Read xml
	fin=open(xmlfname)
	text=fin.read()
	fin.close()
	fins=os.path.splitext(xmlfname)
	fwxml=open(fins[0]+"_new"+fins[1],'w')
	startpart=re.search(r"<\?xml.*?<records>",text).group()
	endpart="</records></xml>"
	fwxml.write(startpart)
	htmlp=HTMLParser.HTMLParser()

	for it in exml._precord.finditer(text):
		if (it):
			record=it.group("inner")
			#first check doi and title
			title=htmlp.unescape(exml.parsetag(record,exml._ptitle).lower().strip())
			doi=exml.parsetag(record,exml._pdoi).lower().strip()

			jc=jcrossref()
			#First try to find doi
			if (doi and jc.getfromdoi(doi)):
				jtitile=removeunicode(jc.title).lower().strip()
				if (strdiff(jtitile,title)>0.9):
					if (pageupdate):
						record=exml._ppages.sub(removeunicode(jc.pages),record)
					fwxml.write("<record>"+record+"</record>")
					continue

			#Try to find using title/year/pages information
			year=exml.parsetag(record,exml._pyear)
			volume=exml.parsetag(record,exml._pvolume)
			pages=exml.parsetag(record,exml._ppages)
			if (issn is None ):
				issn=exml.parsetag(record,exml._pissn)
			
			# Try to check 3 times using offset argv.
			# Trying to find same year/volume/start-page, high similar title
			trytitle=0;
			while True:
				#try:
				if (jc.getfromtitle(title, issn=issn, year=year, offset=trytitle, cutoff=0.95)):
					if (jc.year==year and jc.volume==volume and jc.pages.split('-')[0]==pages.split("-")[0]):
						if (pageupdate):
							record=exml._ppages.sub(removeunicode(jc.pages),record)
						if (doi.strip()=="" and blankdoi):
							print "Update blank doi for:"+title+"; "+year+"; "+volume+"; "+pages
							record=exml._pdoi.sub(jc.doi,record)
						elif (strdiff(jc.doi,doi)>0.9 and jc.doi !=doi):
							print "Update doi: "+doi+" to "+jc.doi
							record=exml._pdoi.sub(jc.doi,record)
						elif(strdiff(jc.doi,doi)<=0.9):
							print "Not enough doi similarity for record doi: "+doi
						break
				#except:

				trytitle+=1
				if (trytitle>=3):
					print "Can't find suitable for title: "+title
					break
			fwxml.write("<record>"+record+"</record>")
	fwxml.write(endpart)
	fwxml.close()

if __name__=="__main__":
	updateEXMLbyCrossRef(sys.argv[1])
