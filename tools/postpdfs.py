#! /usr/bin/env python
# -*- coding: utf-8 -*-

''' Usage:
# Use -h/--help to see the usage
- Compare the pdf to the sizes in library
- Touch static page for new pdf record
- Move pdf to prefix or issn/volume/issue folder
- Generate pdf-size json file
- Update pdf-size in library
'''

__author__='oapdf'
__date__='2016-2-7 05:30'

from oapdf.doi import DOI
from oapdf.basic import *
from oapdf.pdfhandler import PDFHandler
from optparse import OptionParser

import os,sys,glob,json,time
import re, requests,urllib2
from itertools import chain
from bs4 import BeautifulSoup

# Use to save local page record
username="360"
workingdir=os.path.abspath('.')
nowdir=os.path.basename(os.path.abspath(os.path.curdir))

def similarsize(s1,s2):
	i1=int(s1)
	i2=int(s2)
	if (i1 == i2):
		return 0
	if (abs(i1-i2)/float(min(i1,i2)) < 0.1):
		return 1
	else:
		return -1

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

########################################################################################

def moveprefix(origin='.'):
	'''Just move the PDFs in the origin folder to their prefix sub-folder'''
	pdffiles=glob.glob(origin+os.sep+"10.*.pdf")
	for pdf in pdffiles:
		fname=os.path.split(pdf)[1]
		doi=DOI(filebasename(pdf))
		if (not os.path.exists(origin+os.sep+doi.prefix)): 
			os.makedirs(origin+os.sep+doi.prefix)
		if (not os.path.exists(origin+os.sep+doi.prefix+os.sep+fname)):
			os.renames(pdf,origin+os.sep+doi.prefix+os.sep+fname)

def moveissn(origin='.',prefixdir=True):
	'''Move files to their ISSN/Volume/Issue folder
	Files can be in prefix dir (prefixdir) or just in a folder'''

	targetfiles= '10.*/10.*.pdf' if prefixdir else '10.*.pdf'
	for f in glob.iglob(origin+os.sep+targetfiles):
		doi=DOI(filebasename(f))
		os.renames(f,origin+os.sep+doi.prefix+os.sep+getpdfdir(doi)+doi.quote()+'.pdf')

def genjson(origin='.', target='.', username="360", iterfolder=False):
	'''Generate a json file for a folder PDFs with their size information'''
	nowdir=os.path.basename(os.path.abspath(origin))#os.path.curdir))
	outdict={"owner":username, "repo":nowdir}
	fmove={}
	fcount=0
	if (not iterfolder):
		ig=glob.iglob(origin+os.sep+"10.*/10.*.pdf")
	else:
		ig = (chain.from_iterable(glob.iglob(os.path.join(x[0], '10.*.pdf')) for x in os.walk(origin)))

	for f in ig:
		fsize=os.path.getsize(f)
		fmove[f]=fsize
		fcount+=1

	fmovefname={}
	for k,v in fmove.items():
		fname=os.path.split(k)[1]
		fmovefname[fname]=v

	outdict['total']=fcount
	outdict['items']=fmovefname

	f=open(target+os.sep+nowdir+"@"+username+".json",'w')
	f.write(json.dumps(outdict))
	f.close()

	fmove.clear()
	fmovefname.clear()
	return target+os.sep+nowdir+"@"+username+".json"

def touchpage(origin='.', doilink='../doilink',pdf=True,force=False):
	# Use to save local page record
	if not os.path.exists(doilink):
		os.makedirs(doilink+os.sep+'pages')
	doilink=doilink.rstrip('/').rstrip('\\')
	sfurl="http://oapdf.sourceforge.net/cgi-bin/touchdoi.cgi?owner=oapdf"

	workdir=os.path.abspath(origin).rstrip('\\').rstrip('/')
	count=0
	touchcount=1 # avoid submit when start
	forcesf=force # force to overwrite the exist doilink page

	if (pdf):
		result = (chain.from_iterable(glob.iglob(os.path.join(x[0], '10.*.pdf')) for x in os.walk(workdir)))
	else:
		result = (chain.from_iterable(glob.iglob(os.path.join(x[0], '10.*.html')) for x in os.walk(workdir)))

	toappend=[]
	newtouch=0
	for f in result:
		if (touchcount%100==0):
			r=requests.post(sfurl,params={'dois':json.dumps(toappend)},timeout=120)
			if (r.status_code == 200):
				bs=BeautifulSoup(r.text,"html.parser")
				totaldid=bs.findChild('span',attrs={'id':'total'})
				if totaldid and totaldid.text :
					newtouch+=int(totaldid.text)
				del toappend[:]
			else:
				print "Maybe Error when submit to SF-OAPDF.."
				sys.exit(1)
		count+=1
		fname=filebasename(f)
		if (' ' in fname):
			print "File name has blank!",f
			os.renames(f,os.path.split(f)[0]+os.sep+fname.strip()+os.path.splitext(f)[1])
			fname=fname.strip()
		doi=DOI(fname)
		if (doi):
			dirname=doilink+"/pages/"+doi.decompose(url=False, outdir=True)
			if (forcesf or not os.path.exists(dirname+fname+'.html')):
				touchcount+=1
				toappend.append(doi)
				try:
					if (not os.path.exists(dirname)): os.makedirs(dirname)
					f=open(dirname+fname+'.html',"w")
					f.close()
				except WindowsError as e:
					print e
				except:
					print "Something error for file:",f
		else:
			print "File name may be error (Not DOI name):",fname

	r=requests.post(sfurl,params={'dois':json.dumps(toappend)},timeout=120)
	if (r.status_code == 200):
		bs=BeautifulSoup(r.text,"html.parser")
		totaldid=bs.findChild('span',attrs={'id':'total'})
		if totaldid and totaldid.text :
			newtouch+=int(totaldid.text)
		del toappend[:]
	else:
		print "Maybe Error when submit to SF-OAPDF.."
		sys.exit(1)
	print "Process total file:",count,"; local touch new:",touchcount-1, "; remote touch:",newtouch

