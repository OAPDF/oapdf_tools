#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Last update: 2016.1.29-23:30

import re,requests,random

TIMEOUT_SETTING=30

header={'headers':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

class GatherProxy(object):
	'''To get proxy from http://gatherproxy.com/'''
	url='http://gatherproxy.com/proxylist'
	pre1=re.compile(r'<tr.*?>(?:.|\n)*?</tr>')
	pre2=re.compile(r"(?<=\(\').+?(?=\'\))")

	def getelite(self,pages=1,uptime=95,fast=True):
		'''Get Elite Anomy proxy
		Pages define how many pages to get
		Uptime define the uptime(L/D)
		fast define only use fast proxy with short reponse time'''

		proxies=set()
		for i in range(1,pages+1):
			params={"Type":"elite","PageIdx":str(i),"Uptime":str(uptime)}
			try:
				r=requests.post(self.url+"/anonymity/t=Elite",params=params,headers=header,timeout=TIMEOUT_SETTING)
				for td in self.pre1.findall(r.text):
					if fast and 'center fast' not in td:
						continue 
					try:
						tmp= self.pre2.findall(str(td))
						if(len(tmp)==2):
							proxies.add(tmp[0]+":"+str(int('0x'+tmp[1],16)))
					except:
						pass
			except Exception as e:
				print e,' when get elite proxy from gatherproxy..'
		return proxies

	def getports(self,pages=1,uptime=95,fast=True,port=""):
		'''Get Elite Anomy proxy
		Pages define how many pages to get
		Uptime define the uptime(L/D)
		fast define only use fast proxy with short reponse time'''
		if not port:
			ports=['80','8080','3128']
			port=random.sample(ports,1)[0]
		proxies=set()
		for i in range(1,pages+1):
			params={"Port":port,"PageIdx":str(i),"Uptime":str(uptime)}
			try:
				r=requests.post(self.url+"/port/"+port,params=params,headers=header,timeout=TIMEOUT_SETTING)
				for td in self.pre1.findall(r.text):
					if fast and 'center fast' not in td:
						continue 
					try:
						tmp= self.pre2.findall(str(td))
						if(len(tmp)==2):
							proxies.add(tmp[0]+":"+str(int('0x'+tmp[1],16)))
					except:
						pass
			except Exception as e:
				print e,' when get port',port,'proxy from gatherproxy..'
		return proxies

class ProxyPool(object):
	'''A proxypool class to obtain proxy'''

	gatherproxy=GatherProxy()

	def __init__(self):
		self.pool=set()
		self.dead=set()

	def reset(self):
		self.pool.clear()
		self.dead.clear()

	def updateGatherProxy(self,pages=1,uptime=95,fast=True,port=None):
		'''Use GatherProxy to update proxy pool'''
		#getelite -> getports
		self.pool.update(self.gatherproxy.getports(pages=pages,uptime=uptime,fast=fast,port=port))
		self.pool=self.pool-self.dead
		if (not self.pool):
			self.updateGatherProxy(self,pages=pages+1,uptime=uptime-10,fast=fast,port=port)

	def removeproxy(self,proxy):
		'''Remove a proxy from pool'''
		if (proxy in self.pool):
			self.pool.remove(proxy)

	def randomchoose(self):
		'''Random Get a proxy from pool'''
		if (self.pool):
			return random.sample(self.pool,1)[0]
		else:
			self.updateGatherProxy()
			return random.sample(self.pool,1)[0]

	def getproxy(self,maxtry=10,nowtry=0):
		'''Get a dict format proxy randomly'''
		if (nowtry>maxtry):
			return ""
		proxy=self.randomchoose()
		proxies={'http':proxy,'https':proxy}
		#r=requests.get('http://icanhazip.com',proxies=proxies,timeout=1)
		try:
			r=requests.get('http://dx.doi.org',proxies=proxies,timeout=5)
			if (r.status_code == 200 ):
				return proxies
			else:
				self.removeproxy(proxy)
				self.dead.add(proxy)
				return self.getproxy(maxtry=maxtry,nowtry=nowtry+1)
		except Exception as e:
			print e
			self.removeproxy(proxy)
			self.dead.add(proxy)
			return self.getproxy(maxtry=maxtry,nowtry=nowtry+1)

#gp=GatherProxy()
#print random.sample(gp.getelite(3),1)