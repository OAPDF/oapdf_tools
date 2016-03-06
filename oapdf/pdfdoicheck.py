#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

import os,re
import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
from StringIO import StringIO

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

TIMEOUT_SETTING=30
TIMEOUT_SETTING_DOWNLOAD=120

###### Function

fsre=re.compile(r'font-size:.*?px')
def fontsize2int(s):
	fs=fsre.search(s)
	try:
		if fs:
			return int(fs.group().replace('font-size:','').replace('px',''))
		else:
			return -1
	except:
		return -1

def getlargefontsize(s,cutoff=0.85):
	results=fsre.findall(s)
	setfs=set(results)
	listints=[ fontsize2int(i) for i in setfs]
	listints.sort()
	#print listints
	outdict={}

	total=0
	for i in setfs:
		ci=results.count(i)
		total+=ci
		outdict[fontsize2int(i)]=ci
	#print outdict

	fless=0
	limitsize=0
	for i in listints:
		fless+=outdict[i]
		if fless>total*cutoff:
			limitsize=i+1
			break
	#print "Limit Font size", limitsize
	return limitsize

def fontsizestr(s,cutoff=0.85,fontsize=0):
	if (fontsize>0):
		limitsize=fontsize
	else:
		limitsize=getlargefontsize(s,cutoff)
	bs=BeautifulSoup(s,'html.parser')
	bss=bs.findChildren('span')
	outstr=''
	for i in bss:
		if (fontsize2int( i.get('style','') ) >= limitsize):
			if (i.text):
				outstr+=i.text+' '
	#nstr= normalizeString(outstr)
	#print outstr
	return outstr


###### PDFdoiCheck class

