#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''Basic function may be used in many place'''

import os,sys,re
import json,urllib2,difflib

######################## Part 1: General Functions ############################

def strdiff(str1, str2):
	'''Similarity of two string'''
	return difflib.SequenceMatcher(None, str1, str2).ratio()

def strsimilarity(longstr,shortstr,maxdistance=20,algorithm=2):
	'''Better algorithm for str similarity'''
	if (algorithm ==1):
		matching=difflib.SequenceMatcher(None,longstr,shortstr).get_matching_blocks()
		length=0
		lastposition=-1
		for item in matching:
			if (lastposition ==-1):
				lastposition=item[0]+item[2]
				length+=item[2]
			elif (item[0]-lastposition<=maxdistance):
				lastposition=item[0]+item[2]
				length+=item[2]	
			else:
				lastposition=item[0]+item[2]	
		return float(length)/len(shortstr)
	else:
		matching=difflib.SequenceMatcher(None,longstr,shortstr).get_opcodes()
		length=0
		lastposition=-1
		for item in matching:
			if (item[0] == 'equal'):
				if (lastposition ==-1):
					length+=item[4]-item[3]
					lastposition=item[2]
				elif (item[1]-lastposition <=maxdistance):
					length+=item[4]-item[3]
					lastposition=item[2]
				else:
					break
			elif(item[0] == 'replace'):
				lastposition=item[2]
		return float(length)/len(shortstr)								

def removeunicode(s):
	'''Remove non-ascii char'''
	out=''
	for i in range(len(s)):
		if (ord(s[i])<128):
			out+=s[i]
		else:
			out+=" "
	return str(out)

def normalizeString(s):
	'''Replace [!a-zA-Z0-9_] to blank'''
	return re.sub("\W+",' ',s)

def filebasename(fname):
	'''Get the basic name without extension'''
	return os.path.splitext(os.path.basename(fname))[0]

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def doidecompose(suffix):
	lens=len(suffix)
	if (lens<=5):
		return ""
	layer=(lens-1)/5
	dirurl=""
	for i in range(layer):
		## In window, dir name can't end at '.'
		item=suffix[i*5:(i+1)*5].rstrip('.')
		# Avoid 'con' file/folder name, maybe prn
		if (item[:4].lower() == 'con.'):
			item=item.replace('.','%2E',1)
		dirurl += item+"/"
	return dirurl

def decomposeDOI(doi, url=False, outdir=False, outlist=False, length=5):
	'''Decompose doi to a list or a url needed string.
	Only decompose the quoted suffix and prefix will be reserved.
	Note that dir name can't end with '.', so the right ends '.' will be delete here.
	Note that only support standard doi name, not prefix@suffix!
	If error, return "".

	Default, decompose to a dir name (related to doi).
	If url, output url string (containing quoted doi name)
	If outdir, output string for directory of doi
	If outlist, output to a list including quoted doi'''
	doi=doi.strip()
	doisplit=doi.split('/',1)
	if (len(doisplit) != 2):
		print "Error Input DOI:", doi.encode('utf-8')
		return ""
	prefix=doisplit[0]
	suffix=quotefileDOI(doisplit[1])
	lens=len(suffix)

	# Too short suffix
	if (lens<=length):
		if outdir: 
			prefix+"/"
		if (url):
			return prefix+"/"+prefix+"@"+suffix
		elif (outlist):
			return [prefix,suffix]
		else:
			return prefix+"/"

	# Decompose suffix
	layer=(lens-1)/length
	dirurl=[prefix]
	for i in range(layer):
		item=suffix[i*length:(i+1)*length].rstrip('.')
		if (item[:4].lower() == 'con.'):
			item=item.replace('.','%2E',1)
		dirurl.append(item)

	if (outdir):
		return "/".join(dirurl)+"/"
	elif (url):
		return "/".join(dirurl)+"/"+prefix+"@"+suffix
	elif (outlist):
		dirurl.append(suffix[(lens-1)/length*length:])
		return dirurl
	# Default return dir string for doi
	else: 
		return "/".join(dirurl)+"/"

def is_oapdf(doi,check=False):
	'''Check the doi is in OAPDF library'''
	if (check and "/" not in doi and "@" in doi):
		doi=unquotefileDOI(doi)
	try:#urllib maybe faster then requests
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+decomposeDOI(doi,url=True)+".html",timeout=timeout_setting)
		return (r.code is 200)
	except:
		return False

def has_oapdf_pdf(doi,check=False):
	'''Check whether the doi has in OAPDF library'''
	if (check and "/" not in doi and "@" in doi):
		doi=unquotefileDOI(doi)
	tmp=doi.split('/',1)
	if (len(tmp) is not 2):return False
	prefix=tmp[0]
	quoted=quotefileDOI(doi)
	try:#urllib maybe faster then requests
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+prefix+"/path/"+quoted+".html",timeout=timeout_setting)
		return (r.code is 200)
	except:
		return False

def valid_doaj(doi):
	'''Valid the DOI is Open Access by DOAJ'''
	r=urllib2.urlopen('https://doaj.org/api/v1/search/articles/doi:'+doi,timeout=timeout_setting)
	return json.loads(r.read()).get('total',0)>0

def __doifilerename(fname):
	'''A function for old doi_pdf filename format'''
	if ('/' not in fname and '@' not in fname and '_' in fname):
		try:
			os.renames(fname, fname.replace('_','@',1))
			return fname.replace('_','@',1)
		except WindowsError as e:
			print e
	return fname

def pdfexistpath(fname):
	if (os.path.exists(fname) or os.path.exists('Done/'+fname)\
		or os.path.exists('High/'+fname) or os.path.exists('Unsure/'+fname)\
		or os.path.exists('Fail/'+fname) or os.path.exists('Untitle/'+fname) ):
		return True
	else:
		return False

def browsercookiesdict(s):
	'''Covert cookies string from browser to a dict'''
	ss=s.split(';')
	outdict={}
	for item in ss:
		i1=item.split('=',1)[0].strip()
		i2=item.split('=',1)[1].strip()
		outdict[i1]=i2
	return outdict