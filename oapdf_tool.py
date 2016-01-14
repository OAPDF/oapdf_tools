#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''Module for DOI and journal record operation
Also include the journal pdf function'''

import os,sys,re,difflib,gc,glob,time,random
import requests,urlparse
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

#disable warning
requests.packages.urllib3.disable_warnings()
# browser header
browserhdr={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
escaper=HTMLParser()

########## DOI and string tools library ####################

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return requests.utils.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return requests.utils.unquote(doi.replace('@','/'))

def strdiff(str1, str2):
	'''Similarity of two string'''
	return difflib.SequenceMatcher(None, str1, str2).ratio()

def strsimilarity(longstr,shortstr):
	'''Better algorithm for str similarity'''
	matching=difflib.SequenceMatcher(None,longstr,shortstr).get_matching_blocks()
	length=0
	for item in matching:
		length+=item[2]
	return float(length)/len(shortstr)

def removeunicode(s):
	'''Remove non-ascii char'''
	out=''
	for i in range(len(s)):
		if (ord(s[i])<128):
			out+=s[i]
	return str(out)

def normalizeString(s):
	'''Replace [!a-zA-Z0-9_] to blank'''
	return re.sub("\W+",' ',s)

def is_oapdf(doi):
	'''Check the doi is in OAPDF library'''
	doi=DOI(doi)
	r=requests.get("http://oapdf.github.io/doilink/pages/"+doi.decompose(url=True,outdir=False)+".html")
	return (r.status_code is 200)

def filebasename(fname):
	return os.path.splitext(os.path.basename(fname))[0]

class DOI(str):
	'''A class for standard DOI. 
	It should contain "10." and / or @, Else: it will be blank 
	if doi is quote, it will unquote when generate'''
	pdoi=re.compile("\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")
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
		self.record=None

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
				dirurl.append(suffix[i*length:(i+1)*length])
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
		else:
			doi=self.unquote(doi)
		r=requests.get("http://dx.doi.org/"+doi)
		if (r.status_code is 200):
			return r.url
		else:
			return ""

	def is_oapdf(self,doi=None):
		'''Check the doi is in OAPDF library'''
		if (not doi):
			r=requests.get("http://oapdf.github.io/doilink/pages/"+self.decompose(url=True,outdir=False)+".html")
			return (r.status_code is 200)
		else:
			return DOI(doi).is_oapdf()

	def valid_doiorg(self,doi=None):
		'''Valid DOI is OK in dx.doi.org'''
		if (not doi):
			doi=self
		else:
			doi=self.unquote(doi)
		r=requests.get("http://dx.doi.org/"+doi,allow_redirects=False)
		return (r.status_code == 303)

	def valid_crossref(self,doi=None,fullparse=False):
		'''Valid DOI is OK in crossref, 
		return a CrossRef record. Default not parse all record'''
		if (not doi):
			doi=self
		else:
			doi=self.unquote(doi)
		cr=crrecord()
		if (cr.getfromdoi(doi,fullparse=fullparse)):
			self.record=cr
			return cr
		return None		

	def gettitle(self,doi=None):
		'''Get the doi title, may be faster than valid_crossref'''
		if (not doi):
			doi=self
		else:
			doi=self.unquote(doi)
		r=requests.get("http://api.crossref.org/works/"+doi)
		if (r.status_code is 200):
			title=r.json()['message'].get('title',[''])[0]
			return title
		print "Error doi (DOI.gettile)! "+doi 
		return ""

############### Record Related Library ####################

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

	def reset(self):
		self.journal=""
		self.title=""
		del self.authors[:]
		self.year=""
		self.volume=""
		self.issue=""
		self.pages=""
		self.doi=""
		self.issn=""
		del self.urls[:]
		self.pdf=""
		self.abstract=""
		self.note=""		
		
	def __repr__(self):
		return self.doi+": "+self.title+" | "+self.journal+" | "+self.year+"; "+self.volume+"("+self.issue+")"+", "+self.pages

	def __str__(self):
		return self.__repr__()

def parseNotefirst(text):
	'''Parse NoteFirst record (xml format)'''
	soup=BeautifulSoup(text,"html.parser")
	j=jrecord()
	j.title=soup.primarytitle.text
	doi=soup.doi.text
	j.doi=doi[doi.find("10."):]
	j.journal=soup.media.info.text
	j.year=soup.year.text
	j.volume=soup.volume.text
	j.issue=soup.issue.text
	j.pages=soup.pagescope.text
	authors=soup.findChildren('fullname')
	j.authors=[ author.info.text for author in authors]
	#j.issn=""
	return j

######## CrossRef records library #########

class crrecord(jrecord):
	'''Simple CrossRef Record just for check doi+title'''
	def __init__(self):
		jrecord.__init__(self)
		#new for crossref multi-value
		self.journals=[]
		self.issns=[]

	def reset(self):
		jrecord.reset(self)
		del self.journals[:]
		del self.issns[:]

	def _getauthor(self,ainfo):
		if (len(ainfo)<1 or not isinstance(ainfo,list)):
			return []
		authors=[]
		for i in ainfo:
			authors.append(i.get("family",'')+", "+i.get("given",''))
		return authors

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

	def getfromdoi(self, doi, fullparse=True):
		'''Get information from doi
		fullparse: will parse more information'''
		r=requests.get("http://api.crossref.org/works/"+doi)
		if (r.status_code is 200):
			data=r.json()['message']
			self.title=data.get('title',[''])
			if (isinstance(self.title,list) and len(self.title)>0):
				self.title=self.title[0]
			elif (len(self.title) is 0):
				print "Strang blank title when crossref...: "+doi
				self.title=''
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

			return True
		else:
			print "Error doi by CrossRef: "+doi
			return False

	def getfromtitle(self,title,year="",volume="",issue="",pages="", limit=3, offset=0, cutoff=0.9, fullparse=True):
		'''Get information from journal title, better with year, volume, issue, pages information'''
		# Over max records try 
		if (offset>limit):
			return False
		# Cancel ISSN check because unreliable

		# search url
		url="http://api.crossref.org/works?query="+normalizeString(title)+"&rows=1&offset="+str(offset)
		if (year):
			#some time year maybe +- 1
			url+="&filter=from-pub-date:"+str(int(year)-1)+"-06,until-pub-date:"+str(int(year)+1)+"-06"	
		#print url
		
		# search crossref
		r=requests.get(url)
		if (r.status_code is 200):
			try:
				data=r.json()['message']['items'][0]
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
					# check whether fitting to giving parameters
					if (year and year.strip()!=self.year.strip()): 
						# possible +- 1year
						if not (abs(int(year)-int(self.year)) is 1 and volume.strip()==self.volume.strip()):
							self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
								limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse)
					if (volume and volume.strip()!=self.volume.strip()): 
						self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
							limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse)
					if (pages and pages.strip().split('-')[0] !=self.pages.strip().split('-')[0]): 
						self.getfromtitle(title=title,year=year,volume=volume,issue=issue,pages=pages,
							limit=limit,offset=offset+1,cutoff=cutoff,fullparse=fullparse)
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

	def getfromlink(self,url,params):
		trytotal={"rows":"1"}
		r=requests.get(url,params=trytotal)
		total=0
		if (r.status_code is 200):
			total=int(r.json()['message']['total-results'])


############# Endnote relate libraray ##############

def enwparse(enw):
	'''Parse the endnote enw file, return dict'''
	result={'journal':"",'year':'','volume':"",'issue':'','pages':'','title':'','author':[]}
	lines=enw
	if (not isinstance(enw,file)):
		lines=enw.splitlines()
	for line in lines:
		if (len(line)>1):
			item=line[1]
			if item=="T":
				result['title']=line[3:].strip()
			elif item=="D":
				result['year']=line[3:].strip()
			elif item=="P":
				result['pages']=line[3:].strip()
			elif item=="J":
				result['journal']=line[3:].strip()
			elif item=="V":
				result['volume']=line[3:].strip()
			elif item=="N":
				result['issue']=line[3:].strip()
			elif item=="A":
				result['author'].append(line[3:].strip())
	return result


############### PDF related library ########################

def adjustpdflink(link):
	'''Adjust some links to correct address'''
	if ("europepmc.org/abstract/MED" in link):
		r=requests.get(link)
		if (r.status_code is 200):
		 	soup=BeautifulSoup(r.text, "html.parser")
			out=soup.findChild(attrs={"name":"citation_fulltext_html_url"})
			if (out): 
				return out["content"]
	#Avoid some website
	elif ("onlinelibrary.wiley.com" in link or "pubs.acs.org" in link or "link.springer.com" in link or "http://www.sciencedirect.com/" in link):
		return ""
	return link

def getwebpdfparams(link):
	'''Parse link and get the parameters for get'''
	if ("//europepmc.org/" in link):
		return {"pdf":"render"}
	elif ("//www.researchgate.net" in link):
		return {"inViewer":"0","pdfJsDownload":"0","origin":"publication_detail"}
	else:
		qs=None
		try:
			qs=urlparse.parse_qs(urlparse.urlparse(link).query)
			if (qs):
				qs={}
				for k,v in qs:
					if (isinstance(v,list) and len(v)==1):
						qs2[k]=v[0]
					else:
						qs2[k]=v
				return qs2
			else:
				return None
		except:
			pass
	return None

#browserhdr={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
def getwebpdf(link,fname,params=None, force=False):
	'''Get a PDF from a link. if fail, return False'''
	#Have been downloaded...
	if (not force and os.path.exists(fname)):
		return True
	if (not link):
		return False
	try:
		if (params and isinstance(params,dict) ):
			rpdf=requests.get(link,params=params,headers=browserhdr)
		else: rpdf=requests.get(link,headers=browserhdr)
		# check pdf type. sometimes not whole string, use "in"
		if (rpdf.status_code is 200 and 'application/pdf' in rpdf.headers['Content-Type'].lower().strip()):
			fpdf=open(fname,'wb')
			fpdf.write(rpdf.content)
			fpdf.close()
			return True
	except requests.exceptions.ConnectionError:
		print "Error to get pdf linK: "+link+" for file: "+fname
	except requests.exceptions.TooManyRedirects:
		return False
	print "Can't find pdf at link: "+link
	return False

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

	def GetPageNumber(self,fname):
		'''Get total page number of PDF'''	
		try:
			fp = file(fname, 'rb')
			pageno=0
			for page in PDFPage.get_pages(fp, set(), maxpages=0, 
				password=self.password, caching=self.caching, check_extractable=True):
				pageno+=1
			return pageno
		except:
			print "Error Reading PDF page number.."
			return 0

	def GetSinglePage(self,fname,pageno=1):
		'''Get Single Page contents of PDF, return string
		Default first page'''	
		try:
			fp = file(fname, 'rb')
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
			return ""

	def GetPages(self,fname,pagenos=[1]):
		'''Get Several Page contents of PDF, return string
		Default first page'''	
		try:
			fp = file(fname, 'rb')
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
			return ""

	def GetAllPages(self,fname):
		'''Get All Page contents of PDF, return string'''	
		try:
			fp = file(fname, 'rb')
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
			return ""		

###### doipdffile class

class doipdffile(object):
	'''DOI named PDF file processor object'''
	pdoi=re.compile("\\b(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")
	def __init__(self,fname=""):
		self.handle=PDFHandle()
		self.doi=set()
		self.didpage=set()
		self.normaltxt=[]
		self.reset(fname)
		
	@property
	def fname(self):
	    return self._fname
	
	def reset(self,fname):
		'''Reset the saved information and Set the fname 
		!!Important: You should set the fname when you deal with another file!!!'''
		self.doi.clear()
		self.didpage.clear()
		if (isinstance(self.normaltxt,str)):
			del self.normaltxt
			self.normaltxt=[]
		else:
			del self.normaltxt[:]
		self.maxpage=0
		self._fname=""
		if (not fname):
			return
		if (os.path.exists(fname) and os.path.splitext(fname)[1].lower()==".pdf"):
			self._fname=fname
			self.maxpage=self.handle.GetPageNumber(fname)
			self.normaltxt=['' for i in range(self.maxpage)]
		else:
			print "Error file exist or pdf type. Check it"

	def setfile(self,fname):
		self.reset(fname)

	def renamefile(self,newname):
		'''Rename a file'''
		try:
			if not self._fname: 
				print "File Name Not Set!!!"
				return
			if(os.path.exists(newname)):
				"File exists from "+self._fname+" to "+newname
				return 
			os.renames(self._fname,newname)
			self._fname=newname
		except WindowsError:
			os.system("mv '"+self._fname+"' '"+newname+"'")		

	def movetodir(self,newdir):
		'''move to new dir'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return
		fbasic=os.path.split(self._fname)[1]
		try:
			if (newdir[-1] =="/" or newdir[-1] =="\\"):
				if(os.path.exists(newdir+fbasic)):
					"File exists from "+self._fname+" to dir"+newdir
					return 
				os.renames(self._fname, newdir+fbasic)
				self._fname=newdir+fbasic
			else:
				if(os.path.exists(newdir+os.sep+fbasic)):
					"File exists from "+self._fname+" to dir"+newdir
					return 
				os.renames(self._fname,newdir+os.sep+fbasic)
				self._fname=newdir+os.sep+fbasic
		except WindowsError as e:
			os.system("mv '"+self._fname+"' '"+newdir+"'")

	def doiresultprocess(self,dois):
		'''Very important to deal with found dois....'''
		newdois=[]
		for d in dois:
			if (d.strip()[-1] =='.'):
				newdois.append(d.strip()[:-1].lower())
			else:
				newdois.append(d.strip().lower())
		return newdois	

	def finddoi(self,page=1):
		'''Find doi in given page number
		If page<=0, find all page; >0 single page.
		If page is list, find '''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		if (self.maxpage is 0):
			print 'Error max page 0 for '+self._fname
			return ""
		if (isinstance(page,str) or isinstance(page,float) ):
			page=int(page)
		if (isinstance(page,int)):
			if (page <= 0 ):
				outstr=self.handle.GetAllPages(self._fname)
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr.lower().replace("doi:"," "))))
				self.normaltxt=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.update(range(1,self.maxpage+1))
			# Only valid page
			if (page>self.maxpage): 
				page=self.maxpage
			# Only page not process before
			if (page not in self.didpage):
				outstr=self.handle.GetSinglePage(self._fname,page)
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr.lower().replace("doi:"," "))))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.add(page)
		elif ( isinstance(page,list) or isinstance(page,tuple) or isinstance(page,set)):
			for i in page:
				self.finddoi(i)

	def hascontent(self,text, similarity=0.95,page=None):
		'''Normalize text and find it in normalized pdf content found before.'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		text=normalizeString(text).lower().strip().replace(' ','')
		try:
			if (not page or (isinstance(page,int) and (page>self.maxpage or page<=0))):
				if (similarity<1.0):
					sim=strsimilarity(''.join(self.normaltxt),text)
					return (sim >= similarity)
				else:
					return text in ''.join(self.normaltxt)
			elif (isinstance(page,int)):
				if (similarity<1.0):
					sim=strsimilarity(self.normaltxt[page-1],text)
					return (sim >= similarity)
				else:
					return text in self.normaltxt[page-1]
		except:
			print "Something error for hascontent function: "+text	

	def hasoneofcontent(self,ltext,similarity=0.95,page=None):
		'''Normalize text in a list and find it in normalized pdf content found before.
		One in list right result is right'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return False
		if (isinstance(ltext,list)):
			for text in ltext:
				if (self.hascontent(text,similarity=similarity,page=page)):
					return True
		elif (isinstance(ltext,str)):
			return self.hascontent(ltext, similarity=similarity,page=page)
		return False		

	def checktitle(self,title,similarity=0.95,page=None):
		'''For check title. Some special case in title...'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		title=escaper.unescape(title)
		title=re.sub(r"(?:<.?sup>|<.?i>|\$\$.*?{.*?}.*?\$\$)","",title)
		return self.hascontent(title, similarity=similarity,page=page)

	def checkcrossref(self,cr):
		'''Check other info in crossref record...For some paper don't have doi.
		Should fully parse crossref!
		Only first page!'''
		if (isinstance(cr,crrecord)):
			try:
				if (not self.hascontent(cr.pages.split("-")[0],1.0,page=1)): return False
				if (not self.hascontent(cr.volume,1.0,page=1)): return False
				if (not self.hasoneofcontent([cr.year,str(int(cr.year)+1),str(int(cr.year)-1)],1.0,page=1)): return False
				if (not self.hasoneofcontent(cr.journals,1.0,page=1)): return False
				#if (not self.hasoneofcontent(cr.issns,1.0,page=1)): return False
				return True
			except ValueError as e:
				print e
				return False
		return False

	def checkdoi(self,doi,page=1,iterfind=True):
		'''Check whether doi in given page'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return False
		self.finddoi(page)
		if (doi in self.doi):
			return True
		elif (iterfind and page is 1 and self.maxpage is not 1 and self.checkdoi(doi,2)):
			return True
		elif (iterfind and page is 2 and self.maxpage is not 2 and self.checkdoi(doi,self.maxpage)):
			return True
		return False

	def checkdoinormaltxt(self,doi):
		'''Check nospace normalstring doi whether in nospace normalstring context'''
		ndoi=normalizeString(doi).lower().replace(" ",'')
		return (ndoi in ''.join(self.normaltxt))

	def checkdoifurther(self,doi):
		'''Special cases..It will re-read pdf and do more process. 
		So it need to run checkdoinormaltxt first to make sure doi in context'''
		outstr=self.handle.GetPages(self._fname,self.didpage).lower()
		outstr=outstr.replace("\xe2\x80\x93",'-').replace("\xe5\x85\xbe","/")
		#dois=set(self.doiresultprocess(self.pdoi.findall(re.sub(r"\n(?=[^\n])",'',re.sub(r'doi.(?=10.)',' ',outstr)))))
		out2=re.sub(r"\n(?=[^\n])",'',outstr)
		return (doi in out2)

	def checkdoititle(self,doi,title,page=1):
		'''Check whether doi and title in given page'''
		return self.checkdoi(doi,page) and self.hascontent(title)

	def checkdoifname(self,page=[1,2]):
		'''Check whether fname's doi same to doi in file
		Default check two pages'''
		bname=os.path.splitext(os.path.basename(self._fname))[0].strip().lower()
		fdoi=requests.utils.unquote(bname.replace('@','/'))
		return self.checkdoi(fdoi,page)

	def renamecheck(self,fname):
		'''A complex function to get doi from file name, 
		check in crossref, check in pdf file, rename it!'''
		self.reset(fname)
		fdoi=DOI(os.path.splitext(os.path.basename(self._fname))[0])
		self.finddoi(1)
		if (not fdoi):
			if (len(self.doi) is 1):
				nodoi=DOI( list(self.doi)[0] )
				crno=nodoi.valid_crossref(fullparse=True)
				if (crno):
					if (self.checktitle(crno.title)):
					# Valid doi and title, rename file
						self.renamefile("Done/"+nodoi.quote()+".pdf")
						return True
					else:
						print "OK doi in file but not title(Unsure): "+self._fname+" to: "+nodoi.quote()+".pdf"
						self.renamefile("Unsure/"+nodoi.quote()+".pdf")
						return False
				# Error doi
				else:
					print "Error doi and title(Fail): "+self._fname
					self.movetodir("Fail")
					return False
			else:
				print "0/too much doi. Can't sure(Fail): "+self._fname
				self.movetodir("Fail")
				return False
		# fdoi is ok
		cr=fdoi.valid_crossref(fullparse=True)
		#crossref is ok
		if (fdoi and cr):
			crpages=cr.pages.split('-')
			totalpagenumber=1
			if ( len(crpages) == 2 ):
				try:
					totalpagenumber=int(crpages[1])-int(crpages[0])
				except ValueError as e:
					print e, crpages

			# Just check first page, faster.
			doivalid=self.checkdoi(fdoi,page=1,iterfind=False)
			if (doivalid and self.checktitle(cr.title) 
					and self.maxpage >= totalpagenumber):
				# Yes! Good PDF!
				self.movetodir("Done")
				return True

			# Further check doi in page2/last, Finally, will check 1,2 and last pages.
			doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True) or doivalid )
			titlevalid=self.checktitle(cr.title) or (self.checktitle(cr.title,similarity=0.85) and self.checkcrossref(cr))

			if (doivalid):
				if (titlevalid):
					if (self.maxpage >= totalpagenumber):						
						# Yes! Good PDF!
						self.movetodir("Done")
						return True
					else:
						# DOI ok but not title
						print "OK fdoi and title, but page not fit(Fail): "+self._fname
						self.movetodir("Fail")
						return False						
				else:
					# DOI ok but not title
					print "OK fdoi but not title(Untitle): "+self._fname
					self.movetodir("Untitle")
					return False

			# Indeed, doi maybe in pdf, but strange format..
			if (self.checkdoinormaltxt(fdoi)):
				# Indeed, exist! Enough pages?
				if (self.maxpage >= totalpagenumber):
					if (titlevalid):
						# Further check only when title OK
						if (self.checkdoifurther(fdoi)):
							# Fine! move to Done dir
							self.movetodir("Done")
							return True
						else:
							# Can't find, but high similar! move to High dir
							print "OK title and nospacebreak doi,but not pass(High): "+self._fname
							self.movetodir("High")
							return False
					else:
						# DOI ok but not title
						print "Maybe OK fdoi but not title(Untitle): "+self._fname
						self.movetodir("Untitle")
						return False
				else:
					# DOI ok but not title
					print "Maybe OK fdoi, but page not fit(Fail): "+self._fname
					self.movetodir("Fail")
					return False						

			# DOI maybe not exist ....
			if (titlevalid):
				if (self.maxpage >= totalpagenumber):	
					# Old paper don't have doi...
					if (self.checkcrossref(cr)):
						if (int(cr.year)<=1999 and len(self.doi) is 0):
							# Highly possible right
							self.movetodir("Done")
							return True
						#  Bentham, often blank doi
						elif (fdoi[:8] == '10.2174/' and len(self.doi) is 0):
							self.movetodir("Done")
							return True
						elif (len(self.doi) is 0):
							print "OK title and high info fit. But no doi(Highly): "+self._fname
							self.movetodir("High")
							return True							
						else:
							print "OK title and high info fit. But doi not fit(Unsure): "+self._fname
							self.movetodir("Unsure")
							return True								
					elif(len(self.doi) is 0):
						# Maybe wrong file no doi
						print "Not found doi in file but ok title (Unsure): "+self._fname
						self.movetodir("Unsure")
						return False
				elif (len(self.doi) is 0):
					# Maybe wrong file no doi
					print "Only title OK, no doi/pages fit (Fail): "+self._fname
					self.movetodir("Fail")
					return False

			#fdoi,title wrong, no doi in file
			if (len(self.doi) is 0):
				print "Both fdoi and title wrong, no doi in file(Fail): "+self._fname
				self.movetodir("Fail")
				return False

			# Indeed, file has only one doi, not the same to fname
			if (len(self.doi) is 1):
				newdoi=DOI( list(self.doi)[0] )
				newcr=newdoi.valid_crossref(fullparse=True)
				if (newcr):
					crpages=newcr.pages.split('-')
					totalpagenumber=1
					if (len(crpages) ==2 ):
						try:
							totalpagenumber=int(crpages[1])-int(crpages[0])
						except ValueError as e:
							print e, crpages
					if (self.checktitle(newcr.title) and self.maxpage >= totalpagenumber):
					# Valid doi and title, rename file
						print "OK: Rename file from "+self._fname+" to "+newdoi.quote()+".pdf"
						self.renamefile("Done"+os.sep+newdoi.quote()+".pdf")
						return True
					else:
						print "One in-file doi but not title(Unsure): "+self._fname
						self.movetodir("Unsure")
						return False
				# Error doi
				else:
					print "Error doi and title(Fail): "+self._fname
					self.movetodir("Fail")
					return False
			elif(len(self.doi) > 1):
				print "fdoi/title fail. Too much infile doi(Unsure): "+self._fname
				self.movetodir("Unsure")
				return False
			else:
				print "What?????What?????(Fail):"+self._fname
				self.movetodir("Fail")
				return False
			
