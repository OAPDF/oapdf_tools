#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

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
	from .jrecord import Jrecord
except (ImportError,ValueError) as e:
	from doi import DOI
	from crrecord import CRrecord
	from basic import *
	from getpdf import *
	from jrecord import Jrecord

timeout_setting=30
timeout_setting_download=120

############### Bing Academey Search Related ########################

class BingAcademic(object):
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
			r=requests.get(self.bingacademicurl,params=param,headers=self.hdr,timeout=timeout_setting)
			if (r.status_code is 200):
				soup=BeautifulSoup(r.text, "html.parser")
				findpdflinkresult=soup.find_all(attrs={"class":"b_citeItem"})
				bids=bids+[self.bidre.search(str(s)).group() for s in findpdflinkresult]
		return bids

	def findpdfbid(self,inq,maxpage=1):
		'''Get maxpage pages pdf links in searching results for inq keyword in bing academic'''
		#inq=re.sub(r"\s+","+",inq)
		#inq=removeunicode(inq)
		bids=[]
		if (maxpage<1):maxpage=1
		if (maxpage>10):maxpage=10
		for pagei in range(maxpage):
			startpage=pagei*10+1
			param={"mkt":"zh-CN",'q':inq,'first':str(startpage)}
			try:
				r=requests.get(self.bingacademicurl,params=param,headers=self.hdr,timeout=timeout_setting)
				print r.url
				#f=open('ac.html','w');f.write(r.text.encode('utf-8'));f.close()
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
				j=Jrecord()
				return j.parseenw(r.text)
			return Jrecord()
		except requests.exceptions.ConnectionError:
			print "ConnectionError: Fail to find ref info for bid: "+bid
			return Jrecord()

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
		cr=CRrecord()
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
				if (printyn): print cr
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
		cr=CRrecord()
		if( cr.getfromdoi(doi,fullparse=False) and cr.doi):
			keyword=(cr.title+" "+cr.doi).encode('utf-8')
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

	def findPDFbyISSN(self,issn,maxresult=None, step=100, offset=0):
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
				for j in r.json()['message']['items']:
					keyword=j.get('title',[''])[0]+" "+j.get("DOI","")
					print "#####################################",offsetcount,"####################################"
					print "## Now finding for doi with title: "+ keyword.encode('utf-8')+"............"
					sys.stdout.flush()
					bingacad.grepBingAcadPDF(keyword.encode('utf-8'))
					offsetcount+=1
			gc.collect()