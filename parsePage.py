#! /usr/bin/env python
#coding:utf-8

import re
import httplib

#提取内容
def parseSubString(src, beginPos, beginTag, endTag):
	pos1	= src.find(beginTag, beginPos)
	pos2	= src.find(endTag, pos1 +len(beginTag))
	if ( pos1<0 or pos2<0 ):
		return None
	pos1	+= len(beginTag)
	return src[pos1 : pos2]

def splitSection(html):
	#将html分段，认为当出现连续两个换行时，分段
	sectionList = []
	sec = ""
	oh = html.split("\n")
	elCount = 10	#空行数量
	for i, ol in enumerate(oh):
		line = ol.strip()
		if line == "":
			elCount += 1
			sec += ol +"\n"
		else:
			if elCount > 2:
				sectionList.append(sec)
				sec = ol +"\n"
			else:
				sec += ol +"\n"
			elCount = 0
	sectionList.append(sec[:-1])
	return sectionList

#从html中提取出以tagPre开头的一段tag，取的是第一次出现的一段字符串
def drawFirstSectionFromHtmlByTag(html,tag,tagPre):
	posStart = html.find(tagPre)
	if posStart < 0:
		return None
	posFind = posStart+len(tagPre)
	idx = 0
	while True:
		posNext = html.find(tag, posFind)
		if posNext == -1:
			return None
		if html[posNext-2:posNext+len(tag)] == '</'+tag:
			if idx <= 0:
				posEnd = posNext+len(tag)+1
				break
			else:
				posFind = posNext+len(tag)
				idx -= 1
		elif html[posNext-1:posNext+len(tag)] == '<'+tag:
			posFind = posNext+len(tag)
			idx += 1
		else:
			posFind = posNext+len(tag)
	return html[posStart:posEnd]

#从html中提取出以tagPre开头的所有tag组成的列表
def drawAllSectionFromHtmlByTag(html,tag,tagPre):
	posStart = html.find(tagPre)
	secList = []
	if posStart < 0:
		return secList
	posFind = posStart+len(tagPre)
	idx = 0
	while True:
		posNext = html.find(tag, posFind)
		if posNext == -1:
			break
		if html[posNext-2:posNext+len(tag)] == '</'+tag:
			if idx == 0:
				posEnd = posNext+len(tag)+1
				secList.append(html[posStart:posEnd])
				posStart = html.find(tagPre, posEnd)
				if posStart < 0:
					break
				posFind = posStart+len(tagPre)
			else:
				posFind = posNext+len(tag)
				idx -= 1
		elif html[posNext-1:posNext+len(tag)] == '<'+tag:
			posFind = posNext+len(tag)
			idx += 1
		else:
			posFind = posNext+len(tag)
	return secList

def splitHtml(html):
	#将html段落切分，标记tag
	#pieces = re.split("[<>]", html)
	#pieces = re.findall("(<.*?>)(.*?)(<.*?>)", html)
	pieces = []
	pos = 0
	i=0
	while True:
		if i > len(html):
			break
		if i < len(html):
			c = html[i]
		else:
			c = "None"
		#检查是否命中分界线
		hitSep = False
		if c in ["<", "None"]:
			hitSep = True
			npos = i
			#命中分界线
		if c in [">"]:
			hitSep = True
			npos = i+1
		#处理后事
		if hitSep and c!="None" and html[pos]=="<":
			#先不急于分段，检查分界线是否在""包裹中
			status = 0	#0:不在"中  1:"中  2:'中
			for j in range(pos+1, i+1):
				if html[j] == "\"":
					if html[j-1] != "\\":
						if status==0:	status=1
						elif status==1:	status=0
					else:
						#解决url中以\结尾的sb问题
						lastQpos = html.rfind("\"", 0, j-1)
						tmp = html[:lastQpos].replace(" ","").replace("\t","")
						if tmp.endswith("href="):
							#是个\结尾的url
							status = 0
				if html[j] == "'" and html[j-1] != "\\":
					if status==0:	status=2
					elif status==2:	status=0
			if status != 0:
				hitSep = False
		if hitSep:
			p = html[pos:npos]
			pos = npos
			if len(p) > 0:
				pieces.append(p)
		i+=1
#	print "\n".join(pieces)
	return pieces

def markHtmlTag(pieces):
	ret = []
	for p in pieces:
		tag = "text"
		if p.startswith("<!--"):
			tag = "comment"
		elif p.startswith('<![CDATA['):
			tag = "cdata"
		elif p.startswith("<"):
			a = p.strip("<>")
			a = a.replace("\t", " ").split(" ")[0]
			tag = a
		ret.append((p,tag))
	return ret
