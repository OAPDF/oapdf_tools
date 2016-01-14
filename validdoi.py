#! /usr/bin/env python

import sys,os,requests,re

p=re.compile(r"<title>.*?</title>")
pl=re.compile(r'(?<=<a href=")http.*?(?=">)')

fin=open(sys.argv[1])

for line in fin:
	link="http://dx.doi.org/"+line.strip()
	r=requests.get(link,allow_redirects=False)
	title=p.search(r.text).group().lower()
	#if ("dx.doi.org" in r.url):
	#	print line
	if ("redirect" in title):
		print line.strip(), pl.search(r.text).group()
	else:
		print line.strip(), "Error Link!"
fin.close()