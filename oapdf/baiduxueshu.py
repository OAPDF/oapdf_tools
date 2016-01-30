#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

'''Module for DOI and journal record operation
Also include the journal pdf function'''

import os,sys,re
import time,random,gc
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup

try:
	from .doi import DOI
	from .crrecord import CRrecord
	from .basic import *
	from .getpdf import *
	from .pdfdoicheck import PDFdoiCheck
except (ImportError,ValueError) as e:
	from doi import DOI
	from crrecord import CRrecord
	from basic import *
	from getpdf import *
	from pdfdoicheck import PDFdoiCheck

timeout_setting=30
timeout_setting_download=120

def pdfexistpath(fname):
	if (os.path.exists(fname) or os.path.exists('Done/'+fname)\
		or os.path.exists('High/'+fname) or os.path.exists('Unsure/'+fname)\
		or os.path.exists('Fail/'+fname) or os.path.exists('Untitle/'+fname) ):
		return True
	else:
		return False

############################# Part5: Search Engine ##################################

class SearchEngine(object):

	def __init__(self):
		self.url=""
		self.word=""
		self.request=None
		
	def search(self,keyword,params={},headers={}):
		r=requests.get(self.url,params=params,headers=headers,timeout=timeout_setting)
		if (r.status_code is 200):
			return r.text
		return ""

	def getitems(self):
		pass

class ResultItem(object):
	def __init__(self):
		self.text=""
		self.title=""
		self.link=""
		self.abstract=""

