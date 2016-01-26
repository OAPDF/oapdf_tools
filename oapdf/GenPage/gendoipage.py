#! /usr/bin/env python

#### Usage:
# put this script in a repository root directory 
# It will scan the whole subdir pdf and generate html link for it in "html" and "pages" subdirectory

# Update: 2016.1.19 3:26AM

import os,sys,glob
import re, requests,urllib2

# User link for repository
userlink="https://github.com/oapdf1/"
# Setup the doilink dir

# doilink dir is for doilink saving
doilinkdir="../doilink/"
outdoilinkdir=doilinkdir+"pages/"

#oapdfdir="../doilink/"
oapdfdir="_pages/"
outdir="pages/"
if (oapdfdir):
	outdir=oapdfdir+outdir
#if (not os.path.exists("html")): os.makedirs("html")
if (not os.path.exists(outdir)): os.makedirs(outdir)

# Force rewrite the existing file
force=False
combine=False
# Default method
postcombine=True

if (len(sys.argv)>1): 
	if sys.argv[1]  == 'f': 
		force = True; postcombine=False
	elif sys.argv[1] == 'c': 
		combine=True; postcombine=False
	elif sys.argv[1] == 'n': 
		postcombine=False

nowdir=os.path.basename(os.path.abspath(os.path.curdir))
p=re.compile(r"<title>.*?</title>")
pl=re.compile(r'(?<=<a href=\")http.*?(?=\">)')
ph=re.compile(r"</head>")

########## Function

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
		dirurl.append(suffix[i*length:(i+1)*length].rstrip('.'))

	if (outdir):
		"/".join(dirurl)+"/"
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
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+decomposeDOI(doi,url=True)+".html")
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
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+prefix+"/path/"+quoted+".html")
		return (r.code is 200)
	except:
		return False

def combinepage(fname,outdir='_pages/pages/',outdoilinkdir='../doilink/pages/'):
	'''Only suitable here'''
	if (outdir == doilinkdir):return
	doifname=fname.replace(outdir,outdoilinkdir,1)
	if (not os.path.exists(fname)):return
	f=open(fname);s2=f.read();f.close()

	doidir=os.path.split(doifname)[0]
	if (not os.path.exists(doifname)):
		try:
			if (not os.path.exists(doidir)): os.makedirs(doidir)
			f=open(doifname,'w');
			f.write(s2);
			f.close()
		except Exception as e:
			print e
			print "Can't write out to doilink file:",doifname
		return

	f=open(doifname);s1=f.read();f.close()
	pp1=s1.find('PubMed</a>')
	pp2=s2.find('PubMed</a>')
	cp1=s1[pp1:].find('|')#maybe rfind('|') will good, by if | exist at end?
	cp2=s2[pp1:].find('|')
	links1=pl.findall(s1[pp1+cp1:])
	links2=pl.findall(s2[pp2+cp2:])
	for link in links2:
		if link not in links1:
			links1.append(link)
	linkstr=""
	for i in range(len(links1)):
		if (i is 0):
			linkstr+='<a href="'+links1[i]+'">PDFLink</a>'
		else:
			linkstr+=',<a href="'+links1[i]+'">'+str(i+1)+'</a>'
	f=open(doifname,'w')
	f.write(re.sub(r'PubMed</a>.*?</span>','PubMed</a> | '+linkstr+'</span>',s1))
	f.close()
	print "Successful combine for:",fname, 'with',len(links1), 'links'

############ Start #############

# if _pages, don't submit to github
if (oapdfdir =='_pages/' or oapdfdir =='./_pages/' ):
	if (os.path.exists('.gitignore')):
		f=open('.gitignore')
		s=f.read();f.close()
		if ('_pages/' not in s):
			f=open('.gitignore','a')
			f.write('_pages/'+'\n')
			f.close()
	else:
		f=open('.gitignore','a')
		f.write('_pages/'+'\n')
		f.close()

# do the combine! You'd better move the not repeat file to doilink firstly! 
if (combine):
	result = [os.path.join(dp, f) for dp, dn, filenames in os.walk("_pages/pages/") for f in filenames if os.path.splitext(f)[1] == '.html']
	for fname in result:
		combinepage(fname,outdir,outdoilinkdir)
	sys.exit(0)

findpdffiles=glob.glob("10.*.pdf")
for pdffile in findpdffiles:
	# if is a file , move it
	if (os.path.isfile(pdffile)):
		dois=pdffile.split("@",1)
		if (not os.path.exists(dois[0])): 
			os.makedirs(dois[0])
		if (not os.path.exists(dois[0]+os.sep+pdffile)):
			os.renames(pdffile,dois[0]+os.sep+pdffile)