#----------------------------------------------------------------------
def splitContentByTopDiv(html):

	#排除javascript，因为其中有可能有导致分段中止的tag
	while True:
		scriptStart = html.find('<script type="text/javascript"')
		if scriptStart == -1:
			scriptStart = html.find('<script>')

		scriptEnd = -1
		if scriptStart == -1:
			break
		else:
			scriptEnd = html.find('</script>', scriptStart)
			if scriptEnd != -1:
				html = html[:scriptStart] + html[scriptEnd+len('</script>'):]
			else:
				break
	#排除注释
	while True:
		commentStart = html.find('<!--')
		commentEnd = -1
		if commentStart == -1:
			break
		else:
			commentEnd = html.find('-->', commentStart)
			if commentEnd != -1:
				html = html[:commentStart] + html[commentEnd+len('-->'):]
			else:
				break


	"""按div进行结果分割"""
	secList = []
	pos = 0
	findPos = 2
	lv = 0
	while True:
		tabPos = html.find("div", findPos)
		if tabPos==-1:
			break
		tableStart = html[tabPos-1:tabPos+3].lower() == "<div"
		tableEnd = html[tabPos-2:tabPos+3].lower() == "</div"
		if tableStart:
			#是一个table开始
			if lv == 0:
				#是顶级table开始，记录之前的段落
				secList.append(html[pos:tabPos-1])
				pos = tabPos-1
			lv += 1
		if tableEnd:
			#一个table结束
			lv -= 1
			#if lv <= 0: #因为广告的加入，通过top div分段的结果不好了，目前将分段尽可能细化，在之后通过特定tag辨别加入列表
			#顶级table结束，记录之前的段落
			secList.append(html[pos:tabPos+4])
			lv = 0
			pos = tabPos-2
			#end if
		findPos = tabPos+3
	#记录最后一个段落
	secList.append(html[pos:])
	return secList


def splitByTopTable(html):

	#排除javascript，因为其中有可能有导致分段中止的tag
	while True:
		scriptStart = html.find('<script type="text/javascript">')
		if scriptStart == -1:
			scriptStart = html.find('<script>')

		scriptEnd = -1
		if scriptStart == -1:
			break
		else:
			scriptEnd = html.find('</script>', scriptStart)
			if scriptEnd != -1:
				html = html[:scriptStart] + html[scriptEnd+len('</script>'):]
			else:
				break

	#排除注释
	while True:
		commentStart = html.find('<!--')
		commentEnd = -1
		if commentStart == -1:
			break
		else:
			commentEnd = html.find('-->', commentStart)
			if commentEnd != -1:
				html = html[:commentStart] + html[commentEnd+len('-->'):]
			else:
				break

	#按照顶级Table将html分段
	secList = []
	pos = 0
	findPos = 2
	lv = 0
	while True:
		tabPos1 = html.find("table", findPos)
		tabPos2 = html.find("TABLE", findPos)
		tabPos = -1
		if tabPos1>0 and (tabPos1<tabPos2 or tabPos2<0):
			tabPos = tabPos1
		if tabPos2>0 and (tabPos2<tabPos1 or tabPos1<0):
			tabPos = tabPos2
		if tabPos < 0:
			break
		tableStart = html[tabPos-1:tabPos+5].lower() == "<table"
		tableEnd = html[tabPos-2:tabPos+5].lower() == "</table"
		if tableStart:
			#是一个table开始

			if lv == 0:
				#是顶级table开始，记录之前的段落
				secList.append(html[pos:tabPos-1])
				pos = tabPos-1

			lv += 1
		if tableEnd:
			#一个table结束
			lv -= 1

			if lv <= 0: #去掉，因为百度的顶部导航会导致/table标签的缺失
			#顶级table结束，记录之前的段落
				secList.append(html[pos:tabPos+6])
				pos = tabPos+6
				lv = 0
			#end if

			#pos = tabPos-2
		findPos = tabPos+5
	#记录最后一个段落
	secList.append(html[pos:])
	return secList
