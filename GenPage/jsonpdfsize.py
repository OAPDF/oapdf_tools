#! /usr/bin/env python

import os,sys,glob,time
import re, urllib2,json

username="oapdf1"
doilinkdir='../doilink'

workingdir=os.path.abspath('.')
nowdir=os.path.basename(os.path.abspath(os.path.curdir))

def doidecompose(suffix):
	lens=len(suffix)
	if (lens<=5):
		return ""
	layer=(lens-1)/5
	dirurl=""
	for i in range(layer):
		## In window, dir name can't end at '.'
		dirurl += suffix[i*5:(i+1)*5].rstrip('.')+"/"
	return dirurl

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def is_oapdf(doi,check=False):
	'''Check the doi is in OAPDF library'''
	if (check and "/" not in doi and "@" in doi):
		doi=unquotefileDOI(doi)
	try:#urllib maybe faster then requests
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+decomposeDOI(doi,url=True)+".html")
		return (r.code is 200)
	except:
		return False

outdict={"owner":username, "repo":nowdir}
fmove={}
fcount=0
ig=glob.iglob("10.*/10.*.pdf")
for f in ig:
	fsize=os.path.getsize(f)
	fmove[f]=fsize
	fcount+=1

fmovefname={}
for k,v in fmove.items():
	fname=os.path.split(k)[1]
	fmovefname[fname]=v
	sout=(fmovefname)

outdict['total']=fcount
outdict['items']=fmovefname

f=open(doilinkdir+os.sep+nowdir+"@"+username+".json",'w')
f.write(json.dumps(outdict))
f.close()

fmove.clear()
fmovefname.clear()
