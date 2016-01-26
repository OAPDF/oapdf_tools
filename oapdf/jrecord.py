#! /usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

######################## Part3: Journal Record #############################
############### General Journal Record class ###############################

class Jrecord(object):
	'''Basic journal record information'''
	def __init__(self):
		self.journal=""
		self.title=""
		self.authors=[]
		self.year=""
		self.volume=""
		self.issue=""
		self.pages=""
		self.doi=""
		self.issn=""
		self.publisher=""
		self.urls=[]
		self.pdf=""
		self.abstract=""
		self.note=""

	def __getattr__(self, name):
		"""Locate the function with the dotted attribute."""
		def traverse(parent, child):
			if instance(parent, str):
				parent = getattr(self, parent)
				return getattr(parent, child)
		return reduce(traverse, name.split('.'))

	def __getitem__(self,name):
		'''Aact as dict'''
		return getattr(self,name)

	def reset(self):
		self.journal=""
		self.title=""
		del self.authors[:]
		self.year=""
		self.volume=""
		self.issue=""
		self.pages=""
		self.doi=""
		self.issn=""
		self.publisher=""
		del self.urls[:]
		self.pdf=""
		self.abstract=""
		self.note=""		
		
	def __repr__(self):
		return (self.doi+": "+self.title+" | "+self.journal+" | "+self.year+"; "+self.volume+"("+self.issue+")"+", "+self.pages).encode('utf-8')

	def __str__(self):
		return self.__repr__()

	def writexml(self):
		pass

	def writeenw(self):
		pass

	def writebib(self):
		pass

	def writeris(self):
		pass

	def parseNoteFirst(self,text=None,infile=None):
		'''Parse NoteFirst record (xml format), return self'''
		if isinstance(text,basestring):
			pass
		elif isinstance(infile,basestring):
			f=open(infile);
			text=f.read()
			f.close()
		elif isinstance(infile,file):
			text=infile.read()
		else: #Do nothing
			return None		
		soup=BeautifulSoup(text,"html.parser")
		self.title=soup.primarytitle.text
		doi=soup.doi.text
		self.doi=doi[doi.find("10."):]
		self.journal=soup.media.info.text
		self.year=soup.year.text
		self.volume=soup.volume.text
		self.issue=soup.issue.text
		self.pages=soup.pagescope.text
		authors=soup.findChildren('fullname')
		self.authors=[ author.info.text for author in authors]
		#self.issn=""
		return self

	def parseenw(self,text=None,infile=None):
		'''Parse the endnote enw file, return self'''
		lines=None
		# Use basestring for both str and unicode!
		if isinstance(text,basestring):
			lines=text.splitlines()
		elif isinstance(text,list):
			lines=text
		elif isinstance(infile,basestring):
			lines=open(infile);
		elif isinstance(infile,file):
			lines=infile
		else: #Do nothing
			return None
		for line in lines:
			if (len(line)>1):
				item=line[1]
				if item=="T":
					self.title=line[3:].strip()
				elif item=="D":
					self.year=line[3:].strip()
				elif item=="P":
					self.pages=line[3:].strip()
				elif item=="J":
					self.journal=line[3:].strip()
				elif item=="V":
					self.volume=line[3:].strip()
				elif item=="N":
					self.issue=line[3:].strip()
				elif item=="A":
					self.authors.append(line[3:].strip())
		if isinstance(infile,basestring):
			lines.close()
		return self