ph=PDFHandler()
def comparepdfsizeMove(totalfiles,sfresult,target='Done',check=False):
	# Start to compare
	for fg in totalfiles: #glob.iglob(origin+os.sep+'10.*.pdf'):
		fnamesplit=os.path.split(fg)
		doi=DOI(filebasename(fg))
		if (doi):
			fpath=fg.strip().split('@',1)
			fsize=os.path.getsize(fg)
			printout=""
			if (not sfresult.has_key(doi)):
				if (not check or ph.FastCheck(fg)):
					targetfname=target+os.sep+fnamesplit[1]
					try:
						os.renames(fg,targetfname)
					except:
						if (os.path.exists(targetfname)):
							if (similarsize(fsize,os.path.getsize(targetfname))>=0):
								os.remove(fg)
						else:					
							print "Move fail...",fg
				else:
					print 'File maybe wrong..',fg
			else:
				for line in sfresult[doi]:
					s=similarsize(fsize,str(line).strip())
					if ( s >= 0):
						os.remove(fg)
						printout=""
						break
					#elif ( s is 1 and int(fsize)<int(line.strip())):
					#	os.remove(fg)
					#	printout=""
					#	break				
					else:
						printout=fg+" now size: "+str(fsize)+"; in lib: "+str(line).strip()
				if (printout): print printout
		else:
			print "File is not in doi style!",fg


def comparepdfsize(origin='.',target='Done',check=False, totalsize=None):
	'''Compare PDF size in origin to online library.
	If new, move to target folder'''
	if not os.path.exists(origin):
		print "The origin folder not exist! Exit!"
		sys.exit(1)

	if (not os.path.exists(target)):
		os.makedirs(target)

	if (totalsize and float(totalsize)>0):
		totalsize=float(totalsize)*1000000000

	sfurl="http://oapdf.sourceforge.net/cgi-bin/pdfsize.cgi?owner=oapdf"
	workingdir=os.path.abspath('.')

	# Get online informations
	count=0
	sfresult={}
	tmpdois=set()
	totalfiles=[]
	nowsizes=0
	for fg in glob.iglob(origin+os.sep+'10.*.pdf'):
		if nowsizes>totalsize:
			break
		
		doi=DOI(filebasename(fg))
		if (doi):
			count+=1
			totalfiles.append(fg)
			nowsizes+=os.path.getsize(fg)

			if (count%100 == 0):
				# Firstly, query the records
				try:
					r=requests.post(sfurl,params={'dois':json.dumps(list(tmpdois))},timeout=120)
				except requests.RequestException:
					r=requests.post(sfurl,params={'dois':json.dumps(list(tmpdois))},timeout=120)

				if (r.status_code ==200):
					sfresult.update(r.json())
					tmpdois.clear()

					comparepdfsizeMove(totalfiles,sfresult,target=target,check=check)
					del totalfiles[:]
					sfresult.clear()
					#time.sleep(2)
			tmpdois.add(doi)
			
	if (len(tmpdois)>0):
		r=requests.post(sfurl,params={'dois':json.dumps(list(tmpdois))},timeout=120)
		if (r.status_code ==200):
			sfresult.update(r.json())
			tmpdois.clear()

			comparepdfsizeMove(totalfiles,sfresult,target=target,check=check)
			del totalfiles[:]
			sfresult.clear()


