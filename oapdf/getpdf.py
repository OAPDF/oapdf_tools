#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

import os,re
import requests,urlparse
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup


TIMEOUT_SETTING=30
TIMEOUT_SETTING_DOWNLOAD=120

################### Part4: PDF related library ########################

def adjustpdflink(link):
	'''Adjust some links to correct address'''
	if ("europepmc.org/abstract/MED" in link):
		r=requests.get(link,timeout=TIMEOUT_SETTING)
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
	elif ("//www.researchgate.net/publication" in link):
		return {"inViewer":"0","pdfJsDownload":"0","origin":"publication_detail"}
	elif ("//www.researchgate.net/profile" in link):
		return {"origin":"publication_detail"}
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

browserhdr={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
def getwebpdf(link,fname,params=None, force=False):
	'''Get a PDF from a link. if fail, return False'''
	#Have been downloaded...
	if (not force and os.path.exists(fname)):
		return True
	if (not link):
		return False
	try:
		if (params and isinstance(params,dict) ):
			rpdf=requests.get(link,params=params,headers=browserhdr,timeout=TIMEOUT_SETTING)
		else: rpdf=requests.get(link,headers=browserhdr,timeout=TIMEOUT_SETTING)
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
	except requests.exceptions.ChunkedEncodingError:
		return False
	print "Can't find pdf at link: "+link
	return False