####################### BaiduXuShu Related ###############################

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
		#new add to check and remove not good result
		self.pdfcheck=PDFdoiCheck()
	def reset(self):
		self.request=None
		del self.items[:]
		del self.soup; self.soup=None
		del self.request; self.request=None
		self.pdfcheck.reset('')
		
	def search(self,keyword,params={},headers={}):
		self.reset()
		if (not keyword):return

		params[self.word]=keyword
		params['sc_hit']='1'#for find all, not exactly
		r=requests.get(self.url,params=params,headers=headers,timeout=timeout_setting)
		if r.status_code is 200:
			self.soup=BeautifulSoup(r.text, "html.parser")
			self.items=self.soup.findChildren('div',attrs={'class':'result sc_default_result xpath-log'})
			#print "Find",len(self.items)," Results."
			#for item in items:

	def _parsepdflink(self,link):
		'''Some pdf link in baidu format'''
		if (link):
			link=requests.utils.unquote(link)
		if (len(link)>4):
			if link[:2]=="/s":
				rer=re.search(r'(?<=url=)http.*?(?=\&ie;=utf-8)',link)
				if rer:
					link=rer.group()
					return link
			elif(link[:4] == 'http'):
				return link
			return ''
		return ""

	def getpdflink(self,num=0):
		pdfs=[ i.text for i in self.items[num].findChildren('p',attrs={'class':"saveurl"})] \
			+[ i['href'] for i in self.items[num].findChildren('a',attrs={'class':"sc_download c-icon-download-hover"})]
		pdfs=list(set([ adjustpdflink(self._parsepdflink(pdf)) for pdf in pdfs]))
		if '' in pdfs: pdfs.remove('')
		if (pdfs): print "Get",len(pdfs)," links for record ",num,":",#,str(pdfs)
		return pdfs

	def getcite(self,num=0,citetype="txt"):
		cite=self.items[num].findChild('a',attrs={'class':'sc_q c-icon-shape-hover'})
		try:
			params={'t':citetype,'url':cite['data-link'],'sign':cite['data-sign']}
			r=requests.get(self.citeurl,params=params,timeout=timeout_setting)
			if r.status_code is 200:
				return r.text
		except:
			print "Can't get citation"
		return ""

	def getdoi(self,num=0):
		'''Get DOI from Baidu Cite'''
		soup=BeautifulSoup(self.getcite(num,citetype='txt'),"html.parser")
		if (soup.doi): 
			doi=soup.doi.text
		elif(soup.primarytitle):
			cr=CRrecord()
			cr.getfromtitle(soup.primarytitle.info.text,ignorecheminfo=True)
			doi=cr.doi
		else:
			doi=DOI("")
		return DOI(doi[doi.find('10.'):])

	def getallpdf(self,doifilter=None):
		'''Get All pdf from link
		doifilter should be a function, return True when DOI ok'''
		usedoifilter=callable(doifilter)
		getfilelist=[]
		for i in range(len(self.items)):
			try:
				links=self.getpdflink(i)
				if (links):
					doi=DOI(self.getdoi(i))
					if not doi:
						print "blank doi..",doi
						continue
					if ( usedoifilter and not doifilter(doi)):
						print doi,'Not fit filter..'
						continue
					if (doi.freedownload()):
						print doi,'exist in free library..'
						continue
					doifname=doi.quote()+".pdf"
					if (pdfexistpath(doifname)):
						print doi,'Files exist in current folder..'
						continue
					print "### Find for result with DOI: "+doi
					for link in links:
						print 'Link:',str(link),
						if (getwebpdf(link,fname=doifname,params=getwebpdfparams(link))):
							print "Try Getting..",
							try:
								dpfresult=self.pdfcheck.renamecheck(doifname)
								sys.stdout.flush()
								if (dpfresult!=0): 
									#Important to set fname to None		
									rmresult=self.pdfcheck.removegarbage(fname=None)
									if (rmresult <= 1):
										if (os.path.exists(self.pdfcheck._fname)):
											if dpfresult<4:
												print "!!!!!!! Get PDF file to Not Done..: "+doifname
												getfilelist.append(self.pdfcheck._fname)
												#time.sleep(random.randint(1,5))								
												break
											else:
												if (not os.path.exists('tmpfail/'+self.pdfcheck._fname)):
													os.renames(self.pdfcheck._fname,'tmpfail/'+self.pdfcheck._fname)
												else:
													os.remove(self.pdfcheck._fname)
										else:
											print "What? should never happen for pdfdoicheck.moveresult Not Done.."
									else:
										print "Has been removed.."
								else:
									if (os.path.exists(self.pdfcheck._fname)):
										print "!!!!!!! Get PDF file to Done!: "+doifname
										getfilelist.append(self.pdfcheck._fname)
										#time.sleep(random.randint(1,5))								
										break
									else:
										print "What? should never happen for pdfdoicheck.moveresult Done.."
							except Exception as e:
								if os.path.exists(doifname):
									if (not os.path.exists('tmpfail/'+doifname)):
										os.renames(doifname,'tmpfail/'+doifname)
									else:
										os.remove(doifname)
								print e,'Error at baidu getallpdf when doing pdfcheck'
						else:
							print "can't get at this link"
			except Exception as e:
				print e, "##### Error when get pdf.."
		return getfilelist

	def findwordPDF(self,keyword,doifilter=None):
		print "#########################################################################"
		print "## Now finding for: "+ keyword+"............"
		sys.stdout.flush()
		self.search(keyword=keyword)
		self.getallpdf(doifilter)		

	def findcrossreftitledoi(self,doi,printyn=True):
		'''Find doi by crossref first'''
		cr=CRrecord()
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
		'''Put doi in file and use it to find pdf'''
		fin=open(fname)
		countN=0
		for line in fin:
			ldoi=line.lower().strip()
			doi=DOI(ldoi)
			if (os.path.exists(doi.quote()+".pdf")):
				continue
			self.findcrossreftitledoi(ldoi)
			#time.sleep(random.randint(1,10))
			countN+=1
			if countN>=10:
				gc.collect()
				countN=0
		fin.close()			

	def findPDFbyISSN(self,issn,maxresult=None, step=100, offset=0, usedoi=True,doifilter=None):
		'''Find PDF by ISSN based on search result from crossref'''
		# may be improve to not only issn..
		if (not issn):return
		needurl="http://api.crossref.org/journals/"+issn+"/works"
		cr=CRrecord()
		total=cr.gettotalresultfromlink(needurl)
		if (not maxresult or maxresult <=0 or maxresult>total): 
			maxresult=total
		params={"rows":str(step)}
		maxround=(maxresult-offset)/step+1
		offsetcount=offset

		for i in range(maxround):
			params["offset"]=str(step*i+offset)
			r=requests.get(needurl,params,timeout=timeout_setting_download)
			if (r.status_code is 200):
				for j in r.json().get('message',{}).get('items',{}):
					keyword=j.get('title',[''])
					doi=DOI(j.get("DOI",""))
					if not doi:
						offsetcount+=1
						continue
					if (doi.freedownload()):
						offsetcount+=1
						continue
					if (keyword): 
						keyword=keyword[0]
					else:
						offsetcount+=1
						continue
					if usedoi:keyword+=" "+doi
					print "#####################################",offsetcount,"####################################"
					print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
					sys.stdout.flush()
					self.search(keyword.encode('utf-8'))
					bdresult=self.getallpdf(doifilter)
					for fbd in bdresult:
						self.pdfcheck.reset(fbd)
						dpfresult=self.pdfcheck.renamecheck(fbd)
						if (dpfresult!=0): 
							#Important to set fname to None
							rmresult=self.pdfcheck.removegarbage(fname=None)
						sys.stdout.flush()
					offsetcount+=1
			gc.collect()
		print "End of process for",issn