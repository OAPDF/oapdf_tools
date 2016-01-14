#! /usr/bin/env python
# A script help to set the pdf-urls
# Need XML input.

import sys,os,re

fin=open(sys.argv[1])
text=fin.read()
fin.close()

fins=os.path.splitext(sys.argv[1])
fw=open(fins[0]+"_new"+fins[1],'w')

precord=re.compile(r"<record>.*?</record>")
pdoi=re.compile(r"(?<=<electronic-resource-num>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</electronic-resource-num>)")
ppdflink=re.compile(r"(?<=<pdf-urls><url>internal-pdf://)(?P<inner>.*?)(?=</url></pdf-urls>)")
datapath=re.search(r'(?<=<database)(?:.*?)(?<=path=")(?P<inner>.*?)(?=">)',text).group("inner")

startpart=re.search(r"<\?xml.*?<records>",text).group()
endpart="</records></xml>"
fw.write(startpart)

datapath=datapath.replace('\\','\\\\')
datapaths=os.path.splitext(datapath);
pdfdir=datapaths[0]+".Data/PDF/"

for it in precord.finditer(text):
	doi=pdflink=""
	record=it.group()

	mdoi=pdoi.search(record)
	if (mdoi):
		doi = mdoi.group("inner")
	mpdflink=ppdflink.search(record)
	if (mpdflink):
		pdflink = mpdflink.group("inner")

	dois=doi.split('/',1)
	newdoi='@'.join(dois)
	newlink=newdoi+".pdf"

	#### If you have pdf files in PDF/..../ subdirectory, move it!
	#if (os.path.exists(pdfdir+pdflink)): 
	#	if (pdflink != newlink and not os.path.exists(pdfdir+newlink)):
	#		os.renames(pdfdir+pdflink,pdfdir+newlink)
	#elif (os.path.exists(pdfdir+newlink)):
	#	pass
	#else:
	#	print "Can't find file: "+pdfdir+pdflink
	fw.write(ppdflink.sub(newlink,record))

fw.write(endpart)
fw.close()