def delJavascriptAndComment(html):
	#排除javascript，因为其中有可能有导致分段中止的tag
	while True:
		scriptStart = html.find('<script type="text/javascript">')
		if scriptStart == -1:
			scriptStart = html.find('<script')

		scriptEnd = -1
		if scriptStart == -1:
			break
		else:
			scriptEnd = html.find('</script>', scriptStart)
			if scriptEnd != -1:
				html = html[:scriptStart] + html[scriptEnd+len('</script>'):]
			else:
				break

	#排除注释
	while True:
		commentStart = html.find('<!--')
		commentEnd = -1
		if commentStart == -1:
			break
		else:
			commentEnd = html.find('-->', commentStart)
			if commentEnd != -1:
				html = html[:commentStart] + html[commentEnd+len('-->'):]
			else:
				break
	return html

def drawDivAndTable(html):
	#排除javascript，因为其中有可能有导致分段中止的tag
	'''while True:
		scriptStart = html.find('<script type="text/javascript">')
		if scriptStart == -1:
			scriptStart = html.find('<script')

		scriptEnd = -1
		if scriptStart == -1:
			break
		else:
			scriptEnd = html.find('</script>', scriptStart)
			if scriptEnd != -1:
				html = html[:scriptStart] + html[scriptEnd+len('</script>'):]
			else:
				break'''

	#排除注释
	'''while True:
		commentStart = html.find('<!--')
		commentEnd = -1
		if commentStart == -1:
			break
		else:
			commentEnd = html.find('-->', commentStart)
			if commentEnd != -1:
				html = html[:commentStart] + html[commentEnd+len('-->'):]
			else:
				break'''

	#按照顶级Table将html分段
	secList = []
	posDiv = -1
	posTable = -1
	posCur = 0
	fDiv = False
	fTable = False
	numDiv = 0
	numTable = 0
	tableStart = 0
	divStart = 0

	while True:
		if not fDiv and not fTable:
			posDiv = html.find('div', posCur)
			posTable = html.find('table', posCur)
			if posDiv != -1 and posTable != -1:
				if posDiv < posTable:
					fDiv = True
					posCur = posDiv
				else:
					fTable = True
					posCur = posTable
			elif posDiv != -1:
				fDiv = True
				posCur = posDiv
			elif posTable != -1:
				fTable = True
				posCur = posTable
			else:
				break
		elif fDiv:
		       posCur = html.find('div', posCur)
		       if posCur == -1:
			       break
		elif fTable:
		       posCur = html.find('table', posCur)
		       if posCur == -1:
			       break
		#print posCur
		#print html[posCur:posCur+100]
		if fDiv:
			if html[posCur-1:posCur+3] == '<div':
				if numDiv == 0:
					divStart = posCur-1
				numDiv += 1
			elif html[posCur-2:posCur+3] == '</div':
				numDiv -= 1
				if numDiv <= 0:
					secList.append(html[divStart:posCur+4])
					fDiv = False
					#print html[divStart:posCur+4]
			posCur += 3
		if fTable:
			if html[posCur-1:posCur+5] == '<table':
				if numTable == 0:
					tableStart = posCur-1
				numTable += 1
			elif html[posCur-2:posCur+5] == '</table':
				numTable -= 1
				if numTable <= 0:
					secList.append(html[tableStart:posCur+6])
					fTable = False
					#print html[tableStart:posCur+6]
			posCur += 5
	return secList

def splitSectionByTag(html, beginTag, endTag):
	secList = []
	pos = 0
	while True:
		sec = parseSubString(html, pos, beginTag, endTag)
		if sec == None:
			break
		else:
			secList.append(sec)
			pos = html.find(sec,pos) +len(sec) +len(endTag)
	return secList

#------------------------------------------------------------

def splitByTopli(content):
	#按照顶级li将content分段
	secList = []
	pos = 0
	beginSearchPos = 2
	lv = 0
	while True:
		startPos = content.find("li", beginSearchPos)
		if startPos==-1:
			#没有找到
			break

		liStart = (content[startPos-1:startPos+3].lower() == "<li " or content[startPos-1:startPos+3].lower() == "<li>")
		liEnd = content[startPos-2:startPos+3].lower() == "</li>"
		if liStart:
			#是一个table开始
			if lv == 0:
				#是顶级table开始，记录之前的段落
				secList.append(content[pos:startPos-1])
				pos = startPos-1
			lv += 1
		if liEnd:
			#一个table结束
			lv -= 1
			if lv <= 0:
				#顶级table结束，记录之前的段落
				secList.append(content[pos:startPos+3])
				lv = 0
				pos = startPos+3
		beginSearchPos = startPos+3
	#记录最后一个段落
	secList.append(content[pos:])
	return secList
