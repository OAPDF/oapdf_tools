#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys,requests
from oapdf import DOI

f=open(sys.argv[1])

for line in f:
	doi=DOI(line.strip())
	if (not doi):
		continue
	if (doi.is_oapdf()):
		continue
	pmc=doi.pmcid
	if (pmc):
		url="http://europepmc.org/articles/"+pmc+"?pdf=render"
		r=requests.get(url)
		if (r.status_code == 200):
			fname=doi.quote()+".pdf"
			fw=open(fname,'wb')
			fw.write(r.content)
			fw.close()
		else:
			print "Error on DOI",doi,"with PMCID:",pmc
	else:
		print "DOI",doi,"doesn't have PMCID:",pmc