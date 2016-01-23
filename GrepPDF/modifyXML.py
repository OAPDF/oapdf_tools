#! /usr/bin/env python
# -*- coding: utf8 -*-
import os,sys

predoi="10.1021/"

pos1str='<notes><style face="normal" font="default" size="100%">'
pos1len=len(pos1str)
pos2str='Times Cited'
pos2len=len(pos2str)
doistr='<electronic-resource-num><style face="normal" font="default" size="100%">'
doistrlen=len(doistr)

substr=False

def processdoi(stri):
	pos1=stri.find(doistr)
	pos2=stri.find('</style></electronic-resource-num>')
	if (pos1 is -1 or pos2 is -1):
		return stri
	dois=stri[pos1+doistrlen:pos2]
	pos3=dois.find("10.")
	if ( pos3 >=0):
		newdoi=dois[pos3:].lower().strip()
		return stri[:pos1+doistrlen]+newdoi+stri[pos2:]
	else:
		return stri
	

if (__name__ == '__main__'):
	fname=sys.argv[1]
	fnamelist=os.path.splitext(fname)
	fwname=fnamelist[0]+"_new"+fnamelist[1]
	fr=open(fname)
	all=fr.read()
	fr.close()
	fw=open(fwname,'w')
	length=len(all)
	
	prepos1=0; pos1=0;pos2=0
	
	while True:
		prepos1=pos1;
		pos1=all.find(pos1str,pos2)
		writestr=""
		if (pos1 is -1): 
			break
		elif ((pos1-pos2)>50):
			fw.write(processdoi(all[pos2:pos1+pos1len]))
		else:
			fw.write(processdoi(all[prepos1:pos1+pos1len]))
			
		
		try:
			pos2=all.find(pos2str,pos1)
			if (substr):
				#oristr=all[pos1+pos1len:pos2]
				fw.write(substr)
		except:
			pass
		#fw.write(all[pos1+pos1len:pos2])
	#last part
	fw.write(processdoi(all[pos2:]))
	fw.close()