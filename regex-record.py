#! /usr/bin/env python
import sys,os,re

fin=open(sys.argv[1])
text=fin.read()
fin.close()

precord=re.compile(r"<record>.*?</record>")
pdoi=re.compile(r"(?<=<electronic-resource-num>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</electronic-resource-num>)")
#pdoi=re.compile(r'(?<=<electronic-resource-num><style face="normal" font="default" size="100%">).*(?=</style></electronic-resource-num>)')
pyear=re.compile(r"(?<=<year>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</year>)")
pvolume=re.compile(r"(?<=<volume>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</volume>)")
pissue=re.compile(r"(?<=<number>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</number>)")
ppages=re.compile(r"(?<=<pages>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</pages>)")
ptitle=re.compile(r"(?<=<title>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</title>)")
pjournal=re.compile(r"(?<=<full-title>)(<style.*?>)(?P<inner>.*?)(</style>)(?=</full-title>)")
ppdflink=re.compile(r"<pdf-urls><url>internal-pdf://(?P<inner>.*?)</url></pdf-urls>")


datapath=re.search(r'(?<=<database)(?:.*?)(?<=path=")(?P<inner>.*?)(?=">)',text).group("inner")
datapath=datapath.replace('\\','\\\\')
datapaths=os.path.splitext(datapath);
pdfdir=datapaths[0]+".Data/PDF/"
startpart=re.search(r"<\?xml.*?<records>",text).group()
endpart="</records></xml>"

for it in precord.finditer(text):
	doi=journal=title=year=volume=issue=pages=""
	record=it.group()
	mdoi=pdoi.search(record)
	if (mdoi):
		doi = mdoi.group("inner")
	mpages=ppages.search(record)
	if (mpages):
		pages = mpages.group("inner")	
	myear = pyear.search(record)
	if (myear):
		year = myear.group("inner")	
	mvolume=pvolume.search(record)
	if (mvolume):
		volume = mvolume.group("inner")	
	missue=pissue.search(record)
	if (missue):
		issue = missue.group("inner")
	mtitle=ptitle.search(record)
	if (mtitle):
		title = mtitle.group("inner")
	mjournal=pjournal.search(record)
	if (mjournal):
		journal = mjournal.group("inner")
	mpdflink=ppdflink.search(record)
	if (mpdflink):
		pdflink = mpdflink.group("inner")

	dois=doi.split('/',1)
	newdoi='@'.join(dois)
	newlink=dois[1]+"/"+newdoi+".pdf"

	print doi, ":", title+" |", journal+" |", year+",", volume+"("+issue+"),", pages,pdfdir+pdflink,newlink