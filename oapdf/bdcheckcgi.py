#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last Update: 2016.1.25 12:20PM

'''Module for bdcheck.cgi'''

import requests,json,time
try:
	from .doi import DOI
except (ImportError,ValueError) as e:
	from doi import DOI

TIMEOUT_SETTING=30
TIMEOUT_SETTING_DOWNLOAD=120

class BDCheck(object):
	url="http://oapdf.sourceforge.net/cgi-bin/bdcheck.cgi?owner=oapdf"

	def get(self,doi):
		'''Get list whether [bdcheck,oapdf,free] for single doi
		Return a dict for multi dois'''
		try:
			if (isinstance(doi,str)):
				doi=DOI(doi)
				if (doi):
					r=requests.get(self.url+"&doi="+doi+"&select=True",timeout=TIMEOUT_SETTING)
					if r.status_code ==200:
						return r.json().get(doi,[])
				return [0,0,0]
			# if dois in list/tuple/set
			elif(isinstance(doi,(list,tuple,set))):
				dois=list(doi)
				result={}
				length=len(dois)
				maxround= length/100+1 if length%100 != 0 else length/100
				for i in range(0,maxround):
					if ((i+1)*100>=len(dois)):
						doisjs=json.dumps(dois[i*100:])
					else:
						doisjs=json.dumps(dois[i*100:(i+1)*100])
					param={'dois':doisjs}
					r=requests.post(self.url+"&select=True",params=param,timeout=TIMEOUT_SETTING)
					if r.status_code == 200:
						result.update(r.json())
					time.sleep(1)
				return result
			return [0,0,0]
		except Exception as e:
			print e,"SF BDCheck Get Fail.."
			if (isinstance(doi,(list,tuple,set))): return {}
			return [0,0,0] 


	def set(self,doi,oapdf=None,free=None):
		'''Update the bdcheck even oapdf/free in library
			If give a list of doi, just post them. 
			No return.'''
		try:
			if (isinstance(doi,str)):
				doi=DOI(doi)
				if (doi):
					if (oapdf and free):
						r=requests.get(self.url+"&doi="+doi+"&update=True&oapdf=True&free=True",timeout=TIMEOUT_SETTING)
					elif oapdf:
						r=requests.get(self.url+"&doi="+doi+"&update=True&oapdf=True",timeout=TIMEOUT_SETTING)				
					elif free:
						r=requests.get(self.url+"&doi="+doi+"&update=True&free=True",timeout=TIMEOUT_SETTING)
					else:
						r=requests.get(self.url+"&doi="+doi+"&update=True",timeout=TIMEOUT_SETTING)

			elif(isinstance(doi,(list,tuple,set))):
				dois=list(doi)
				result={}
				length=len(dois)
				maxround= length/100+1 if length%100 != 0 else length/100
				for i in range(0,maxround):
					if ((i+1)*100>=len(dois)):
						doisjs=json.dumps(dois[i*100:])
					else:
						doisjs=json.dumps(dois[i*100:(i+1)*100])
					param={'dois':doisjs}
					if (oapdf and free):
						r=requests.post(self.url+"&update=True&oapdf=True&free=True",params=param,timeout=TIMEOUT_SETTING)
					elif oapdf:
						r=requests.post(self.url+"&update=True&oapdf=True",params=param, timeout=TIMEOUT_SETTING)				
					elif free:
						r=requests.post(self.url+"&update=True&free=True",params=param, timeout=TIMEOUT_SETTING)
					else:
						r=requests.post(self.url+"&update=True",params=param, timeout=TIMEOUT_SETTING)
					time.sleep(1)


		except Exception as e:
			print e,"SF BDCheck Set Fail.."

	def setbycheck(self,doi):
		'''Update the bdcheck/oapdf/free in library based on check oapdf/free
		Can't set the record to "bdcheck" state
		return the [oapdf,free]'''
		try:
			if (isinstance(doi,str)):
				doi=DOI(doi)
				if (doi):
					oapdffree=doi.freedownload(outtuple=True)
					if (oapdffree[0] and oapdffree[1]):
						r=requests.get(self.url+"&doi="+doi+"&update=True&oapdf=True&free=True",timeout=TIMEOUT_SETTING)
					elif oapdffree[0]:
						r=requests.get(self.url+"&doi="+doi+"&update=True&oapdf=True",timeout=TIMEOUT_SETTING)				
					elif oapdffree[1]:
						r=requests.get(self.url+"&doi="+doi+"&update=True&free=True",timeout=TIMEOUT_SETTING)
					return oapdffree
			return [False,False]
		except Exception as e:
			print e,"SF BDCheck SetByCheck Fail.."
			return [False,False]

	def filterdois(self,indois,oapdf=1,crjson=False):
		'''Filter the input filter DOI, only do for Not Search Before
		Can also filter dois in OAPDF:
			oapdf>0: bdcheck or oapdf
			oapdf=0: bdcheck 
			oapdf<0: bdcheck and oapdf
		Return a set (faster) '''
		try:
			if (isinstance(indois,(list,set,tuple))):
				# dois in list/set/tuple 
				# or items in crossref results
				outdois=set()
				if (not crjson):
					outdict = self.get(indois)
					for k,v in outdict.items():
						if oapdf>0:
							if sum(v[:2]) >= 1:
								outdois.add(k)
						elif oapdf<0:
							if sum(v[:2]) is 2:
								outdois.add(k)
						else:
							if v[0] is 1:
								outdois.add(k)
					return outdois
				else:
					indois=[ item.get("DOI","") for item in indois ]
					return self.filterdois(indois,oapdf=oapdf,crjson=False)
			elif (isinstance(indois,dict) and crjson):
				indois=[ item.get("DOI","") for item in indois.get('message',{}).get('items',[]) ]
				return self.filterdois(indois,oapdf=oapdf,crjson=False)
		except Exception as e:
			print e,"SF BDCheck filterdois Fail.."
			return set()
