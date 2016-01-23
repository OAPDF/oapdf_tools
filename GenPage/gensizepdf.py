#! /usr/bin/env python

import os,sys,glob,json

# Rewrite it, Default False
_force=True
# Suitable for add the new pdf information to it
# Default True
_add=False

# make sure only one mode
if _add:
	_force=False

for jf in sys.argv[1:]:
	f=open(jf)
	j=json.loads(f.read())
	f.close()
	for pdf,fs in j['items'].items():
		fpath=pdf.strip().split('@',1)
		fname=pdf
		if ('10.' in fpath[0]):
			if (not os.path.exists(fpath[0])): 
				os.makedirs(fpath[0])
			fname=fpath[0]+os.sep+pdf
			if (not _force and not _add and os.path.exists(fname)): 
				continue
		if (_add):
			fw=open(fname,'a')
		else:
			fw=open(fname,'w')
		fw.write(str(fs)+'\n')
		fw.close()
