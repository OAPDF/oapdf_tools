#! /usr/bin/env python

import os,sys,glob
import urllib2,json

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def maxissn(issns):
	maxissn="0000-0000"
	maxnum=0
	for i in range(len(issns)):
		if (issns[i] > maxissn):
			maxissn=issns[i]
			maxnum=i
			continue
	return issns[maxnum]


def getpdfdir(doi):
		'''Get only the larger issn, should normal doi'''
	#try:
		r=urllib2.urlopen('https://api.crossref.org/works/'+doi)
		j=json.loads(r.read())
		item=j['message']
		volume=item.get('volume','0')
		issue=item.get('issue','0')
		issn=maxissn(item.get('ISSN',['9999-9999']))
		return issn+os.sep+volume+os.sep+issue+os.sep
	#except:
	#	return ""
	
for f in glob.iglob('10.*/10.*.pdf'):
	paths=os.path.split(f)
	doi=unquotefileDOI(os.path.splitext(paths[1])[0]).strip()
	os.renames(f,paths[0]+os.sep+getpdfdir(doi)+paths[1])
	