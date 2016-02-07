#! /usr/bin/env python

#### Usage:
# put this script in a repository root directory 
# It will scan the whole subdir pdf and generate html link for it in "html" and "pages" subdirectory

# Update: 2016.1.19 3:26AM

import os,sys,glob
import re, requests,urllib2
from itertools import chain

doilink='C:\\Users\\Hom\\Desktop\\MyGit\\platinhom\\OAPDF\\doilink'

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def filebasename(fname):
	'''Get the basic name without extension'''
	return os.path.splitext(os.path.basename(fname))[0]

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

if __name__ == '__main__':
	workingdir=os.path.abspath('.')
	pdf=True
	iglobonly=False
	count=0
	touchcount=1 #avoid start git submit
	gitsubmit=False
	if (len(sys.argv)>1):
		workdir=sys.argv[1].rstrip('\\').rstrip('/')
		if (len(sys.argv)>2 and sys.argv[2] != 's'):
			pdf=False
		elif(len(sys.argv)>2 and sys.argv[2] == 's'):
			gitsubmit=True
		if (len(sys.argv)>3):
			pdf=True
			iglobonly=True
	else:
		workdir='.'
	if (iglobonly):
		result=glob.iglob(workdir+os.sep+'10.*')
	else:
		if (pdf):
			result = (chain.from_iterable(glob.iglob(os.path.join(x[0], '10.*.pdf')) for x in os.walk(workdir)))
		else:
			result = (chain.from_iterable(glob.iglob(os.path.join(x[0], '10.*.html')) for x in os.walk(workdir)))

	for f in result:
		if (gitsubmit and touchcount%10000==0):
			os.chdir(doilink)
			print "Now start to submit......"
			os.system('git add -A')
			os.system('git commit -am "update"')
			rs=os.system('git push origin gh-pages')
			if (int(rs) != 0):
				rs=os.system('git push origin gh-pages')
			if (int(rs) != 0):
				print "Git submit fail!!! Check it!"
				sys.exit(1)
			os.chdir(workingdir)			
		if (os.path.isfile(f)):
			count+=1
			fname=filebasename(f)
			if (' ' in fname):
				print "File name has blank!",f
				os.renames(f,os.path.split(f)[0]+os.sep+fname.strip()+os.path.splitext(f)[1])
				fname=fname.strip()
			dirname=doilink+"/pages/"+decomposeDOI(unquotefileDOI(fname),url=False, outdir=True)
			if (not os.path.exists(dirname+fname+'.html')):
				touchcount+=1
				try:
					if (not os.path.exists(dirname)): os.makedirs(dirname)
					f=open(dirname+fname+'.html',"w")
					f.close()
				except WindowsError as e:
					print e
				except:
					print "Something error for file:",f
		else:
			for ff in glob.iglob(f+"/10.*.pdf"):
				count+=1
				fname=filebasename(ff)
				if (' ' in fname):
					print "File name has blank!",ff
					os.renames(ff,os.path.split(f)[0]+os.sep+fname.strip()+os.path.splitext(ff)[1])
					fname=fname.strip()
				dirname=doilink+"/pages/"+decomposeDOI(unquotefileDOI(fname),url=False, outdir=True)
				if (not os.path.exists(dirname+fname+'.html')):
					touchcount+=1
					try:
						if (not os.path.exists(dirname)): os.makedirs(dirname)
						os.system('touch '+dirname+fname+'.html')
					except WindowsError as e:
						print e
					except:
						print "Something error for file:",ff

	if (gitsubmit):
		os.chdir(doilink)
		print "Now start to submit......"
		os.system('git add -A')
		os.system('git commit -am "update"')
		rs=os.system('git push origin gh-pages')
		if (int(rs) != 0):
			rs=os.system('git push origin gh-pages')
		if (int(rs) != 0):
			print "Git submit fail!!! Check it!"
			sys.exit(1)
		os.chdir(workingdir)
	print "Process total file:",count,"; touch new:",touchcount-1
