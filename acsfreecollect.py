#! /usr/bin/env python

import os,sys,gc,glob
import re,difflib,time,random,copy
import requests,urllib2,urlparse
from optparse import OptionParser
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

############ Global setting #############
escaper=HTMLParser()
#disable requests warning
requests.packages.urllib3.disable_warnings()

outfileprefix="downacsc307"

jshort=['achre4', 'jafcau', 'ancham', 'aamick', 'bichaw', 'bcches', 'bomaf6', 'abseba', 'accacs', 'acscii', 'acbcct', 'jceda8', 'jceaax', 'jcisd8', 'acncdm', 'crtoec', 'chreay', 'jctcce', 'cmatex', 'acsccc', 'cgdefu', 'enfuem', 'esthag', 'estlcu', 'iechad', 'iecred', 'aidcbc', 'inocaj', 'jacsat', 'langd5', 'amlccd', 'mamobx', 'jmcmar', 'amclct', 'mpohbp', 'ancac3', 'nalefd', 'jnprdf', 'joceah', 'orlef7', 'oprdfk', 'orgnd7', 'acsodf', 'apchd5', 'jpcafh', 'jpcbfk', 'jpccck', 'jpclcd', 'jpchax', 'jprobs', 'ascefj', 'ascecg', 'asbcd6', 'cenear']
jdone=['bichaw','jpcafh','jpccck', 'orlef7', 'joceah', 'jmcmar', 'inocaj','jacsat', 'acbcct','bomaf6']

jtodo=['enfuem','esthag','estlcu','iechad']

scriptre=re.compile(r"<script(.|\n)*?</script>")
for i in range(len(jtodo)):
	loi="http://pubs.acs.org/loi/"+jtodo[i]

	rloi=requests.get(loi)
	simpletext=scriptre.sub('',rloi.text)
	sloi=BeautifulSoup(simpletext, "html.parser")
	rows=sloi.findChildren("div",attrs={'class':'row'})

	issueurl=[ row.a['href'] for row in rows ]

	f=open(outfileprefix+str(i)+".txt",'a')
	for ilink in issueurl:
		print "Doing: "+ilink
		tmp=ilink.split('/')
		#if (int(tmp[-2])>43):
		#	continue
		#if (int(tmp[-2]) == 43 and int(tmp[-1]) >=11):
		#	continue
		try:
			r=requests.get(ilink)
			rs=BeautifulSoup(scriptre.sub("",r.text), "html.parser")
			eds=rs.findChildren(attrs={'class':"icon-item editors-choice"})
			aus=rs.findChildren(attrs={'class':"icon-item author-choice"})
			outs= [ out.parent.findChild(attrs={'class':"icon-item pdf-high-res"}).a['href'] for out in eds+aus] 
			corr=rs.findChildren(attrs={'id':'AdditionsandCorrections'})
			outs=outs+[out.parent.parent.findChild(attrs={'class':"icon-item pdf-high-res"}).a['href'] for out in corr]
			for out in outs:
				f.write(out+'\n')  
			#'/doi/pdf/10.1021/acs.jmedchem.5b00326'
			sys.stdout.flush()
			f.flush()
		except:
			pass

	f.close()