prefixdir=glob.glob("10.*")
for prefix in prefixdir:
	# if is a file , move it
	if (os.path.isfile(prefix)):
		### May be some repeat pdf save in here
		dois=prefix.split("@",1)
		if (os.path.exists(dois[0]+os.sep+prefix)):
			f1size=os.path.getsize(prefix)
			f2size=os.path.getsize(dois[0]+os.sep+prefix)
			if (f1size==f2size):
				os.remove(prefix)
			elif(f1size-f2size<300000 and f1size>f2size):
				try:
					os.remove(dois[0]+os.sep+prefix)
					os.renames(prefix,dois[0]+os.sep+prefix)
				except:
					print "Move fail..",prefix
		continue
	#if (not os.path.exists("html/"+prefix)): 
	#	os.makedirs("html/"+prefix)
	if (not os.path.exists(outdir+prefix)): 
		os.makedirs(outdir+prefix)
	for pd in glob.iglob(prefix+"/*.pdf"):
		try:
			doi=pd.split(os.sep)[1][:-4]
			doiat=doi.replace("/","@")
			dois=doiat.split("@",1)
			doi1=dois[0]
			doi2=dois[1]
			suffixpath=doidecompose(doi2)
			#htmldir="html/"+prefix+"/"+suffixpath;
			pagedir=outdir+prefix+"/"+suffixpath;

			#if (os.path.exists(htmldir+doiat+".html") and os.path.exists(pagedir+doiat+".html")):

			### if force rewrite, rewrite it
			if (not force and os.path.exists(pagedir+doiat+".html")):
				if (postcombine and not os.path.exists(outdoilinkdir+prefix+"/"+suffixpath+doiat+".html")): 
					combinepage(pagedir+doiat+".html",outdir,outdoilinkdir)
				continue
			realdoi=doiat.replace("@","/")
			#may be wrong if origin doi has @
			link="http://dx.doi.org/"+realdoi
			r=requests.get(link,allow_redirects=False)
			title=p.search(r.text).group().lower()
			reallink=""
			if ("redirect" in title):
				reallink=pl.search(r.text).group()
				pdflink=userlink+nowdir+"/raw/master/"+prefix+"/"+doiat+".pdf"
				#if (not os.path.exists(htmldir)): os.makedirs(htmldir)
				if (not os.path.exists(pagedir)): os.makedirs(pagedir)
				##write html page
				#fw=open(htmldir+doiat+".html",'w')
				#fw.write(ph.sub('<script>window.location.href="'+pdflink+'"</script></head>',r.text))
				#fw.close()

				fw=open(pagedir+doiat+".html",'w')
				fw.write("<html><head><title>"+realdoi+'</title><meta name="robots" content="noindex,nofollow" /> <meta name="googlebots" content="noindex,nofollow" /></head><body>')
				fw.write('<iframe src="'+reallink+'" width="100%" height="96%"></iframe><div width="100%" align="center"><span style="align:center;">')
				fw.write('<a href="https://github.com/OAPDF/doilink/">OAPDF Project</a> : ')
				fw.write('<a href="https://scholar.google.com.hk/scholar?q='+realdoi+'">Google Scholar</a> | ')
				fw.write('<a href="http://xueshu.baidu.com/s?wd='+realdoi+'">Baidu Scholar</a> | ')
				fw.write('<a href="http://www.ncbi.nlm.nih.gov/pubmed/?term='+realdoi+'">PubMed</a> | ')
				fw.write('<a href="'+pdflink+'">PDFLink</a></span></div></body></html>')
				fw.close()

				if (force):
					if (not os.path.exists(outdoilinkdir+prefix+"/"+suffixpath)): os.makedirs(outdoilinkdir+prefix+"/"+suffixpath)
					fw=open(outdoilinkdir+prefix+"/"+suffixpath+doiat+".html",'w')
					fw.write("<html><head><title>"+realdoi+'</title><meta name="robots" content="noindex,nofollow" /> <meta name="googlebots" content="noindex,nofollow" /></head><body>')
					fw.write('<iframe src="'+reallink+'" width="100%" height="96%"></iframe><div width="100%" align="center"><span style="align:center;">')
					fw.write('<a href="https://github.com/OAPDF/doilink/">OAPDF Project</a> : ')
					fw.write('<a href="https://scholar.google.com.hk/scholar?q='+realdoi+'">Google Scholar</a> | ')
					fw.write('<a href="http://xueshu.baidu.com/s?wd='+realdoi+'">Baidu Scholar</a> | ')
					fw.write('<a href="http://www.ncbi.nlm.nih.gov/pubmed/?term='+realdoi+'">PubMed</a> | ')
					fw.write('<a href="'+pdflink+'">PDFLink</a></span></div></body></html>')
					fw.close()

				if (not force and postcombine): combinepage(pagedir+doiat+".html",outdir,outdoilinkdir)

			else:
				print doi, " Error Link!"
				try:
					os.renames(pd, pd.split(os.sep)[1])
				except:
					f=open(pd.split(os.sep)[1]+".error",'w');
					f.write(pd)
					f.close()
		except:
			pass



