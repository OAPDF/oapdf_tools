#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

import os,re
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

try:
	from .doi import DOI
	from .pdfhandler import PDFHandler
	from .basic import normalizeString,strsimilarity,strdiff
	from .crrecord import CRrecord
except (ImportError,ValueError) as e:
	from doi import DOI
	from pdfhandler import PDFHandler
	from basic import normalizeString,strsimilarity,strdiff
	from crrecord import CRrecord

escaper=HTMLParser()

###### PDFdoiCheck class

class PDFdoiCheck(object):
	'''DOI named PDF file processor object'''
	pdoi=re.compile("(?:\:|\\b)(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")
	def __init__(self,fname=""):
		self.handle=PDFHandler()
		self.doi=set()
		self.didpage=set()
		self.normaltxt=[]
		self.reset(fname)
		self.nowdoi=''
		
	@property
	def fname(self):
	    return self._fname
	
	def reset(self,fname):
		'''Reset the saved information and Set the fname 
		!!Important: You should set the fname when you deal with another file!!!'''
		self.handle.reset()
		self.doi.clear()
		self.nowdoi=''
		self.didpage.clear()
		if (isinstance(self.normaltxt,str)):
			del self.normaltxt
			self.normaltxt=[]
		else:
			del self.normaltxt[:]
		self.maxpage=0
		self._fname=""
		if (not fname):
			return
		if (os.path.exists(fname) and os.path.splitext(fname)[1].lower()==".pdf"):
			self._fname=fname
			self.maxpage=self.handle.GetPageNumber(fname)
			self.normaltxt=['' for i in range(self.maxpage)]
		else:
			print "Error file exist or pdf type. Check it"

	def setfile(self,fname):
		self.reset(fname)

	def renamefile(self,newname):
		'''Rename a file'''
		try:
			if not self._fname: 
				print "File Name Not Set!!!"
				return
			if(os.path.exists(newname)):
				"File exists from "+self._fname+" to "+newname
				return 
			os.renames(self._fname,newname)
			self._fname=newname
		except WindowsError:
			os.system("mv '"+self._fname+"' '"+newname+"'")		

	def movetodir(self,newdir):
		'''move to new dir'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return
		fbasic=os.path.split(self._fname)[1]
		try:
			if (newdir[-1] =="/" or newdir[-1] =="\\"):
				if(os.path.exists(newdir+fbasic)):
					"File exists from "+self._fname+" to dir"+newdir
					return 
				os.renames(self._fname, newdir+fbasic)
				self._fname=newdir+fbasic
			else:
				if(os.path.exists(newdir+os.sep+fbasic)):
					"File exists from "+self._fname+" to dir"+newdir
					return 
				os.renames(self._fname,newdir+os.sep+fbasic)
				self._fname=newdir+os.sep+fbasic
		except WindowsError as e:
			os.system("mv '"+self._fname+"' '"+newdir+"'")

	judgedirs={0: 'Done' , 1: 'High', 2: 'Unsure', 3: 'Untitle', 4: 'Fail', 5: 'Page0', 6: 'ErrorDOI',-1:'Unknow'}
	def moveresult(self,judgenum,printstr=None):
		'''move to new dir'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return
		fbasic=os.path.split(self._fname)[1]
		newdir=judgedirs.get(judgenum,'Unknow')
		if (printstr): 
			print printstr
		else:
			print "Try move file",fbasic,'to dir',newdir
		try:
			if(os.path.exists(newdir+os.sep+fbasic)):
				"File exists from "+self._fname+" to dir"+newdir
				return 
			os.renames(self._fname,newdir+os.sep+fbasic)
			self._fname=newdir+os.sep+fbasic
		except WindowsError as e:
			os.system("mv '"+self._fname+"' '"+newdir+"'")

	def doiresultprocess(self,dois):
		'''Very important to deal with found dois....'''
		newdois=[]
		for d in dois:
			if (d.strip()[-1] =='.'):
				newdois.append(d.strip()[:-1].lower())
			else:
				newdois.append(d.strip().lower())
		return newdois	

	def finddoi(self,page=1):
		'''Find doi in given page number
		If page<=0, find all page; >0 single page.
		If page is list, find page in list'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		if (self.maxpage is 0):
			print 'Error max page 0 for '+self._fname
			return ""
		if (isinstance(page,str) or isinstance(page,float) ):
			page=int(page)
		if (isinstance(page,int)):
			if (page <= 0 ):
				outstr=self.handle.GetAllPages(self._fname)
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr.lower().replace("doi:"," "))))
				self.normaltxt=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.update(range(1,self.maxpage+1))
			# Only valid page
			if (page>self.maxpage): 
				page=self.maxpage
			# Only page not process before
			if (page not in self.didpage):
				outstr=self.handle.GetSinglePage(self._fname,page)
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr.lower().replace("doi:"," "))))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.add(page)
		elif ( isinstance(page,list) or isinstance(page,tuple) or isinstance(page,set)):
			for i in page:
				self.finddoi(i)

	def totalpages(self,pages):
		'''To get total page from record pages'''
		ps=pages.split('-')
		if (len(ps) == 2):
			if (ps[0].isdigit() and ps[1].isdigit()):
				return int(ps[1])-int(ps[0])+1
			else:
				pss=[re.sub(r'\D','',p) for p in ps]
				if (pss[0].isdigit() and pss[1].isdigit()):
					return int(pss[1])-int(pss[0])+1
				else:
					# Can't parse
					return 0
		else:
			#Only first page
			return -1

	######### Start to judge ######################
	def hascontent(self,text, similarity=0.95,page=None):
		'''Normalize text and find it in normalized pdf content found before.'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return (False,0.0)

		text=normalizeString(text).lower().strip().replace(' ','')
		if (not text):
			return (False,0.0)
		if (len(text)<3):
			return (False,0.0)
		elif (len(text)==3):
			perfect=text in self.normaltxt[page-1]
			return (perfect,float(perfect)/2)
		try:
			if (not page or (isinstance(page,int) and (page>self.maxpage or page<=0))):
				if (similarity<1.0):
					sim=strsimilarity(''.join(self.normaltxt),text)
					return (sim >= similarity,sim)
				else:
					perfect=text in ''.join(self.normaltxt)
					return (perfect,float(perfect))
			elif (isinstance(page,int)):
				if (similarity<1.0):
					sim=strsimilarity(self.normaltxt[page-1],text)
					return (sim >= similarity,sim)
				else:
					perfect=text in self.normaltxt[page-1]
					return (perfect,float(perfect))
		except:
			print "Something error for hascontent function: "+text
			return (False,0.0)	

	def hasoneofcontent(self,ltext,similarity=0.95,page=None):
		'''Normalize text in a list and find it in normalized pdf content found before.
		One in list right result is right'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return (False,0.0)
		result=(False,0.0)
		maxnow=0.0
		if (isinstance(ltext,list)):
			for text in ltext:
				result=self.hascontent(text,similarity=similarity,page=page)
				if (result[0]):
					return result
				elif(result[1]>maxnow):
					maxnow=result[1]
			result=(False,maxnow)
		elif (isinstance(ltext,str)):
			result=self.hascontent(ltext, similarity=similarity,page=page)
			return result
		return result	

	def checktitle(self,title,similarity=0.95,page=None):
		'''For check title. Some special case in title...'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		title=escaper.unescape(title)
		title=re.sub(r"(?:<.?sup>|<.?i>|\$\$.*?{.*?}.*?\$\$)","",title)
		return self.hascontent(title, similarity=similarity,page=page)

	def checkcrossref(self,cr):
		'''Check other info in crossref record...For some paper don't have doi.
		Should fully parse crossref!
		Only first page!'''
		if (isinstance(cr,CRrecord)):
			try:
				if (not self.hascontent(cr.pages.split("-")[0],1.0,page=1)): return False
				if (not self.hascontent(cr.volume,1.0,page=1)): return False
				if (not self.hasoneofcontent([cr.year,str(int(cr.year)+1),str(int(cr.year)-1)],1.0,page=1)): return False
				if (not self.hasoneofcontent(cr.journals,1.0,page=1)): return False
				#if (not self.hasoneofcontent(cr.issns,1.0,page=1)): return False
				return True
			except ValueError as e:
				print e
				return False
		return False

	def checkdoi(self,doi,page=1,iterfind=True):
		'''Check whether doi in given page'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return False
		self.finddoi(page)
		if (doi in self.doi):
			return True
		elif (iterfind and page is 1 and self.maxpage is not 1 and self.checkdoi(doi,2)):
			return True
		elif (iterfind and page is 2 and self.maxpage is not 2 and self.checkdoi(doi,self.maxpage)):
			return True
		return False

	def checkdoinormaltxt(self,doi):
		'''Check nospace normalstring doi whether in nospace normalstring context'''
		ndoi=normalizeString(doi).lower().replace(" ",'')
		return (ndoi in ''.join(self.normaltxt))

	def checkdoifurther(self,doi):
		'''Special cases..It will re-read pdf and do more process. 
		So it need to run checkdoinormaltxt first to make sure doi in context'''
		outstr=self.handle.GetPages(self._fname,self.didpage).lower()
		outstr=outstr.replace("\xe2\x80\x93",'-').replace("\xe5\x85\xbe","/")
		#dois=set(self.doiresultprocess(self.pdoi.findall(re.sub(r"\n(?=[^\n])",'',re.sub(r'doi.(?=10.)',' ',outstr)))))
		out2=re.sub(r"\n(?=[^\n])",'',outstr)
		return (doi in out2)

	def checkdoititle(self,doi,title,page=1):
		'''Check whether doi and title in given page'''
		return self.checkdoi(doi,page) and self.hascontent(title)

	def checkdoifname(self,page=[1,2]):
		'''Check whether fname's doi same to doi in file
		Default check two pages'''
		bname=os.path.splitext(os.path.basename(self._fname))[0].strip().lower()
		fdoi=requests.utils.unquote(bname.replace('@','/'))
		return self.checkdoi(fdoi,page)

	def scorefitting(self,cr):
		'''Score the PDF with the giving crossref record'''
		try:
			spages=self.hascontent(cr.pages,1.0,page=1)[1]
			if (spages<0.1):
				spages2=self.hascontent(cr.pages.split('-')[0],1.0,page=1)[1]
				if (spages2>spages):
					spages=spages2
			sjournal=self.hasoneofcontent(cr.journals,1.0,page=1)[1]
			syear=self.hasoneofcontent([cr.year,str(int(cr.year)+1),str(int(cr.year)-1)],1.0,page=1)[1]
			sauthors=0.0
			if (cr.authors):
				slauthors=[self.hasoneofcontent(a.split(','),1.0,page=1)[1] for a in cr.authors]
				sauthors=sum(slauthors)/float(len(slauthors))
			sissn=self.hasoneofcontent(cr.issns,1.0,page=1)[1]
			page1s=(spages,sjournal,syear,sauthors,sissn)

			spages=self.hascontent(cr.pages,1.0,page=2)[1]
			if (spages<0.1):
				spages2=self.hascontent(cr.pages.split('-')[0],1.0,page=2)[1]
				if (spages2>spages):
					spages=spages2
			sjournal=self.hasoneofcontent(cr.journals,1.0,page=2)[1]
			syear=self.hasoneofcontent([cr.year,str(int(cr.year)+1),str(int(cr.year)-1)],1.0,page=2)[1]
			sauthors=0.0
			if (cr.authors):
				slauthors=[self.hasoneofcontent(a.split(','),1.0,page=2)[1] for a in cr.authors]
				sauthors=sum(slauthors)/float(len(slauthors))
			sissn=self.hasoneofcontent(cr.issns,1.0,page=2)[1]
			page2s=(spages,sjournal,syear,sauthors,sissn)

			pagefinal=[ max(page1s[i],page2s[i]) for i in range(5)] 
			finalscore=pagefinal[0]*0.1+pagefinal[1]*0.1+pagefinal[2]*0.05+pagefinal[3]*0.15+pagefinal[4]*0.1
			return {'total':finalscore,'pages':pagefinal[0],'journal':pagefinal[1],'year':pagefinal[2],'authors':pagefinal[3],'issn':pagefinal[4]}
		except Exception as e:
			print e
			return {'total':0,'pages':0,'journal':0,'year':0,'authors':0,'issn':0}

	def renamecheck(self,fname,wtitle=0.65,cutoff=0.85,justcheck=False,resetfile=True,fdoi=None):
		'''A complex function to get doi from file name, 
		check in crossref, check in pdf file, rename it!
		just check can cancel move file'''
		### Result back:
		# 0: Done 
		# 1: High
		# 2: Unsure
		# 3: Untitle
		# 4: Fail
		# 5: Page0
		# 6: ErrorDOI
		if (resetfile): self.reset(fname)
		if (self.maxpage == 0):
			if not justcheck: self.movetodir("Page0")
			print "Error Page 0(Fail): "+self._fname
			return 5
		if (not fdoi):
			fdoi=DOI(os.path.splitext(os.path.basename(self._fname))[0])
		else:
			fdoi=DOI(fdoi)
		self.finddoi(1)
		if (not fdoi):
			if (len(self.doi) is 1):
				print "Origin no fdoi but has one doi in file:",self._fname,
				judgenum = self.renamecheck(self._fname,wtitle=wtitle,cutoff=cutoff,\
					justcheck=True,resetfile=False,fdoi=list(self.doi)[0])
				if not justcheck:
					moveresult(judgenum,printstr=None)
				#nodoi=DOI( list(self.doi)[0] )
				#crno=CRrecord()
				#crno=crno.valid_doi(nodoi,fullparse=True)
				#if (crno):
				#	if (self.checktitle(crno.title)[0]):
				#	# Valid doi and title, rename file
				#		if not justcheck: self.renamefile("Done/"+nodoi.quote()+".pdf")
				#		return True
				#	else:
				#		print "OK doi in file but not title(Unsure): "+self._fname+" to: "+nodoi.quote()+".pdf"
				#		if not justcheck: self.renamefile("Unsure/"+nodoi.quote()+".pdf")
				#		return False
				## Error doi
				#else:
				#	print "Error doi and title(Fail): "+self._fname
				#	if not justcheck: self.movetodir("Fail")
				#	return False
			else:
				print "0/too much doi. Can't sure(Fail): "+self._fname
				if not justcheck: self.movetodir("Fail")
				return False
		# fdoi is ok
		cr=CRrecord()
		cr=cr.valid_doi(fdoi,fullparse=True)

		#crossref is ok
		if (fdoi and cr):
			self.nowdoi=fdoi
			totalpagenumber=1
			try:
				totalpagenumber=self.totalpages(cr.pages)
			except ValueError as e:
				print e, cr.pages

			totalpagewrong=False
			if totalpagenumber>0 and not (self.maxpage >= totalpagenumber and self.maxpage <= totalpagenumber+2):
				totalpagewrong=True

			# Just check first page, faster.
			doivalid=self.checkdoi(fdoi,page=1,iterfind=False)
			titleeval=self.checktitle(cr.title)
			if (totalpagenumber > 0 and not totalpagewrong):
				if (doivalid and titleeval[0] and len(self.doi) is 1):
					# Yes! Very Good PDF!
					if not justcheck: self.movetodir("Done")
					return True

			# Further check doi in page2/last, Finally, will check 1,2 and last pages.
			doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True) or doivalid )

			# Page wrong and doi can't make sure
			if (len(self.doi)!=1 and totalpagewrong):
				print "PDF Page",self.maxpage,"!=",totalpagenumber,"(Fail): "+self._fname
				if not justcheck: self.movetodir("Fail")
				return False

			if (not totalpagewrong):
				crscore=self.scorefitting(cr)
				titlevalid=False
				try:
					if (int(cr.year)>1990):
						titlevalid=titleeval[0] or (titleeval[1]*wtitle+crscore['total'])>=cutoff
					else:
						titlevalid=titleeval[0] or (titleeval[1]*wtitle+crscore['total'])>=cutoff-0.1
				#(self.checktitle(cr.title,similarity=0.85) and self.checkcrossref(cr))
				except Exception as e:
					print e

				if (doivalid):
					if (titlevalid):					
						# Yes! Good PDF!
						if not justcheck: self.movetodir("Done")
						return True
					else:
						# DOI ok but not title
						print "OK fdoi but not title(Untitle): "+self._fname
						print "Title/Paper score:",titleeval[1],crscore,self._fname
						if not justcheck: self.movetodir("Untitle")
						return False
				
				# Indeed, doi maybe in pdf, but strange format..
				if (self.checkdoinormaltxt(fdoi)):
					if (titlevalid):
						# Further check only when title OK
						if (self.checkdoifurther(fdoi)):
							# Fine! move to Done dir
							if not justcheck: self.movetodir("Done")
							return True
						else:
							# Can't find, but high similar! move to High dir
							print "OK title and nospacebreak doi,but not pass(High): "+self._fname
							if not justcheck: self.movetodir("High")
							return False
					else:
						# DOI ok but not title
						print "Maybe OK fdoi but not title(Untitle): "+self._fname
						print "Title/Paper score:",titleeval[1],crscore,self._fname
						if not justcheck: self.movetodir("Untitle")
						return False						

				# DOI maybe not exist ....
				if (titlevalid):	
					# Old paper don't have doi...
					if (self.checkcrossref(cr)):
						if (len(self.doi) is 0 and crscore['total'] >= 0.4):
							if not justcheck: self.movetodir("Done")
							return True
						elif (len(self.doi) is 0 and titleeval[1]>=0.85 and crscore['total'] >= 0.35):
							if not justcheck: self.movetodir("Done")
							return True
						elif (len(self.doi) is 0 and titleeval[1]>=0.95 and crscore['total'] >=0.3):
							if not justcheck: self.movetodir("Done")
							return True
						elif (len(self.doi) is 0 and titleeval[1]>=0.90 and crscore['pages']>=0.9 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9)):
							if not justcheck: self.movetodir("Done")
							return True
						elif (len(self.doi) is 0 and titleeval[1]>=0.90 and crscore['pages']>=0.5 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9) and crscore['authors']>=0.8):
							if not justcheck: self.movetodir("Done")
							return True						
						#elif (int(cr.year)<=1999 and len(self.doi) is 0):
						#	# Highly possible right
						#	if not justcheck: self.movetodir("High")
						#	return True
						#  Bentham, often blank doi
						#elif (fdoi[:8] == '10.2174/' and len(self.doi) is 0):
						#	if not justcheck: self.movetodir("Done")
						#	return True
						elif (len(self.doi) is 0):
							print "Title/Paper score:",titleeval[1],crscore,self._fname
							print "OK title and high info fit. But no doi(Highly): "+self._fname
							if not justcheck: self.movetodir("High")
							return True							
						else:
							print "OK title and high info fit. But doi exist not fit(Unsure): "+self._fname
							if not justcheck: self.movetodir("Unsure")
							return False								
					elif(len(self.doi) is 0):
						# Maybe wrong file no doi
						print "Not found doi in file but ok title (Unsure): "+self._fname
						if not justcheck: self.movetodir("Unsure")
						return False

			#fdoi,title wrong, no doi in file
			if (len(self.doi) is 0):
				print "Both fdoi and title wrong, no doi in file(Fail): "+self._fname
				if not justcheck: self.movetodir("Fail")
				return False

			# Indeed, file has only one doi, not the same to fname
			if (len(self.doi) is 1):
				newdoi=DOI( list(self.doi)[0] )
				newcr=CRrecord()
				newcr=newcr.valid_doi(newdoi,fullparse=True)
				if (newcr):
					crpages=newcr.pages.split('-')
					totalpagenumber=1
					if (len(crpages) ==2 ):
						try:
							totalpagenumber=self.totalpages(newcr.pages)
						except ValueError as e:
							print e, crpages
					if (self.checktitle(newcr.title) and self.maxpage >= totalpagenumber and self.maxpage <= totalpagenumber+2):
					# Valid doi and title, rename file, then recheck it
						print "OK: Rename file from "+self._fname+" to "+newdoi.quote()+".pdf"
						if not justcheck: self.renamefile("Done"+os.sep+newdoi.quote()+".pdf")
						return True
					else:
						print "One in-file doi but not title(Unsure): "+self._fname
						if not justcheck: self.movetodir("Unsure")
						return False
				# Error doi
				else:
					print "Error doi and title(Fail): "+self._fname
					if not justcheck: self.movetodir("Fail")
					return False
			elif(len(self.doi) > 1):
				print "fdoi/title fail. Too much infile doi(Unsure): "+self._fname
				if not justcheck: self.movetodir("Unsure")
				return False
			else:
				print "What?????What?????(Fail):"+self._fname
				if not justcheck: self.movetodir("Fail")
				return False
		elif not cr:
			print "Error DOI fname(Fail):"+self._fname
			if not justcheck: self.movetodir("ErrorDOI")
			return False