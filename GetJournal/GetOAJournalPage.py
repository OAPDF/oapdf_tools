#! /usr/bin/env python
# Generate pages for OAPDF for Open Access Journal
# Last Update: 2016.1.15-4:30
import urllib2,os,sys,json,gc,re

userequests=True
try:
	import requests
except ImportError:
	userequests=False

# Is important! 
# If redirect is true, it always get the true link and parse whether pdf link in website.
# Else, if the website have two redirection to reallink, set redirect to False may cause wrong result! And It can't check pdf link.
# But, close redirect can improve speed. 
redirection=True

# Force rewrite the exist file
force=False

issn=""
offset=0
maxresult=500

browserhdr={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
p=re.compile(r"<title>.*?</title>")
pl=re.compile(r'(?<=<a href=\")http.*?(?=\">)')
ph=re.compile(r"</head>")

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def urlcovert(url):
	#for PNAS
	if ("www.pnas.org" in url):
		return url+'.full.pdf'
	elif('journals.plos.org/' in url):
		return url.replace('article?id','article/asset?id')+'.PDF'
	else:
		return ""

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
		r=urllib2.urlopen("http://oapdf.github.io/doilink/pages/"+decomposeDOI(doi,url=True,outdir=False)+".html")
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
	'''Combine pages of given directory to doilink directory'''
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

def genpage(doi, pdflink, reallink=None, fname=None):
	if (not fname):
		fname=decomposeDOI(doi,url=True,outdir=False,length=5)+".html"
	if (not reallink):
		url="http://38.100.138.163/"+doi
		try:
			r=urllib2.urlopen(url,timeout=20)
			if r.code == 200: 
				reallink=r.url
			else:
				print "Can't get real link for doi:",doi,'. Maybe network problem or wrong doi'
				return
		except:
			print "Can't get real link for doi:",doi,'. Maybe network problem or wrong doi'
			return
	fdirs=os.path.split(fname)
	if (not os.path.exists(fdirs[0])):os.makedirs(fdirs[0])
	fw=open(fname,'w')
	fw.write("<html><head><title>"+doi+'</title><meta name="robots" content="noindex,nofollow" /> <meta name="googlebots" content="noindex,nofollow" /></head><body>')
	fw.write('<iframe src="'+reallink+'" width="100%" height="96%"></iframe><div width="100%" align="center"><span style="align:center;">')
	fw.write('<a href="https://github.com/OAPDF/doilink/">OAPDF Project</a> : ')
	fw.write('<a href="https://scholar.google.com.hk/scholar?q='+doi+'">Google Scholar</a> | ')
	fw.write('<a href="http://xueshu.baidu.com/s?wd='+doi+'">Baidu Scholar</a> | ')
	fw.write('<a href="http://www.ncbi.nlm.nih.gov/pubmed/?term='+doi+'">PubMed</a> | ')
	fw.write('<a href="'+pdflink+'">PDFLink</a></span></div></body></html>')
	fw.close()

#############----------------------------###################

def findPDFbyISSN(issn,maxresult=None, step=100, offset=0):
	'''Find PDF by ISSN based on search result from crossref'''
	# may be improve to not only issn..
	if (not issn):return
	needurl="http://api.crossref.org/journals/"+issn+"/works"
	j1=needurl+"?rows=1"
	r=urllib2.urlopen(j1)
	j=json.loads(r.read())
	r.close()
	total=int(j['message']['total-results'])
	if (not maxresult or maxresult <=0 or maxresult>total): 
		maxresult=total-offset
	prefix="?rows="+str(step)
	maxround=maxresult/step+1
	offsetcount=offset
	for i in range(maxround):
		params=prefix+"&offset="+str(step*i+offset)
		try:
			r=urllib2.urlopen(needurl+params)
			js=json.loads(r.read())
			for j in js['message']['items']:
				doi=j.get("DOI","")
				if (is_oapdf(doi)):
					print "#####################################",offsetcount,"####################################"
					print "## Now Has OAPDF for doi:",doi,"Done! Next: "+str(offsetcount+1)
					offsetcount+=1
					continue
				if (doi):
					print "#####################################",offsetcount,"####################################"
					print "## Now Get PDF for doi:",doi, 
					#url="http://dx.doi.org/"+doi
					url="http://38.100.138.163/"+doi
					r2=urllib2.urlopen(url,timeout=20)
					urlreal=r2.url
					rpdf=urllib2.urlopen(urlcovert(urlreal),timeout=20)
					with open(quotefileDOI(doi)+".pdf",'wb') as pdf:
						pdf.write(rpdf.read())
					r2.close();rpdf.close()
					if (os.path.exists(quotefileDOI(doi)+".pdf")):
						print "Done! Next: "+str(offsetcount+1)
					else:
						print "Fail...."
				r.close()
				sys.stdout.flush()
				offsetcount+=1
		except:
			pass
		gc.collect()

def genPagebyISSN(issn,maxresult=None, step=1000, offset=0):
	'''Generate OAPDF Page by ISSN based on search result from crossref'''
	# may be improve to not only issn..
	if (not issn):return
	needurl="http://api.crossref.org/journals/"+issn+"/works"
	j1=needurl+"?rows=1"
	r=urllib2.urlopen(j1)
	j=json.loads(r.read())
	r.close()
	total=int(j['message']['total-results'])
	if (not maxresult or maxresult <=0 or maxresult>total): 
		maxresult=total-offset
	prefix="?rows="+str(step)
	maxround=maxresult/step+1
	offsetcount=offset
	for i in range(maxround):
		params=prefix+"&offset="+str(step*i+offset)
		try:
			r=urllib2.urlopen(needurl+params)
			js=json.loads(r.read())
			for j in js['message']['items']:
				doi=j.get("DOI","")
				#if (is_oapdf(doi)):
				#	print "#####################################",offsetcount,"####################################"
				#	print "## Now Has OAPDF for doi:",doi,"Done! Next: "+str(offsetcount+1)
				#	offsetcount+=1
				#	continue
				if (doi):
					print "#####################################",offsetcount,"####################################"
					print "## Now Generate Page for doi:",doi, 
					fname=decomposeDOI(doi,url=True,outdir=False,length=5)+".html"
					if (not force and os.path.exists(fname)):
						print "Done! Exist-Next: "+str(offsetcount+1)
						offsetcount+=1
						continue
					#url="http://dx.doi.org/"+doi
					url="http://38.100.138.163/"+doi
					urlreal=""
					if (not userequests):
						r2=urllib2.urlopen(url,timeout=20,headers=browserhdr)
						if (url.code == 200):
							urlreal=r2.url
							pdflink=urlcovert(urlreal)
							if (not pdflink):
								print "Error: Real link can't convert to pdf link!:", doi
								offsetcount+=1
								continue
							
							#check whether pdf link in webpage 
							if (re.search(re.escape(pdflink),r2.read(),flages=re.I)):
								genpage(doi, pdflink=pdflink, reallink=urlreal, fname=fname)
							else:
								print "Error: PDF link not found!:", doi
								offsetcount+=1
								continue
						else:
							print "Error: Wrong DOI!:", doi
							offsetcount+=1;continue
					else:
						r2=requests.get(url,allow_redirects=redirection,headers=browserhdr, timeout=200)
						if (r2.status_code != 404):
							if (redirection):
								urlreal=r2.url
							else:
								urlreal=pl.search(r2.text).group()
							pdflink=urlcovert(urlreal)
							if (not pdflink):
								print "Error: Real link can't convert to pdf link!:", doi
								offsetcount+=1;continue
							#check whether pdf link in webpage 
							if ( not redirection or (redirection and re.search(re.escape(pdflink), r2.text, re.I)) ):
								genpage(doi, pdflink=pdflink, reallink=urlreal, fname=fname)
							else:
								print "Error: PDF link not found!:", doi
								offsetcount+=1;continue
						else:
							print "Error: Wrong DOI!:", doi
							offsetcount+=1;continue
					
					### Check PDF if you need..
					#rpdf=urllib2.urlopen(urlcovert(urlreal),timeout=20)
					#with open(quotefileDOI(doi)+".pdf",'wb') as pdf:
					#	pdf.write(rpdf.read())
					#r2.close();rpdf.close()

					if (os.path.exists(fname)):
						print "Done! Next: "+str(offsetcount+1)
					else:
						print "Error: Fail to generate page...."
				r.close()
				sys.stdout.flush()
				offsetcount+=1
		except:
			pass
		gc.collect()	

if __name__ == "__main__":
	if (len(sys.argv)<2):
        	exit()
	elif (len(sys.argv)>=2):
		issn=sys.argv[1]
		if (len(sys.argv)>=3):
			offset=int(sys.argv[2])
			if (len(sys.argv)>=4):
				maxresult=int(sys.argv[3])
	#issn="1091-6490"
	#total=127499
	genPagebyISSN(issn,offset=offset,step=100,maxresult=maxresult);
