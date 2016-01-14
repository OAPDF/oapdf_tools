#! /usr/bin/env python
import sys,os,shutil,time
import urllib2 as ul2
import random

#doi="10.1021/ci960138u"
#my_headers = ['Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)',
#    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; InfoPath.1',
#    'Mozilla/4.0 (compatible; GoogleToolbar 5.0.2124.2070; Windows 6.0; MSIE 8.0.6001.18241)',
#    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
#    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; Sleipnir/2.9.8)']

f=open(sys.argv[1])
if (not os.path.exists("Done/")): 
	os.makedirs("Done")
failcount=0
for l in f:
	doi=l.strip().strip('/')
	doisplit=doi.split('/')
	doiout="_".join(doisplit)
	if (len(doisplit)<2):
		print "Error DOI:"+doi
		continue
	if os.path.exists("./"+doiout+".pdf"):
		continue
	if os.path.exists("Done/"+doiout+".pdf"):
		continue
	if os.path.exists("Accept/"+doiout+".pdf"):
		continue
	if os.path.exists("Done/"+doi.split('/',1)[1]+"/"):
		continue	
	try:
		link="http://sci-hub.io/"+doi
		#random_header = random.choice(my_headers)
		#req=ul2.Request(link)
		#req.add_header("User-Agent",random_header)
		#req.add_header('Host', 'pubs.acs.org.sci-hub.io')
		#req.add_header('Referer', 'http://pubs.acs.org.sci-hub.io')
		#req.add_header('GET', link)
		web=ul2.urlopen(link)#(req)
		pdflink=""
		for line in web:
			if "<iframe src" in line and "sci-hub.io" in line and ".pdf" in line:
				pdflink=""
				if ("http" in line):
					i=line.index("http");
					j=line.index(".pdf");
					pdflink = line[i:j+4]
				else:
					i=line.index("sci-hub.io");
					j=line.index(".pdf");
					pdflink = "http://"+line[i:j+4]
				break
		# Another store link..
		if (len(pdflink)<5):
			link="http://pubs.acs.org.sci-hub.io/doi/abs/"+doi
			web=ul2.urlopen(link)
			for line in web:
				if "<iframe src" in line and "sci-hub.io" in line and ".pdf" in line:
					pdflink=""
					if ("http" in line):
						i=line.index("http");
						j=line.index(".pdf");
						pdflink = line[i:j+4]
					else:
						i=line.index("sci-hub.io");
						j=line.index(".pdf");
						pdflink = "http://"+line[i:j+4]
					break

		#pdfreq=ul2.urlopen(link)
		#with open(doiout+".pdf",'w') as fp:
		#	shutil.copyfileobj(pdfreq,fp)
		if (len(pdflink)<5):
			print doi+" can't find!!!!"
		else:
			os.system("wget -t 1 -T 5 "+pdflink+" -O "+doiout+".pdf")
			try:
				if (os.path.exists(doiout+".pdf")):
					fsize=os.path.getsize(doiout+".pdf")
					if (fsize>3000):
						os.renames(doiout+".pdf", "Done/"+doiout+".pdf")
						failcount=0
					elif (fsize<2000):
						os.remove(doiout+".pdf")
						failcount+=1
					if (failcount>=10):
						failcount=0
						time.sleep(1800)
			except:
				pass
			time.sleep(12)
	except : 
		pass
f.close()
