#! /usr/bin/env python
import urllib2,os,sys,json,gc

issn=""
offset=0
maxresult=500

def quotefileDOI(doi):
	'''Quote the doi name for a file name'''
	return urllib2.quote(doi,'+/()').replace('/','@')

def unquotefileDOI(doi):
	'''Unquote the doi name for a file name'''
	return urllib2.unquote(doi.replace('@','/'))

def urlcovert(url):
	#for PNAS
	return url+'.full.pdf'

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
	findPDFbyISSN(issn,offset=offset,step=100,maxresult=maxresult);
