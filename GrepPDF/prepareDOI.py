#! /usr/bin/env python
# -*- coding: utf8 -*-
import os,sys

predoi="10."

if (__name__ == '__main__'):
	fname=sys.argv[1]
	fnamelist=os.path.splitext(fname)
	fwname=fnamelist[0]+"_new"+fnamelist[1]
	fr=open(fname)
	fw=open(fwname,'w')
	for line in fr:
		fw.write(line[line.find("10."):].lower().strip()+"\n")
	fr.close()
	fw.close()