################ ResearchGate Library ########################
#browserhdr={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
rgparams={"inViewer":"0","pdfJsDownload":"0","origin":"publication_detail"}
class ResearchGate(object):
	def isRGlink(self,link):
		if (re.search("www.researchgate.net/.*?publication",link)):
			return True
		return False
	def isRGpdflink(self,link):
		if (re.search("www.researchgate.net/.*?publication.*?\.pdf",link)):
			return True
		return False
	def getpdfByLink(self,link,filename=""):
		if (not filename):
			re1=re.search(r"[^/]+?.pdf",link)
			if (re1):
				filename=re1.group()
			else:
				print "No file name given!"
				return False
		if (os.path.exists(filename)):
			return True
		r=requests.get(link,params=rgparams,headers=browserhdr)
		if r.status_code is 200:
			f=open(filename,'wb')
			f.write(r.content)
			f.close()
			if (os.path.exists(filename)): return True
		return False
	def getpdfByID(self,rgid):
		r=requests.get("https://www.researchgate.net/publication/"+str(rgid),headers=browserhdr)
		if (r.status_code is 200):
			soup=BeautifulSoup(r.text, "html.parser")
			out=soup.findChild(name="a",attrs={"class":"blue-link js-download rf btn btn-promote"})
			link=''
			if (out):
				link=out['href']
			out=soup.findChild(attrs={'name':"citation_doi"})
			doi=""
			if (out):
				doi=out['content']
			filename=quotefileDOI(doi.lower().strip())
			return self.getpdfByLink(link,filename)
		return False

