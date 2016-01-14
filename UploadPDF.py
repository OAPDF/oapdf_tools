#! /usr/bin/env python

import os,sys,glob

tmpdir='tmp'
oapdfdir="OAPDF_2"
doilinkdir='doilink'

totalsize=1
while totalsize>0:
	totalsize=0

	ig=glob.iglob(tmpdir+"/10.*.pdf")
	for f in ig:
		#600M FOR submit
		if (totalsize>600000000L):
			os.chdir(oapdfdir)
			print "Now start to submit......"
			os.system('python gendoipage.py')
			os.system('git add -A')
			os.system('git commit -am "update"')
			rs=os.system('git push origin master')
			if (int(rs) != 0):
				rs=os.system('git push origin master')
			if (int(rs) != 0):
				print "Git submit fail!!! Check it!"
				sys.exit(1)
			os.chdir('../'+doilinkdir)
			os.system('git add -A')
			os.system('git commit -am "update"')
			os.system('git push origin gh-pages')
			os.chdir('..')
			print "Successfully submit!"
			break
		try:
			fsize=os.path.getsize(f)
			os.renames(f,oapdfdir+os.sep+os.path.basename(f))
			totalsize+=fsize
		except:
			pass

os.chdir(oapdfdir)
print "Now start to submit......"
os.system('python gendoipage.py')
os.system('git add -A')
os.system('git commit -am "update"')
os.system('git push origin master')
os.chdir('../'+doilinkdir)
os.system('git add -A')
os.system('git commit -am "update"')
os.system('git push origin gh-pages')
os.chdir('..')
print "Successfully submit!"


