#! /usr/bin/env python
#coding:utf-8

import urllib,urllib2
import random
import socket
import os
import threading
import time,datetime
import re
import parsePage


def getCookie(url,user_agent):
	from urllib2 import Request,urlopen,URLError
	req = Request(url)
	req.add_header("User-Agent",user_agent)

	cookie = None
	try:
		resp = urlopen(req)
		cookieMap = resp.headers.dict
		cookies = []
		for key in cookieMap:
			if key.lower().find("cookie")>=0:
				cookies.append(cookieMap[key])
		cookie = ";".join(oneCookie.split(";")[0] for oneCookie in cookies)
		resp.close()
	except Exception,e:
		try:
			cookieMap = e.headers.dict
			cookies = []
			for key in cookieMap:
				if key.lower().find("cookie")>=0:
					cookies.append(cookieMap[key])


			cookie = ";".join(oneCookie.split(";")[0] for oneCookie in cookies)
		except:
			pass
	return cookie

def crawUrl(url, useCookie=False,timeout=None,user_agent=None):
	default_time = socket.socket().gettimeout()
	if timeout !=None:
		socket.socket().settimeout(timeout)

	ret = None
	redirectUrl = None
	statusCode = -1
	from urllib2 import Request,urlopen,URLError
	if user_agent==None:
		user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
	if useCookie:
		cookie = getCookie(url,user_agent)

	request = Request(url)
	request.add_header("User-Agent",user_agent)
	if useCookie:
		request.add_header("Cookie",cookie)
	try:
		ff = urlopen(request)
	except URLError,e:
		import sys,traceback
		excInfo = sys.exc_info()
		infoList = traceback.format_exception(*excInfo[0:3])
		print ''.join(infoList)

		if hasattr(e,'reason'):
			statusCode = e.reason[0]
		elif hasattr(e,'code'):
			statusCode = e.code
			redirectUrl = e.geturl()
		else:
			print '-----',url

		socket.socket().settimeout(default_time)
	else:
		statusCode = ff.code
		redirectUrl = ff.geturl()
		ret = ff.read()
		ff.close()
	socket.socket().settimeout(default_time)

	return ret,redirectUrl,statusCode

def parseOtc():
	currencyList = ("zil", "dew", "elf", "eos")
	#url="https://otcbtc.com/sell_offers?currency=eos&fiat_currency=cny&payment_type=all"

	sellUrlTpl = "https://otcbtc.com/sell_offers?currency=%s&fiat_currency=cny&payment_type=all"
	buyUrlTpl = "https://otcbtc.com/buy_offers?currency=%s&fiat_currency=cny&payment_type=all"
	for currency in currencyList:
		sellUrl = sellUrlTpl%(currency,)
		try:
			html,redirect,status=crawUrl(sellUrl)
		except urllib2.HTTPError:
			print html
		#print html
		recommendCardDiv = parsePage.drawFirstSectionFromHtmlByTag(html,'div', '<div class="recommend-card"')
		priceDiv = parsePage.drawFirstSectionFromHtmlByTag(recommendCardDiv, 'div', '<div class="recommend-card__price"')
		sellPrice = re.sub("<.*?>","",priceDiv).strip()
		#print priceDiv
		#print price

		buyUrl = buyUrlTpl%(currency,)
		try:
			html,redirect,status=crawUrl(buyUrl)
		except urllib2.HTTPError:
			print html
		#print html
		recommendCardDiv = parsePage.drawFirstSectionFromHtmlByTag(html,'div', '<div class="recommend-card"')
		priceDiv = parsePage.drawFirstSectionFromHtmlByTag(recommendCardDiv, 'div', '<div class="recommend-card__price"')
		buyPrice = re.sub("<.*?>","",priceDiv).strip()
		print "%s, %s, %s, %s, %.2f"%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), currency, buyPrice, sellPrice, (float(buyPrice)-float(sellPrice))*100/float(buyPrice))



if __name__ == "__main__":
	while True:
		parseOtc()
		time.sleep(5)
