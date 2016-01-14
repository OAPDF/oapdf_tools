#! /usr/bin/env python
import sys,os,base64
from optparse import OptionParser
magic="61"
def encodehom(instr):
	s1=base64.encodestring(instr).strip()+"61"
	s2=base64.encodestring(s1).strip()
	s=s2[-3:]+s2[:-3]
	s3="".join(s.split('\n'))
	return s3

def decodehom(instr):
	s1=base64.decodestring(instr[3:]+instr[:3])
	s2=base64.decodestring(s1[:-2])
	return s2

if __name__=="__main__":
	parser = OptionParser()
	parser.add_option("-e", "--encode", action="store", 
					dest="encode", default="",
					help="Encode the string")
	parser.add_option("-d", "--decode", action="store", 
					dest="decode", default="",
					help="Decode the string")
	(options, args) = parser.parse_args()
	if (len(sys.argv)!=3):
		print "Something Wrong!"
		exit(1)
	if (options.encode):
		print encodehom(options.encode)
	elif (options.decode):
		print decodehom(options.decode)
