#! /usr/bin/env python
# -*- coding: utf8 -*-
import os,sys

predoi="10.1016/"
pdfdir="Done/"

if (__name__ == '__main__'):
	fname=sys.argv[1]
	fnamelist=os.path.splitext(fname)
	fwname=fnamelist[0]+"_new"+fnamelist[1]
	fr=open(fname)
	all=fr.read()
	fr.close()
	fw=open(fwname,'w')
	length=len(all)
	
	pos1=0;pos2=0
	
	while True:
		pos1=all.find("</urls>",pos2)
		if (pos1 is -1): 
			break
		else:
			fw.write(all[pos2:pos1])
		try:
			pos2=all.find("</style></electronic-resource-num>",pos1)
			if (all.find("pdf-urls>",pos1-100,pos1) is -1):
				pd=all.find(predoi,pos1,pos2)
				doi=all[pd:pos2]
				doii=doi.split('/')
				if (os.path.exists(pdfdir+doii[0]+"_"+doii[1]+".pdf")):
					if (not os.path.exists(pdfdir+doii[1])): os.mkdir(pdfdir+doii[1])
					os.renames(pdfdir+doii[0]+"_"+doii[1]+".pdf",pdfdir+doii[1]+os.sep+doii[0]+"_"+doii[1]+".pdf")
					fw.write("<pdf-urls><url>internal-pdf://"+doii[1]+"/"+doii[0]+"_"+doii[1]+".pdf"+"</url></pdf-urls>")
				# share same pdf
				elif (os.path.exists(pdfdir+doii[1]+"/"+doii[0]+"_"+doii[1]+".pdf")):
					fw.write("<pdf-urls><url>internal-pdf://"+doii[1]+"/"+doii[0]+"_"+doii[1]+".pdf"+"</url></pdf-urls>")
		except:
			pass
		fw.write(all[pos1:pos2])
	#last part
	fw.write(all[pos2:])
	fw.close()
			
		
