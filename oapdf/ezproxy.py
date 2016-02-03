#! /usr/bin/env python
# -*- coding: utf-8 -*-

#menu
#http://creativaplus.uaslp.mx/login?user=cgiuser&pass=cgipass
# post : http://ezproxy.harford.edu/login?user=21556768546687&url=
# http://ezproxy.lcsc.edu:2048/login?user=kdleach&pass=021783
# http://webserver.macu.edu:2048/login 3952//3952
#  http://ezproxy.reinhardt.edu:2048/login brown//45199

class EzProxy(object):
	def __init__(self,proxy):
		'''Use a ezproxy url to initialize, without ?login
		can be http://ezproxy.harvard.edu:8080/''' 
		self.proxy=proxy

	def reset(self,proxy,user="",passwd=None):
		self.proxy=proxy
		self.user=user
		self.passwd=passwd

	def setinfo(self,user,passwd):
		'''Setup parameters'''
		self.user=user
		self.passwd=passwd

	def geturl(self):
		url=self.url.rstrip('/')+'/login?user='+self.user
		if (self.passwd):
			url+='&pass='+self.passwd
		url+='&url='
		return url