def genpdfsize(jsfnames):
	'''Generate PDF information on SF library'''
	sfurl="http://oapdf.sourceforge.net/cgi-bin/pdfsize.cgi?owner=oapdf"
	count=0
	tmpdoisize={}
	tmpdois=set()
	toappend={}
	if isinstance(jsfnames,str):
		jsfnames=[jsfnames]

	for jf in jsfnames:
		f=open(jf)
		j=json.loads(f.read())
		f.close()
		for pdf,fs in j['items'].items():
			count+=1
			if (count%100 == 0):
				# Firstly, query the records
				r=requests.post(sfurl,params={'dois':json.dumps(list(tmpdois))},timeout=120)
				result=r.json()
				for d,s in tmpdoisize.items():
					if (not set(s).issubset(set(result.get(d,[])))):
						toappend[d]=list(set(s+result.get(d,[])))
				if (len(toappend)>0):
					rr=requests.post(sfurl,params={'doisize':json.dumps(toappend),'update':"True"},timeout=120)
					if (rr.status_code == 200):
						#print rr.text
						#if fail, submit at next time
						tmpdoisize.clear()
						tmpdois.clear()
						toappend.clear()
				else:
					tmpdoisize.clear()
					tmpdois.clear()
					toappend.clear()				
				time.sleep(2)
			doi=DOI(filebasename(pdf))
			tmpdois.add(doi)
			tmpdoisize.setdefault(doi,[]).append(fs)

	if (len(tmpdois)>0):
		# Firstly, query the records
		r=requests.post(sfurl,params={'dois':json.dumps(list(tmpdois))},timeout=120)
		result=r.json()
		for d,s in tmpdoisize.items():
			if (not set(s).issubset(set(result.get(d,[])))):
				toappend[d]=list(set(s+result.get(d,[])))
		if (len(toappend)>0):
			rr=requests.post(sfurl,params={'doisize':json.dumps(toappend),'update':"True"},timeout=120)
			if (rr.status_code == 200):
				#print rr.text
				#if fail, submit at next time
				tmpdoisize.clear()
				tmpdois.clear()
				toappend.clear()
		else:
			tmpdoisize.clear()
			tmpdois.clear()
			toappend.clear()
	print "Total done for:",count


if __name__ == '__main__':

	helpdes="Process PDF files after collection"

	parser = OptionParser(description=helpdes) 

	parser.add_option("-c", "--compare", action="store", 
					dest="compare", default="",
					help="Compare the PDF in this folder to online library")	
	parser.add_option("--fast", action="store_true", 
					dest="fast", default=False,
					help="Fast check PDF whether it's valid")
	parser.add_option("--size", action="store", 
					dest="size", default="",
					help="The total size of PDFs to be compared (in GB)")

	parser.add_option("-g", "--generate", action="store_true", 
					dest="generate", default=False,
					help="generate the PDF information based on json file to online library")
	parser.add_option("-t", "--touch", action="store", 
					dest="touch", default="",
					help="Touch static file in online library")	
	parser.add_option("--doilink", action="store", 
					dest="doilink", default="",
					help="Local doilink path, default ../doilink")		
	parser.add_option("-o", "--out", action="store", 
					dest="out", default="",
					help="Move the PDF/Generate files to the target folder")

	parser.add_option("-a", "--all", action="store", 
					dest="all", default="",
					help="Multisteps: moveprefix, touchpage, gen-json, gen-decoypdf, moveissn")

	parser.add_option("-m", "--moveprefix", action="store", 
					dest="moveprefix", default="",
					help="Move PDF to the prefix folder")	
	parser.add_option("-i", "--issn", action="store", 
					dest="issn", default="",
					help="Move PDF to the issn folder (ISSN/Volume/Issue)")
	parser.add_option("--noprefix", action="store_true", 
					dest="noprefix", default=False,
					help="Move PDF (not in prefix folder) to the issn folder")	
	
	parser.add_option("-j", "--json", action="store", 
					dest="json", default="",
					help="Generate Json file (pdf:size) for a folder")
	parser.add_option("--user", action="store", 
					dest="user", default="",
					help="The user of repository")
	parser.add_option("--iter", action="store_true", 
					dest="iter", default=False,
					help="Iterated to the sub-folder (when genjson")

	(options, args) = parser.parse_args()

	targetdir=options.out

	if (options.compare):
		if (not targetdir):targetdir='Done'
		if (not options.size):options.size=None
		print "Start comparing pdf file with size..."
		comparepdfsize(origin=options.compare,target=targetdir,check=options.fast,totalsize=options.size)
		sys.exit()

	if options.all:
		print "Start moving..."
		moveissn(origin=options.all,prefixdir=False)
		
		if not options.doilink: options.doilink='../doilink'
		print "Start touching..."
		touchpage(origin=options.all, doilink=options.doilink,pdf=True,force=False)

		if (not targetdir):targetdir='.'
		if not options.user: options.user='360'
		print "Start to generate json for pdf size.."
		jf=genjson(origin=options.all, target=targetdir, username=options.user, iterfolder=True)
		
		print "Start to update pdf size in online library.."
		genpdfsize(jf)

	if options.moveprefix:
		print "Start moving..."
		moveprefix(options.moveprefix)

	if options.touch:
		if not options.doilink: options.doilink='../doilink'
		print "Start touching..."
		touchpage(origin=options.touch, doilink=options.doilink,pdf=True,force=False)

	jf=""
	if options.json:
		if (not targetdir):targetdir='.'
		if not options.user: options.user='360'
		print "Start to generate json for pdf size.."
		jf=genjson(origin=options.json, target=targetdir, username=options.user, iterfolder=options.iter)

	if options.generate:
		if jf: args.append(jf)
		print "Start to update pdf size in online library.."
		genpdfsize(args)

	if options.issn:
		print "Start moving..."
		moveissn(origin=options.issn,prefixdir= (not options.noprefix))






	