############### Bing Academey Search Related ########################

class BingAcedemic(object):
	'''A class for Bing Academic Search'''

	# Global var for bing search, only valid when bing search is using China region!			
	bingacademicurl="http://www.bing.com/academic/"
	hdr={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',\
'Connection':'keep-alive'}
	# re for extract BID in download/citation
	bidre=re.compile(r'(?<=data-paperid=\")\w+?(?=\">)')

	def __init__(self):
		t=int(time.time())
		self.bfile=open("bingid_"+str(t)+".txt",'a')

	def bingacademicResultID(self,inq,maxpage=1):
		'''Get maxpage pages record ID in searching results for inq keyword in bing academic'''
		inq=re.sub(r"\s+","+",inq)
		bids=[]
		if (maxpage<1):maxpage=1
		if (maxpage>10):maxpage=10
		for pagei in range(maxpage):
			startpage=pagei*10+1
			param={"mkt":"zh-CN",'q':inq,'first':str(startpage)}
			r=requests.get(self.bingacademicurl,params=param,headers=self.hdr)
			if (r.status_code is 200):
				soup=BeautifulSoup(r.text, "html.parser")
				findpdflinkresult=soup.find_all(attrs={"class":"b_citeItem"})
				bids=bids+[self.bidre.search(str(s)).group() for s in findpdflinkresult]
		return bids

	def findpdfbid(self,inq,maxpage=1):
		'''Get maxpage pages pdf links in searching results for inq keyword in bing academic'''
		inq=re.sub(r"\s+","+",inq)
		bids=[]
		if (maxpage<1):maxpage=1
		if (maxpage>10):maxpage=10
		for pagei in range(maxpage):
			startpage=pagei*10+1
			param={"mkt":"zh-CN",'q':inq,'first':str(startpage)}
			try:
				r=requests.get(self.bingacademicurl,params=param,headers=self.hdr)
				if (r.status_code is 200):
					soup=BeautifulSoup(r.text, "html.parser")
					findpdflinkresult=soup.find_all(attrs={"class":"b_downloadItem"})
					if (findpdflinkresult):
						bids=bids+[self.bidre.search(str(s)).group() for s in findpdflinkresult]
			except requests.exceptions.ConnectionError as e:
				print e ,'for', inq
		return bids

	def bidpdflink(self,bid):
		'''Get PDF link from bing ID'''
		requestsSession = requests.Session()
		requestsSession.mount('http://', requests.adapters.HTTPAdapter(max_retries=5))
		try:
			r=requestsSession.get("http://mylib.chinacloudsites.cn/Paper/Download/"+str(bid),timeout=20)
			print "pdflink time:",r.elapsed
			sys.stdout.flush()
			pdflinks=[]
			if (r.status_code is 200):
				results=r.json()['result']
				for result in results:
					pdflinks.append(result.get('link',''))
				self.bfile.write(bid+"\n")
				self.bfile.flush()
			return pdflinks
		except requests.exceptions.ConnectionError:
			print "ConnectionError: Fail to find pdf link for bid: "+bid
			return []

	def bidref(self,bid):
		'''Get reference information from bing ID'''
		requestsSession = requests.Session()
		requestsSession.mount('http://', requests.adapters.HTTPAdapter(max_retries=5))
		try:
			params={"type":"endnote"}
			r=requestsSession.get("http://mylib.chinacloudsites.cn/Paper/Citation/"+str(bid),params=params,headers=self.hdr,timeout=20)
			print "get ref time:",r.elapsed
			sys.stdout.flush()
			if (r.status_code is 200):
				return enwparse(r.text)
			return enwparse('')
		except requests.exceptions.ConnectionError:
			print "ConnectionError: Fail to find ref info for bid: "+bid
			return enwparse('')

	def getbidpdf(self,bid,filename=None,printyn=True):
		'''Try to get pdf file based on bing id to a filename'''
		if (not filename): 
			filename=bid+".pdf"
		pdflink=self.bidpdflink(bid)
		if (printyn): print pdflink
		for pl in pdflink:
			if (getwebpdf(adjustpdflink(pl),fname=filename,params=getwebpdfparams(pl))):
				break
		if (os.path.exists(filename)):
			return True
		return False

	def grepBingAcadPDFbyID(self,bid,maxpage=1,printyn=True):
		'''Grep at most maxpage pages pdf for given bing id
		Save to doi style based on refering to crossref.'''
		if (printyn):
			print "###  ###  ###  ###  ###  ###  ###  ###  ### "
			print "## Finding for "+bid+"...."
		cr=crrecord()
		ref=self.bidref(bid)
		if (printyn):
			print ref
		if (os.path.exists(bid+".pdf")):
			print "Exist file:"+bid+".pdf"
			return
		if ref['title']:
			if (cr.getfromtitle(title=ref['title'],year=ref['year'],volume=ref['volume'],
					pages=ref['pages'],issue=ref['issue'],fullparse=False) and cr.doi):
				# try to find by title, if found (true):
				if (printyn): print cr.__repr__().encode('utf-8')
				outname=quotefileDOI(cr.doi)+".pdf"
				if (not os.path.exists(outname)):
					if (self.getbidpdf(bid,filename=outname,printyn=printyn)):
						print "Have Found PDF file: "+outname
				else:
					print "Exist file:"+outname
			else:
				if (self.getbidpdf(bid,filename=bid+".pdf",printyn=printyn)):
					print "Have Found PDF file: "+bid+".pdf"
		else:
			if (self.getbidpdf(bid,filename=bid+".pdf",printyn=printyn)):
				print "Have Found PDF file: "+bid+".pdf"

	def grepBingAcadPDF(self,keyword,maxpage=1,printyn=True):
		'''Grep at most maxpage pages pdf for searching keyword.
		Save to doi style based on refering to crossref.'''
		bids = set(self.findpdfbid(keyword,maxpage))
		for bid in bids:
			#if (bid=='68F37860'):
				self.grepBingAcadPDFbyID(bid,maxpage=maxpage,printyn=printyn)

	def findcrossreftitledoi(self,doi,printyn=True):
		'''Find doi by crossref first'''
		cr=crrecord()
		if( cr.getfromdoi(doi,fullparse=False) and cr.doi):
			keyword=cr.title+" "+cr.doi
			print "#########################################################################"
			print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
			sys.stdout.flush()
			self.grepBingAcadPDF(keyword=keyword,maxpage=1,printyn=printyn)
		else:
			print "Error DOI!: "+doi
		cr.reset()

	def finddoiPDFfromFile(self,filename):
		fin=open(filename)
		countN=0
		for line in fin:
			ldoi=line.lower().strip()
			bingacad.findcrossreftitledoi(ldoi)
			countN+=1
			if countN>=10:
				gc.collect()
				countN=0
		fin.close()		

class SearchEngine(object):

	def __init__(self):
		self.url=""
		self.word=""
		self.request=None
		
	def search(self,keyword,params={},headers={}):
		r=requests.get(self.url,params=params,headers=headers)
		if (r.status_code is 200):
			return r.text
		return ""

class SearchItem(object):
	def __init__(self):
		self.text=""
		self.title=""
		self.link=""
		self.pdf=[""]

class BaiduXueshu(object):
	host="http://xueshu.baidu.com"
	path="/s"
	url="http://xueshu.baidu.com/s"
	word="wd"
	citeurl="http://xueshu.baidu.com/u/citation"
	def __init__(self):
		self.request=None
		self.soup=None
		self.items=[]

	def reset(self):
		self.request=None
		del self.items[:]
		del self.soup; self.soup=None
		del self.request; self.request=None
		
	def search(self,keyword,params={},headers={}):
		self.reset()
		if (not keyword):return

		params[self.word]=keyword
		r=requests.get(self.url,params=params,headers=headers)
		if r.status_code is 200:
			self.soup=BeautifulSoup(r.text, "html.parser")
			self.items=self.soup.findChildren('div',attrs={'class':'result sc_default_result xpath-log'})
			#for item in items:

	def _parsepdflink(self,link):
		if (link):
			link=requests.utils.unquote(link)
		if (len(link)>2):
			if link[:2]=="/s":
				rer=re.search(r'(?<=url=)http.*?(?=\&ie;=utf-8)',link)
				if rer:link=rer.group()
			return link
		return ""

	def getpdflink(self,num=0):
		pdfs=self.items[num].findChildren('p',attrs={'class':"saveurl"})
		return [ self._parsepdflink(pdf.text) for pdf in pdfs ]

	def getcite(self,num=0,citetype="txt"):
		cite=self.items[num].findChild('a',attrs={'class':'sc_q c-icon-shape-hover'})
		params={'t':citetype,'url':cite['data-link'],'sign':cite['data-sign']}
		try:
			r=requests.get(self.citeurl,params=params)
			if r.status_code is 200:
				return r.text
		except:
			print "Can't get citation"
		return ""

	def getdoi(self,num=0):
		soup=BeautifulSoup(self.getcite(num,citetype='txt'),"html.parser")
		doi=soup.doi.text
		return DOI(doi[doi.find('10.'):])

	def getallpdf(self):
		for i in range(len(self.items)):
			try:
				links=self.getpdflink(i)
				if (links):
					doi=self.getdoi(i)
					print "### Find for result with DOI: "+doi
					doifname=doi.quote()+".pdf"
					if (os.path.exists(doifname)):
						continue
					for link in links:
						if (getwebpdf(adjustpdflink(link),fname=doifname,params=getwebpdfparams(link))):
							break
					if (os.path.exists(doifname)):
						print "Get PDF file!: "+doifname
						time.sleep(random.randint(1,5))
						return True
			except:
				print "Error when get pdf.."

	def findcrossreftitledoi(self,doi,printyn=True):
		'''Find doi by crossref first'''
		cr=crrecord()
		if( cr.getfromdoi(doi,fullparse=False) and cr.doi):
			keyword=cr.title+" "+cr.doi
			print "#########################################################################"
			print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
			sys.stdout.flush()
			self.search(keyword=keyword)
			self.getallpdf()
		else:
			print "Error DOI!: "+doi
		cr.reset()

	def finddoiPDFfromFile(self,fname):
		fin=open(fname)
		countN=0
		for line in fin:
			ldoi=line.lower().strip()
			doi=DOI(ldoi)
			if (os.path.exists(doi.quote()+".pdf")):
				continue
			self.findcrossreftitledoi(ldoi)
			time.sleep(random.randint(10,30))
			countN+=1
			if countN>=10:
				gc.collect()
				countN=0
		fin.close()			
				
if __name__ == "__main__":
	try:
		bingacad=BingAcedemic()
		#### Find a keyword by Bing and download pdf
		#bingacad.grepBingAcadPDF("science computational biology",maxpage=10)

		#### Find doi saved in file by Bing and download pdf 
		bingacad.finddoiPDFfromFile(sys.argv[1])

		##### Rename doi file
		#dpf=doipdffile()
		#for f in glob.iglob("*.pdf"):
		#	dpf.renamecheck(f)
		#	sys.stdout.flush()

		#needurl="http://api.crossref.org/journals/0006-3495/works"
		#total=47701
		#params={"rows":"100","offset":"0"}
		#offsetcount=200
		#for i in range(2,478):
		#	params["offset"]=str(100*i)
		#	gc.collect()
		#	r=requests.get(needurl,params)
		#	if (r.status_code is 200):
		#		for j in r.json()['message']['items']:
		#			keyword=j.get('title',[''])[0]+" "+j.get("DOI","")
		#			print "#####################################",offsetcount,"####################################"
		#			print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
		#			sys.stdout.flush()
		#			bingacad.grepBingAcadPDF(keyword)
		#			offsetcount+=1

		#needurl="http://api.crossref.org/journals/0006-3495/works"
		#total=47701
		#params={"rows":"100","offset":"0"}
		#offsetcount=282
		#params["offset"]=str(offsetcount)
		#r=requests.get(needurl,params)
		#if (r.status_code is 200):
		#	for j in r.json()['message']['items']:
		#		keyword=j.get('title',[''])[0]+" "+j.get("DOI","")
		#		print "#####################################",offsetcount,"####################################"
		#		print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
		#		sys.stdout.flush()
		#		bingacad.grepBingAcadPDF(keyword)
		#		offsetcount+=1

		#bdxs=BaiduXueshu()
		#bdxs.finddoiPDFfromFile(sys.argv[1])

	finally:
		pass
		bingacad.bfile.close()







		
