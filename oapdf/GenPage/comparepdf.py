#! /usr/bin/env python

import os,sys,glob

def similarsize(s1,s2):
	i1=int(s1)
	i2=int(s2)
	if (i1 == i2):
		return 0
	if (min(i1,i2)<300000 and abs(i1-i2)<=3000):
		return 1
	elif (abs(i1-i2)<=300000):
		return 1
	else:
		return -1

if (not os.path.exists('Done')):
	os.makedirs('Done')

for fg in glob.iglob('10.*.pdf'):
	fpath=fg.strip().split('@',1)
	fsize=os.path.getsize(fg)
	fname=fpath[0]+os.sep+fg
	printout=""
	if (not os.path.exists(fname)):
		os.renames(fg,'Done'+os.sep+fg)
	else:
		f=open(fname)
		for line in f:
			s=similarsize(fsize,line.strip())
			if ( s is 0):
				os.remove(fg)
				printout=""
				break
			elif ( s is 1 and int(fsize)<int(line.strip())):
				os.remove(fg)
				printout=""
				break				
			else:
				printout=fg+" now size: "+str(fsize)+"; in lib: "+line.strip()
		if (printout): print printout
		f.close()


