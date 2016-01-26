#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

'''Module for DOI and journal record operation
Also include the journal pdf function'''

import os,re
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup


timeout_setting=30
timeout_setting_download=120

################ ResearchGate Library ########################
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
		r=requests.get(link,params=rgparams,headers=browserhdr,timeout=timeout_setting)
		if r.status_code is 200:
			f=open(filename,'wb')
			f.write(r.content)
			f.close()
			if (os.path.exists(filename)): return True
		return False

	#https://www.researchgate.net/profile/Mira_Grdisa/publication/257690910_Synthesisi_and_antitumor_evaluation_of_some_new_substituted_amidino-benzimidazolyl-furyl-phenyl-acylates_and_naphthol21-bfuran-carboxylates
	#/links/00b49526526740bfd7000000.pdf?origin=publication_detail&ev=pub_int_prw_xdl&msrp=FIT9fTKuvW3Kaj1y6ZfsfDUdl27hHXP6ny0Ud6aICBJ_j0v-M_jAE6ebtBifmCz3yk0XLzqF494haG1hDnuyaA.lguBGVbspV5gVpKn5LGIr-DpFG2RPjl8HU6XmxBs08_1nWiKtITtyMlM9mqBMP2KrOk88HuM_ML7z1ll8e27VQ.CjwGWSeBW6lOrOvg4IGibp18nKEOKMwhD2hMEm1hz5W0N_Q38nkBNqviZN5epCRzsxzl3xw0eP3oeUh8_r-8Mw
	def getpdfByID(self,rgid):
		r=requests.get("https://www.researchgate.net/publication/"+str(rgid),headers=browserhdr,timeout=timeout_setting)
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