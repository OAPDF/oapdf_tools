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
	from .basic import normalizeString,strsimilarity,strdiff,removeunicode
	from .crrecord import CRrecord
except (ImportError,ValueError) as e:
	from doi import DOI
	from pdfhandler import PDFHandler
	from basic import normalizeString,strsimilarity,strdiff,removeunicode
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
		self.withSI=False
		
	@property
	def fname(self):
	    return self._fname
	
	def reset(self,fname):
		'''Reset the saved information and Set the fname 
		!!Important: You should set the fname when you deal with another file!!!'''
		self.handle.reset()
		self.doi.clear()
		self.didpage.clear()
		if (isinstance(self.normaltxt,str)):
			del self.normaltxt
			self.normaltxt=[]
		else:
			del self.normaltxt[:]
		self.maxpage=0
		self._fname=""
		self.withSI=False
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

	judgedirs={0: 'Done' , 1: 'High', 2: 'Unsure', 3: 'Untitle', 4: 'Fail', 5: 'Page0', 6: 'ErrorDOI',10:'Unknow'}
	def moveresult(self, judgenum, printstr=None,newfname=''):
		'''move to new dir and even new file name'''
		fname=self._fname
		if (newfname):
			fname=newfname
		if not self._fname: 
			print "File Name Not Set!!!"
			return
		fbasic=os.path.split(fname)[1]
		newdir=self.judgedirs.get(judgenum,'Unknow')

		if (printstr): 
			print printstr
		elif(judgenum != 0):
			print "Try move file",self._fname,'to dir',newdir
			if (newfname):
				print "(Rename) to",fbasic
		elif (newfname):
			print "(Rename) file",self._fname,'to',newdir+os.sep+newfname

		try:
			if(os.path.exists(newdir+os.sep+fbasic)):
				"File exists from "+self._fname+" to dir"+newdir
				return 
			os.renames(self._fname,newdir+os.sep+fbasic)
			self._fname=newdir+os.sep+fbasic
		except WindowsError as e:
			print e
			#os.system("mv '"+self._fname+"' '"+newdir+os.sep+fbasic+"'")

	def doiresultprocess(self,dois):
		'''Very important to deal with found dois....'''
		newdois=[]
		for d in dois:
			if (d.strip()[-1] =='.'):
				newdois.append(d.strip()[:-1].lower())
			else:
				newdois.append(d.strip().lower())
		return newdois	

	def pdfcontextpreprocess(self,text):
		return removeunicode(text.lower().replace('doi:',' ').replace("\xe2\x80\x93",'-').replace("\xe5\x85\xbe","/"))

	def findtext(self,text,page=1):
		'''Just Find text in Page, Don't search doi and save it'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		if (self.maxpage is 0):
			print 'Error max page 0 for '+self._fname
			return ""
		if (isinstance(page,str) or isinstance(page,float) ):
			page=int(page)
		normaltxt=""
		if (isinstance(page,int)):
			if (page<=0):
				page=1
			# Only valid page
			if (page>self.maxpage): 
				page=self.maxpage
			# Only page not process before
			if (not self.normaltxt[page-1] ):
				outstr=self.pdfcontextpreprocess(self.handle.GetSinglePage(self._fname,page))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
			return self.hascontent(text,page=page)[0]
		elif ( isinstance(page,list) or isinstance(page,tuple) or isinstance(page,set)):
			outyn=False
			for i in page:
				outyn= self.findtext(text,i)
				if (outyn):
					break
			return outyn

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
				outstr=self.pdfcontextpreprocess(self.handle.GetAllPages(self._fname))
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr)))
				self.normaltxt=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.update(range(1,self.maxpage+1))
			# Only valid page
			if (page>self.maxpage): 
				page=self.maxpage
			# Only page not process before
			if (page not in self.didpage):
				outstr=self.pdfcontextpreprocess(self.handle.GetSinglePage(self._fname,page))
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr)))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.add(page)
		elif ( isinstance(page,list) or isinstance(page,tuple) or isinstance(page,set)):
			for i in page:
				self.finddoi(i)

	def totalpages(self,pages):
		'''To get total page from record pages'''
		if (not pages or not pages.strip()):
			return 1

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

		try:
			if (not page or (isinstance(page,int) and (page>self.maxpage or page<=0))):
				if (len(text)==3):
					perfect=text in ''.join(self.normaltxt)
					return (perfect,float(perfect)/2)
				if (similarity<1.0):
					sim=strsimilarity(''.join(self.normaltxt),text)
					return (sim >= similarity,sim)
				else:
					perfect=text in ''.join(self.normaltxt)
					return (perfect,float(perfect))
			elif (isinstance(page,int)):
				if (len(text)==3):
					perfect=text in self.normaltxt[page-1]
					return (perfect,float(perfect)/2)
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

	def checkdoi(self,doi,page=1,iterfind=True,justcheck=False):
		'''Check whether doi in given page'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return False
		# Find or just check in self.doi
		if (not justcheck): self.finddoi(page)

		if (doi in self.doi):
			return True
		elif (justcheck):
			return False
		# When not justcheck and iterfind 2 and last page
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

	#def checkdoititle(self,doi,title,page=1):
	#	'''Check whether doi and title in given page'''
	#	return self.checkdoi(doi,page) and self.hascontent(title)

	#def checkdoifname(self,page=[1,2]):
	#	'''Check whether fname's doi same to doi in file
	#	Default check two pages'''
	#	bname=os.path.splitext(os.path.basename(self._fname))[0].strip().lower()
	#	fdoi=requests.utils.unquote(bname.replace('@','/'))
	#	return self.checkdoi(fdoi,page)

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

	def recursivedoicheck(self,excludedoi,olddoi,wtitle=0.65,cutoff=0.85,justcheck=False):
		tryjudge=4
		trydoi=""
		rightdoi=[]
		excludedoi.add(olddoi)
		for doi in self.doi-excludedoi:
			print "Recursive check doi..",self._fname,doi,
			judgenum = self.renamecheck(self._fname,wtitle=wtitle,cutoff=cutoff,\
			justcheck=True,resetfile=False,excludedoi=excludedoi,fdoi=doi)
			excludedoi.add(doi)
			if (judgenum is 0):
				rightdoi.append(doi)
				tryjudge=0
			elif (judgenum<tryjudge):
				trydoi=doi
				tryjudge=judgenum
			# else, retain 4 and blank doi
		if (len(rightdoi) is 1):
			doi=DOI(rightdoi[0])
			if not justcheck:
				self.moveresult(0,printstr=None,newfname=doi.quote()+".pdf")
			return 0
		elif (len(rightdoi) >= 2 ):
			if not justcheck:
				self.moveresult(3,printstr="Many DOIs are OK, can't distinguish...(Unsure)")
			return 3 # Unsure
		else:
			print "Doesn't have reliable doi", self._fname
			if not justcheck:
				self.moveresult(tryjudge,printstr=None)
			return tryjudge

	def renamecheck(self,fname,wtitle=0.65,cutoff=0.85,justcheck=False,resetfile=True,fdoi=None,excludedoi=None):
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
		# 10: Unknow

		# len(self.doi) is 1 and len(self.doi - excludedoi) is 1 : 
		# :: First Run and perform check
		# len(self.doi) is 1 or len(self.doi - excludedoi) is 1 :
		if (not fname and not fdoi):
			print "No given file name or doi! (Return 6)"
			return 6

		if (fname and not fdoi and excludedoi):
			print "What do you want?! No excludedoi set by user! (Return 9)"
			return 9

		if (resetfile): 
			self.reset(fname)

		if (self.maxpage == 0):
			if not justcheck: 
				self.moveresult(5, printstr="Error Page 0 (Page0, R5): "+self._fname)
			return 5

		if (not excludedoi):
			excludedoi=set()

		if (not fdoi):
			fdoi=DOI(os.path.splitext(os.path.basename(self._fname))[0])
		else:
			fdoi=DOI(fdoi)

		recursive= (len(excludedoi) > 0)
		# If in recursive, don't move file!
		if recursive: justcheck=True

		# Only find DOI in first time!
		if (not recursive and fdoi): 
			self.finddoi(1)
		elif (not recursive and not fdoi):
			self.finddoi(set([1,2,self.maxpage]))

		# file doi is shit..Recursively use doi in file or fail
		if (not fdoi and not recursive):
			if (len(self.doi) is 1 or len(self.doi) is 2):
				print "Origin fdoi wrong but has 1/2 doi in file:",self._fname,
				return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=wtitle,justcheck=justcheck)
			# No doi or >2 dois in file
			else:
				if not justcheck: 
					self.moveresult(4,printstr="Error fdoi and 0/too much doi. (Fail): "+self._fname)
				return 4
		elif (not fdoi and recursive):
			print "doi (in recursion) may wrong with error doi. Should never happen.."
			return 4 # Fail

		# fdoi is ok
		cr=CRrecord()
		try:
			cr=cr.valid_doi(fdoi,fullparse=True)
		except requests.exceptions.RequestException as e:
			print e
			cr=None
		except Exception as e:
			print e
			cr=None		

		# Error when year=None, improve in crrecord.
		#if (cr and not cr.year):
		#	cr.year='8888'	

		#crossref is ok
		if (fdoi and cr):
			totalpagenumber=1
			try:
				totalpagenumber=self.totalpages(cr.pages)
			except ValueError as e:
				# should never happen now
				print e, cr.pages

			totalpagewrong=False
			if totalpagenumber>0 and not (self.maxpage >= totalpagenumber and self.maxpage <= totalpagenumber+2):
				totalpagewrong=True
				# When paper with supporting information
				if (self.maxpage > totalpagenumber+2):
					if (self.withSI or self.findtext('Supporting Information', page=[totalpagenumber+1,totalpagenumber+2])):
						if not recursive : self.finddoi(totalpagenumber);
						totalpagewrong=False

			# Recursive but total page wrong. Fast end recursivedoicheck
			if (totalpagewrong and recursive):	
				return 4

			# Just check first page, not find(find before..), faster:
			doivalid=self.checkdoi(fdoi,page=1,iterfind=False,justcheck=True)
			titleeval=self.checktitle(cr.title)
			if (totalpagenumber > 0 and not totalpagewrong):
				if (doivalid and titleeval[0] and len(self.doi) is 1):
					# Yes! Very Good PDF!
					if not justcheck: self.moveresult(0)
					return 0

			# Further check doi in page2/last, Finally, will check 1,2 and last pages.
			if (recursive):
				doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True,justcheck=True) or doivalid )
			else:
				doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True) or doivalid )

			# Page wrong and try recursive use doi
			if (totalpagewrong):
				if (len(self.doi) is 1 or len(self.doi) is 2):
					doi=DOI(list(self.doi)[0])
					# DOI in file is same so error. Don't need recursive
					if (len(self.doi) is 1 and doi == fdoi):
						if not justcheck: 
							self.moveresult(4,printstr="PDF Page "+str(self.maxpage)+"!="+str(totalpagenumber)+"(Fail): "+self._fname)
						return 4

					print 'Wrong total page with dois in file,',self._fname,fdoi,',try recursive'
					return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=wtitle,justcheck=justcheck)
				else:
					if not justcheck: 
						self.moveresult(4,printstr="PDF Page "+str(self.maxpage)+"!="+str(totalpagenumber)+"(Fail): "+self._fname)
					return 4

			if (not totalpagewrong):
				crscore=self.scorefitting(cr)
				titlevalid=False
				try:
					# Too old maybe lost information
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
						if not justcheck: self.moveresult(0)
						return 0

					print "Title/Paper score:",titleeval[1],crscore,self._fname
					if (len(self.doi - set([fdoi])) == 1 and not recursive):
						
						# Try one more
						newresult = self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=wtitle,justcheck=True)
						if (newresult is 0):
							newdoi=DOI(list(self.doi - set([fdoi]))[0])
							print 
							if not justcheck: self.moveresult(0, 
								printstr="(Rename)fdoi ok, but not title. In file doi "+newdoi+" is better for "+self._fname,
								newfname=newdoi.quote()+".pdf")
							return 0

					# Else DOI ok but not title
					if not justcheck: 
						self.moveresult(3,printstr="OK fdoi but not title(Untitle): "+self._fname)
					return 3
				
				# Indeed, doi maybe in pdf, but strange format..
				if (self.checkdoinormaltxt(fdoi)):
					if (titlevalid):
						# Further check only when title OK
						if (self.checkdoifurther(fdoi)):
							# Fine! move to Done dir
							if not justcheck: self.moveresult(0)
							return 0
						else:
							# Can't find, but high similar! move to High dir
							if not justcheck: 
								self.moveresult(1,printstr="OK title and nospacebreak doi,but not pass(High): "+self._fname)
							return 1
					else:
						# DOI ok but not title
						print "Title/Paper score:",titleeval[1],crscore,self._fname
						if not justcheck: 
							self.moveresult(3,printstr="Maybe OK fdoi but not title(Untitle): "+self._fname)
						return 3						

				# DOI maybe not exist ....
				if (titlevalid):
					# Old paper don't have doi...
					if len(self.doi) is 0:
						if (crscore['total'] >= 0.4):
							if not justcheck: self.moveresult(0)
							return 0
						elif (titleeval[1]>=0.85 and crscore['total'] >= 0.35):
							if not justcheck: self.moveresult(0)
							return 0
						elif (titleeval[1]>=0.95 and crscore['total'] >=0.3):
							if not justcheck: self.moveresult(0)
							return 0
						elif (titleeval[1]>=0.90 and crscore['pages']>=0.9 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9)):
							if not justcheck: self.moveresult(0)
							return 0
						elif (titleeval[1]>=0.90 and crscore['pages']>=0.5 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9) and crscore['authors']>=0.8):
							if not justcheck: self.moveresult(0)
							return 0	
						else:
							print "Title/Paper score:",titleeval[1],crscore,self._fname
							if not justcheck: 
								self.moveresult(2,printstr="OK title and high info fit. But no doi(Unsure): "+self._fname)
							return 2					
					
					### Old method check old items:
					#if (self.checkcrossref(cr)):
					#	if (int(cr.year)<=1999 and len(self.doi) is 0):
					#		# Highly possible right
					#		if not justcheck: self.movetodir("High")
					#		return True
					#	  Bentham, often blank doi
					#	elif (fdoi[:8] == '10.2174/' and len(self.doi) is 0):
					#		if not justcheck: self.movetodir("Done")
					#		return True
					#	elif (len(self.doi) is 0):
					#		print "Title/Paper score:",titleeval[1],crscore,self._fname
					#		if not justcheck: 
					#			self.moveresult(1,printstr="OK title and high info fit. But no doi(Highly): "+self._fname)
					#		return 1							
					#	else:
					#		if not justcheck: 
					#			self.moveresult(2,printstr="OK title and high info fit. But doi exist not fit(Unsure): "+self._fname)
					#		return 2								
					#elif(len(self.doi) is 0):
					#	# Maybe wrong file and no doi
					#	if not justcheck: 
					#		self.moveresult(2,printstr="Not found doi in file but ok title (Unsure): "+self._fname)
					#	return 2

			#fdoi,title wrong, no doi in file
			# Or in recursive mode
			if (len(self.doi) is 0 or recursive):
				if not justcheck: 
					self.moveresult(4,printstr="Both fdoi and title wrong, no doi in file(Fail): "+self._fname)
				return 4

			# Indeed, file has only one more doi, not the same to fname
			if (len(self.doi - set([fdoi])) is 1 ):
				print 'Fail fdoi/title. Paper with one more doi in file,',self._fname,',try recursive'
				return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=wtitle,justcheck=justcheck)
			elif(len(self.doi) > 1):
				if not justcheck: 
					self.moveresult(2,printstr="fdoi/title fail. Too much infile doi(Unsure): "+self._fname)
				return 2
			else:
				if not justcheck: 
					self.moveresult(4,printstr="What????? What?????(Fail):"+self._fname)
				return 4
		# not cr
		else:
			if (not recursive):
				self.finddoi(set([1,2,self.maxpage]))
				if (len(self.doi) is 1 or len(self.doi) is 2):
					print 'Error DOI filename,',self._fname,',try recursive'
					return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=wtitle,justcheck=justcheck)				
			if not justcheck: 
				self.moveresult(6,"Error DOI fname(Fail):"+self._fname)
			return 6