class PDFdoiCheck(object):
	'''DOI named PDF file processor object'''
	#pdoi=re.compile("(?:\:|\\b)(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\|\"&\'<>])\\S)+)(?:\+?|\\b)")
	pdoi=DOI.pdoi
	def __init__(self,fname=""):
		self.handle=PDFHandler()
		self.doi=set()
		self.didpage=set()
		self.normaltxt=[]
		self.reset(fname)
		self.withSI=False
		self.fobj=None
		# Save real doi, esepecially when wrong doi
		self.realdoi=""
		
	@property
	def fname(self):
	    return self._fname
	
	def reset(self,fname,fobj=None):
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
		self.realdoi=""
		self.fobj=None
		if (fobj and isinstance(fobj,(file,StringIO))):
			self._fname= "None" #tmp file name for ignore check
			self.fobj=fobj
			self.maxpage=self.handle.GetPageNumber("",fobj=fobj)
			self.normaltxt=['' for i in range(self.maxpage)]
			return			
		if (not fname):
			return
		if (os.path.exists(fname) and os.path.splitext(fname)[1].lower()==".pdf"):
			self._fname=fname
			self.maxpage=self.handle.GetPageNumber(fname)
			self.normaltxt=['' for i in range(self.maxpage)]
		else:
			print "Error file exist or pdf type. Check it"

	def setfile(self,fname):
		'''Seldomly use'''
		self.reset(fname)

	def setfname4fobj(self,fname):
		'''Just set fname for file obj'''
		if (fobj):
			self._fname=fname
		else:
			print "File object not exists!"

	def savefobj2file(self,fname="",doi="",state=None,fobj=None):
		'''Save the current file obj(file/StringIO) to a file
		And also set the self.fname'''
		if (not fname and not doi):
			print "File name or doi is not given!"
			return
		if (doi and not fname):
			doi=DOI(doi)
			fname=doi.quote()+'.pdf'
			
		if (state is not None):
			outdir=self.judgedirs.get(state,'.')
			if not os.path.exists(outdir):os.makedirs(outdir)
			fname=outdir+os.sep+fname	

		if not fobj: fobj=self.fobj		

		if (fname and fobj and not fobj.closed):
			fobj.seek(0)
			if (not os.path.exists(fname)):				
				f=open(fname,'wb')
				f.write(fobj.read())
				f.close()
				fobj.seek(0)
				self._fname=fname
				return True
			else:
				print "File has exist...."
				return False

	def renamefile(self,newname):
		'''Rename a file'''
		try:
			if not self._fname or self._fname is "None": 
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
		if not self._fname or self._fname is "None": 
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
		if not self._fname or self._fname is "None": 
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
			print e,'move fail? in pdfdoicheck.moveresult'
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

	def findtext(self,text,similarity=0.95, page=1):
		'''Just Find text in Page, Don't search doi and save it'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		if (self.maxpage is 0):
			print 'Error max page 0 for '+self._fname
			return ""
		if (isinstance(page,(str,float)) ):
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
				outstr=self.pdfcontextpreprocess(self.handle.GetSinglePage(self._fname,page,fobj=self.fobj))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
			return self.hascontent(text, similarity=similarity, page=page)[0]
		elif ( isinstance(page,(list,tuple,set))):
			outyn=False
			for i in page:
				outyn= self.findtext(text,similarity=similarity,page=i)
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
		if (isinstance(page,(str,float)) ):
			page=int(page)
		if (isinstance(page,int)):
			if (page <= 0 ):
				outstr=self.pdfcontextpreprocess(self.handle.GetAllPages(self._fname,fobj=self.fobj))
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr)))
				self.normaltxt=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.update(range(1,self.maxpage+1))
			# Only valid page
			if (page>self.maxpage): 
				page=self.maxpage
			# Only page not process before
			if (page not in self.didpage):
				outstr=self.pdfcontextpreprocess(self.handle.GetSinglePage(self._fname,page,fobj=self.fobj))
				self.doi.update(self.doiresultprocess(self.pdoi.findall(outstr)))
				self.normaltxt[page-1]=normalizeString(outstr).lower().strip().replace(' ','')
				self.didpage.add(page)
		elif ( isinstance(page,(list,tuple,set))):
			for i in page:
				self.finddoi(i)

	def totalpages(self,pages):
		'''To get total page from record pages'''
		if (not pages or not pages.strip()):
			return 0

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
		elif (len(ps) == 1):
			#Only first page
			return -1
		else:
			return 0

	######### Start to judge ######################
	def hascontent(self,text, similarity=0.95,page=None,algorithm=2):
		'''Normalize text and find it in normalized pdf content found before.
		Normal use algorithm 2, for title use algorithm 3'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return (False,0.0)

		text=normalizeString(text).lower().strip().replace(' ','')
		if (not text):
			return (False,0.0)
		if (len(text)<3):
			return (False,0.0)

		try:
			#Check all parse before
			if (not page or (isinstance(page,int) and (page>self.maxpage or page<=0))):
				if (len(text)==3):
					perfect=text in ''.join(self.normaltxt)
					return (perfect,float(perfect)/2)
				if (similarity<1.0):
					#print text,''.join(self.normaltxt)
					sim=strsimilarity(''.join(self.normaltxt),text,algorithm=algorithm)
					return (sim >= similarity,sim)
				else:
					perfect=text in ''.join(self.normaltxt)
					return (perfect,float(perfect))
			elif (isinstance(page,int)):
				if (len(text)==3):
					perfect=text in self.normaltxt[page-1]
					return (perfect,float(perfect)/2)
				if (similarity<1.0):
					#print text,self.normaltxt[page-1]
					sim=strsimilarity(self.normaltxt[page-1],text,algorithm=algorithm)
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
		'''For check title. Some special case in title...
		Use algorithm 3 for comparison.'''
		if not self._fname: 
			print "File Name Not Set!!!"
			return ""
		title=escaper.unescape(title)
		#title=re.sub(r"(?:<.?sup>|<.?i>|\$\$.*?{.*?}.*?\$\$)","",title)
		title=re.sub(r"(?:<.+?>|\$\$.*?{.*?}.*?\$\$)","",title)
		return self.hascontent(title, similarity=similarity,page=page,algorithm=3)

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
		outstr=self.handle.GetPages(self._fname,self.didpage,fobj=self.fobj).lower()
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
			try:
				totalpagenumber=self.totalpages(cr.pages)
			except Exception as e:
				totalpagenumber=1
				print e
			totalpagewrong=False
			if totalpagenumber>0 and not (self.maxpage >= totalpagenumber and self.maxpage <= totalpagenumber+2):
				totalpagewrong=True

			spages=self.hascontent(cr.pages,1.0,page=1)[1]
			if (spages<0.1):
				spages2=self.hascontent(cr.pages.split('-')[0],1.0,page=1)[1]
				if (spages2>spages):
					spages=spages2
			if spages>0.1 and not totalpagewrong:
				spages+=1.5
			elif (not totalpagewrong):
				if (len(cr.pages.split('-')[0])<3):
					spages+=1.5

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
			if spages>0.1 and not totalpagewrong:
				spages+=1.5
			elif (not totalpagewrong):
				if (len(cr.pages.split('-')[0])<3):
					spages+=1.5

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
			self.realdoi=doi
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

	def renamecheck(self,fname,wtitle=0.65,cutoff=0.85,justcheck=False,resetfile=True,fdoi=None,excludedoi=None, fobj=None):
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


		if (resetfile and isinstance(fobj,(file,StringIO))):
			self.reset(fname="",fobj=fobj)
			fname="None"

		# len(self.doi) is 1 and len(self.doi - excludedoi) is 1 : 
		# :: First Run and perform check
		# len(self.doi) is 1 or len(self.doi - excludedoi) is 1 :
		if (not fname and not fdoi):
			print "No given file name or doi! (Return 6)"
			return 6

		if (fname and not fdoi and excludedoi):
			print "What do you want?! No excludedoi set by user! (Return 9)"
			return 9

		
		if (resetfile and fname !="None"): 
			self.reset(fname)
		elif(resetfile and not isinstance(fobj,(file,StringIO))):
			print "Use reset file but no file name/object is given!"
			return 9

		if (self.maxpage == 0):
			if not justcheck: 
				self.moveresult(5, printstr="Error Page 0 (Page0, R5): "+self._fname)
			return 5

		if (not excludedoi):
			excludedoi=set()

		if (not fdoi):
			#File obj is ""
			fdoi=DOI(os.path.splitext(os.path.basename(self._fname))[0])
		else:
			fdoi=DOI(fdoi)

		recursive= (len(excludedoi) > 0)
		# If in recursive, don't move file!
		if recursive: justcheck=True

		if resetfile and not recursive:
			self.realdoi=fdoi

		# Only find DOI in first time!
		if (not recursive and fdoi): 
			self.finddoi(1)
		elif (not recursive and not fdoi):
			self.finddoi(set([1,2,self.maxpage]))

		# file doi is shit..Recursively use doi in file or fail
		if (not fdoi and not recursive):
			if (len(self.doi) is 1 or len(self.doi) is 2):
				print "Origin fdoi wrong but has 1~2 dois in file:",self._fname,
				return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=justcheck)
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
			#print "pages:",self.maxpage,' in crossref:',cr.pages,totalpagenumber
			if totalpagenumber>0 and not (self.maxpage >= totalpagenumber and self.maxpage <= totalpagenumber+2):
				totalpagewrong=True
				# When paper with supporting information
				if (self.maxpage > totalpagenumber+2):
					self.finddoi(page=2)
					if (self.withSI or (self.findtext('Supporting Information', page=[totalpagenumber+1,totalpagenumber+2])
						and self.findtext(cr.title, similarity=0.75, page=[totalpagenumber+1,totalpagenumber+2]))):
						if not recursive : self.finddoi(totalpagenumber);
						self.withSI=True
						totalpagewrong=False
					# For NIH Public Access
					elif (self.hascontent("NIH Public Access")[0]):
						totalpagewrong=False
					#Such as some Nature with SI in paper without notify.
					elif (self.withSI or (totalpagenumber>1 and self.findtext("acknowledgment", page=[totalpagenumber-1, totalpagenumber]) 
						and self.findtext("reference", page=[totalpagenumber-1, totalpagenumber]))):
						self.withSI=True
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
					self.realdoi=fdoi
					if not justcheck: self.moveresult(0)
					return 0

			# Further check doi in page2/last, Finally, will check 1,2 and last pages.
			if (recursive):
				doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True,justcheck=True) or doivalid )
			else:
				doivalid= ( self.checkdoi(fdoi,page=2,iterfind=True) or doivalid )

			if len(self.doi)>3:
				# Too much doi may be some abstract
				self.moveresult(2,printstr='Has more than 3 dois! (Unsure):'+self._fname)
				return 2

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
					return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=justcheck)
				else:
					if not justcheck: 
						self.moveresult(4,printstr="PDF Page "+str(self.maxpage)+"!="+str(totalpagenumber)+"(Fail): "+self._fname)
					return 4

			if (not totalpagewrong):
				crscore=self.scorefitting(cr)
				if (self.maxpage <= totalpagenumber+2): 
					# Maybe check when maxpage >total+2
					titleeval=self.checktitle(cr.title)
				titlevalid=titleeval[0]
				try:
					paperyear=int(cr.year)
				except:
					paperyear=9999
				try:
					# Too old maybe lost information
					if (paperyear>1990):
						titlevalid=titlevalid or (titleeval[1]*wtitle+crscore['total'])>=cutoff
					else:
						titlevalid=titlevalid or (titleeval[1]*wtitle+crscore['total'])>=cutoff-0.1
				#(self.checktitle(cr.title,similarity=0.85) and self.checkcrossref(cr))
				except Exception as e:
					print e

				if (doivalid):
					if (titlevalid):					
						# Yes! Good PDF!
						self.realdoi=fdoi
						if not justcheck: self.moveresult(0)
						return 0

					print "Title/Paper score:",titleeval[1],crscore,self._fname
					if (len(self.doi - set([fdoi])) == 1 and not recursive):
						
						# Try one more
						newresult = self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=True)
						if (newresult is 0):
							newdoi=DOI(list(self.doi - set([fdoi]))[0])
							self.realdoi=newdoi
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
					tmpdois=set(self.doi)
					for d in tmpdois:
						dd=DOI(d)
						if ( not dd.valid_doiorg(geturl=False) ):
							self.doi.remove(d)
							
					# Old paper don't have doi...
					if len(self.doi) is 0 and totalpagenumber>0:
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
						elif (titleeval[1]>=0.90 and crscore['pages']>=0.5 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9) and crscore['authors']>=0.7):
							if not justcheck: self.moveresult(0)
							return 0
						elif (titleeval[1]>=0.75 or crscore['total'] >=0.25):
							print "Title/Paper score:",titleeval[1],crscore,self._fname
							if not justcheck: 
								self.moveresult(1,printstr="OK title and high info fit. But no doi(Highly): "+self._fname)
								return 1
						else:
							print "Title/Paper score:",titleeval[1],crscore,self._fname
							if not justcheck: 
								self.moveresult(2,printstr="OK title and ok info fit. But no doi(Unsure): "+self._fname)
							return 2
					elif len(self.doi) is 0 and totalpagenumber== -1:
						if (titleeval[1]>=0.90 and crscore['pages']>=0.5 and crscore['year']>=0.9 and (crscore['journal']>=0.9 or crscore['issn']>=0.9) and crscore['authors']>=0.7):
							if not justcheck: self.moveresult(0)
							return 0
						else:
							print "Title/Paper score:",titleeval[1],crscore,self._fname
							if not justcheck: 
								self.moveresult(2,printstr="OK title and high info fit. But no doi and no total pages(Unsure): "+self._fname)
							return 2												
					elif len(self.doi) is 0 and totalpagenumber<=0:
						print "Title/Paper score:",titleeval[1],crscore,self._fname
						if not justcheck: 
							self.moveresult(2,printstr="OK title and high info fit. But no doi and no total pages(Unsure): "+self._fname)
						return 2
					elif ( len(self.doi) > 0 and not recursive):
						print "Good title but file doesn't contain fdoi, however it has >0 doi in file. "
						outnow=self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=True)
						if outnow > 0:
							if not justcheck:
								self.moveresult(2,printstr="OK title but not fdoi. In file doi is not good(Unsure): "+self._fname)
							return 2
						elif(outnow==0):
							print 'Good Title but Fail fdoi. Paper has good in file doi,',self._fname,',try recursive'
							return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=justcheck)

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
				return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=justcheck)
			elif(len(self.doi) > 1):
				if not justcheck: 
					self.moveresult(4,printstr="fdoi/title fail. Too much infile doi(Fail): "+self._fname)
				return 4
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
					return self.recursivedoicheck(excludedoi,olddoi=fdoi,wtitle=wtitle,cutoff=cutoff,justcheck=justcheck)				
			if not justcheck: 
				self.moveresult(6,"Error DOI fname(Fail):"+self._fname)
			return 6

	def checkonlinepdf(self,url=None,fobj=None,doi="",wtitle=0.65,cutoff=0.85,params=None):
		'''Check the online PDF'''
		if not url and not fobj:
			print "No url or fobj is set!"
			return 9
		if url:
			if not params:params={}
			if not header:headers={}
			r=requests.get(url,timeout=TIMEOUT_SETTING_DOWNLOAD)
			if (r.status_code == 200):
				if 'application/pdf' in r.headers['Content-Type'].lower().strip():
					fobj=StringIO(r.content)
				else:
					print "No a pdf file for ",url
					return 9
			else:
				print "Error connection to the online pdf file",url,'state:',r.status_code
				return 9
		if not fobj:
			print "Can't get the file object!"
			return 9
		return self.renamecheck(fname="", fobj=fobj ,wtitle=wtitle,cutoff=cutoff,
			justcheck=True,fdoi=doi,resetfile=True,excludedoi=None)

	def getbigtitle(self,fname=None,cutoff=0.85,fontsize=0,autotry=False):
		'''Get the title or big font context'''
		if not fname: fname=self._fname
		if (not fname):
			print "No file name is set!"
			return ""
		s=self.handle.GetPages(fname,pagenos=[1,2,3],html=True,fobj=self.fobj)
		self.handle.reset(html=True)
		result=""
		if autotry:
			for i in range(19):
				cutoffnow=1.0-0.05*(i+1)
				result=normalizeString(fontsizestr(s,cutoff=cutoffnow))
				if (len(result)> 10):
					break
		else:
			result=normalizeString(fontsizestr(s,cutoff=cutoff,fontsize=fontsize))
		return result

	def removegarbage(self,fname=None,cutoff=0.85,fontsize=0,autotry=False,notdelete=False):
		'''Remove patents, supporting informations files'''
		if not fname: fname=self._fname
		if (not fname or (fname == "None" and not notdelete)):
			print "No file name is set!"
			return 0
		outstr=self.getbigtitle(fname=fname,cutoff=cutoff,fontsize=fontsize,autotry=autotry).lower().strip().replace(' ','')

		## Open Access
		#oawords=['NIH Public Access']
		#moveyn=False
		#for word in oawords:
		#	word=word.lower().strip().replace(" ",'')
		#	sim=strsimilarity(outstr,word)
		#	if (sim >= 0.95 and fname != "None"):
		#		os.renames(fname,'OAPub/'+os.path.split(fname)[1])
		#		self._fname='OAPub/'+os.path.split(fname)[1]
		#		moveyn=True
		#		return 1

		# Patents, SI
		gwords=['EUROPEAN PATENT APPLICATION', 'EUROPEAN PATENT SPECIFICATION',
		'United States Patent', 'AUSTRALIAN PATENT']
		for word in gwords:
			word=word.lower().strip().replace(" ",'')
			sim=strsimilarity(outstr,word)
			if (sim >= 0.95):
				if (not notdelete):
					os.remove(fname)
				elif ( fname != "None" ):
					tmp=os.path.splitext(fname)
					os.renames(fname,tmp[0]+'@.Patent'+tmp[1])
					self._fname=tmp[0]+'@.Patent'+tmp[1]
				return 2

		gwords=['Supporting Information']
		for word in gwords:
			word=word.lower().strip().replace(" ",'')
			sim=strsimilarity(outstr,word)
			if (sim >= 0.95):
				if (not notdelete):
					os.remove(fname)
				elif ( fname != "None" ):
					tmp=os.path.splitext(fname)
					os.renames(fname,tmp[0]+'@.SI'+tmp[1])
					self._fname=tmp[0]+'@.SI'+tmp[1]
				return 3

	def tryrenamefromtitle(self,fname=None,cutoff=0.85,fontsize=0,autotry=False,wtitle=0.65):
		if not fname: fname=self._fname
		if (not fname or (fname == "None")):
			print "No file name is set!"
			return 0
		outstr=self.getbigtitle(fname=fname,cutoff=cutoff,fontsize=fontsize,autotry=autotry).lower().strip()
		print outstr
		url="http://api.crossref.org/works?query="+normalizeString(outstr)+"&rows=5"
		r=requests.get(url,timeout=TIMEOUT_SETTING)
		dois=[]
		if (r.status_code is 200):
			datas=r.json().get('message',{'items':[]}).get('items',[])
			for data in datas:
				dois.append(data.get('DOI',''))

		self.reset(fname)
		outnow=99999
		for doi in dois:
			print "Try doi:",doi,'for',fname
			self.doi=set([doi])
			out=self.renamecheck(fname=fname, fobj=None ,wtitle=wtitle,cutoff=cutoff,
				justcheck=False,fdoi=None,resetfile=False,excludedoi=None)
			if out ==0:
				break
			elif outnow>out:
				outnow=out






