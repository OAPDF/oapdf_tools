#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''A simple wrapper for CrossRefAPI'''

import urllib2,json

timeout_setting=30
timeout_setting_download=120

class CrossRefAPI(object):
	'''Simple wrapper for CrossRef API'''

	def filterstr(self,filterdict):
		'''Generate string for filter'''
		filters=[]
		for k,v in filterdict.items():
			filters.append(k+':'+str(v))
		return ','.join(filters)

	def getqueryurl(self,query,rows=10,offset=0,papertype='journal-article',sample=0,filterdict={},cursor='',qstr=False):
		'''Get query url, support rows/offset/cursor/sample
		Default get journal-article. Support more filters in dict format'''
		if (not query):
			return ""
		query=str(query)
		# Basic options
		if (sample>0):
			optstrbase='sample='+str(sample)
		elif (cursor):
			optstrbase="rows="+str(rows)+'&cursor='+cursor
		elif offset<=0:
			optstrbase="rows="+str(rows)
		else:
			optstrbase="rows="+str(rows)+"&offset="+str(offset)

		optstr=optstrbase
		# Deal with filter
		if (papertype):
			optstr+="&filter=type:"+papertype
			if (filterdict):
				optstr+=','+self.filterstr(filterdict)
		elif (filterdict):
			optstr+='&filter='+self.filterstr(filterdict)

		if (qstr):
			return "http://api.crossref.org/works?query="+query+"&"+optstr
		elif (len(query) == 9 and query[4] == '-'):
			return "http://api.crossref.org/journals/"+query+"/works?"+optstr
		elif ('10.' in query):
			return "http://api.crossref.org/prefixes/"+query+"/works?"+optstr
		elif ( query.isdigit()):
			return "http://api.crossref.org/members/"+query+"/works?"+optstr
		else:
			return "http://api.crossref.org/works?query="+query+"&"+optstr

	def getquerytotal(self,query,papertype=None,filterdict={}):
		'''Get total result number for a query'''
		if (not query):
			return 0
		j1= self.getqueryurl(query,rows=1,papertype=papertype,filterdict=filterdict)
		if (j1):
			r=urllib2.urlopen(j1,timeout=timeout_setting)
			j=json.loads(r.read())
			r.close()
			return int(j['message'].get('total-results',0))
		else:
			return 0

	def getalldoi2file(self,query,fname,papertype=None,filterdict={},getissn=False):
		'''Get All doi for a query to a file.
		getissn can also analyse all issn for this query'''
		if (not query or not fname):
			return
		issns=set()
		total=self.getquerytotal(query,papertype=papertype,filterdict=filterdict)
		f=open(fname,'w')
		print "Total articles:",total
		f.write("# Total articles: "+str(total)+'\n')
		step=1000
		maxround=total/step+1
		nextcursor="*"
		for i in range(maxround):
			needurl=self.getqueryurl(query,rows=step,cursor=nextcursor,papertype=papertype,filterdict=filterdict)
			r=urllib2.urlopen(needurl,timeout=timeout_setting_download)
			js=json.loads(r.read())
			newcursor=js['message'].get('next-cursor',nextcursor)
			if nextcursor == newcursor:
				break
			nextcursor=newcursor
			for j in js['message']['items']:
				doi=j.get("DOI","")
				if (getissn):
					issn=j.get('ISSN')
					issns.update(issn)
				f.write(doi+'\n')
		if (getissn):
			for issn in issns:
				f.write('# '+issn+'\n')
		f.close()

	def is_doaj(self,query):
		'''Test a query is in DOAJ, often use doi'''
		return self.getquerytotal(query,papertype=None,filterdict={'directory':'DOAJ'})>0