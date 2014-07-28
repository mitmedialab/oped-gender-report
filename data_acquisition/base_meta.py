#TO-DO: Switch to lxml to process js
#	   Factor out some byline parsing (e.g. removing 'by')

import csv
import re
try:
	import mediacloud
except:
	pass
from bs4 import BeautifulSoup #using BeautifulSoup to make dealing with regex simpler
import urllib2
import sys
import lxml.etree
import json
import pdb
import yaml
import ml_stripper
import nltk
import string

class BaseMeta():

	url_name = ""
	soup = BeautifulSoup("")

	def __init__(self, url_name=None, soup=None):
		if url_name:
			self.url = url_name
		if soup:
			self.soup = soup

	def token_string(self,text):
		#strip punctuation
		exclude = set(string.punctuation)
		return ' '.join(word for word in nltk.word_tokenize(text) if word not in exclude)

	full_text = None
	def make_soup(self, stories_id=None, url=None, file_name=None, url_name=None, import_full_text=False):
		self.url = ""
		html = None
		self.soup = BeautifulSoup("")

		if url_name:
			self.url = url_name

    # if there is a story ID, look up the story on MediaCloud and download it all
		if stories_id:
			api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
			mc = mediacloud.api.MediaCloud(api_key)
			story = mc.story(stories_id,raw_1st_download=1)
			if import_full_text:
				self.full_text = self.token_string(story[u'story_text'])
				#print "FULLTEXT ACTIVE"
			if not url_name:
				try:
					self.url = story[u'url']
					self.soup = BeautifulSoup(story[u'raw_first_download_file'])
				except Exception as e:
					pass
    # if we're fetching the page from a url
		elif url:
			if not url_name:
				self.url = url
      #download the url
			html = urllib2.urlopen(url).read()
      #load the full html into soup
			self.soup = BeautifulSoup(html)
		elif file_name:
			if not url_name:
				self.url = file_name
      #load the html for this page
			html = open(file_name,'r').read()
			self.soup = BeautifulSoup(html)

    # if the HTML has been loaded and the import fulltext option is set
    # set the full_text variable with a stripped version of html
		if import_full_text and self.full_text is None and html is not None:
				self.full_text = self.token_string(ml_stripper.strip_tags(html))

	byline_tags = []
	def get_byline(self, byline_tags=None):
		bylines = []
		if byline_tags:
			self.byline_tags = byline_tags
		for tag_set in self.byline_tags:
			found = self.soup.select(tag_set[0])
			if found:
				preparsed = found[0].text.encode('utf8') if tag_set[1] == 0 else found[0][tag_set[1]].encode('utf8')
				match = re.match(tag_set[2], preparsed) if len(tag_set) > 2 else None
				postparsed = match.group('byline').strip() if match else preparsed
				match2 = re.match(r'(BY|By|by){1}[\s]+(?P<byline>[A-Za-z\.\- ]+)[\s\S]*', postparsed)
				return match2.group('byline').strip() if match2 else postparsed.strip()
		return ''

	url_section_patterns = []	
	section_tags = []
	def get_section(self, url_section_patterns=None, section_tags=None): ##currently acts as get_opinio
		if url_section_patterns:
			self.url_section_patterns = url_section_patterns
		if section_tags:
			self.section_tags = section_tags
		for reg in self.url_section_patterns:
			match = re.match(reg,self.url)
			if match:
				return (reg, match.group('section'))
		for tag_set in self.section_tags:
			found = self.soup.select(tag_set[0])
			if found:
				preparsed = found[0].text.encode('utf8') if tag_set[1] == 0 else found[0][tag_set[1]].encode('utf8')
				match = re.match(tag_set[2], preparsed) if len(tag_set) > 2 else None
				return match.group('section') if match else preparsed
		return ''

	opinion_sections = []
	def is_opinion(self, opinion_sections=None):
		section = self.get_section()
		if len(self.opinion_sections) and len(section) > 0: 
		  return self.get_section()[0].lower() in self.opinion_sections
		else:
		  return None

class NYTimesMeta(BaseMeta):

	byline_tags = [['meta[name="author"]','content'],['span[class="byline-author"]',0],['meta[name="clmst"]','content'],['meta[name="byl"]','content',r'By (?P<byline>[A-Za-z\.\- ]*)'],['meta[name="CLMST"]','content',r'By[\s]+(?P<byline>[A-Za-z\.\- ]*)'],['p[class="byline"]',0],['h6[class="byline"]',0,r'By[\s]+(?P<byline>[A-Za-z\.\- ]*)']]
		
	url_section_patterns = [r'http://www.nytimes.com/[0-9]{4}/[0-9]{2}/[0-9]{2}/(?P<section>[A-Za-z0-9/]+)/']
	section_tags = [['meta[name="cg"]','content'],['meta[name="CG"]','content']]
		
	opinion_sections = ['opinion']
		

class WashingtonPostMeta(BaseMeta):

	byline_tags = [['meta[name="authors"]','content'],['meta[name="dc.creator"]','content'],['meta[name="DC.creator"]','content'],['span[class="blog-byline"]',0],['div[id="byline"]',0],['p[class="posted"]',0],['span[class="pb-byline"]',0]]
	
	url_section_patterns = [r'http://feeds.washingtonpost.com/c/34656/f/[0-9]+/s/[A-Za-z0-9]+/(sc/[0-9]+/l|l)/0L0Swashingtonpost0N0C(?P<section>[A-Za-z0-9]+?)s0C[A-Za-z0-9]+/story01.htm',r'http://www.washingtonpost.com/wp-dyn/content/article/[0-9]{4}/[0-9]{2}/[0-9]{2}/AR[0-9]+.html?(nav|wprss)=rss_(?P<section>[A-Za-z0-9]+)(/columns$|/industries$|s$|$)']
	section_tags = [['meta[name="section"]','content']]

	opinion_sections = ['opinion','blog']


class WSJMeta(BaseMeta):
	
	byline_tags = [['meta[name="article.author"]','content'],['meta[name="author"]','content'],['h3[class="byline"]',0],['span[id="byline"]',0],['p[id="byline"] a[href^="http://www.marketwatch.com/Journalists/"]',0],['p[class="emphasis"] span[class="credit"]',0]]
	
	section_tags = [['meta[name="article.section"]','content']]


class LATimesMeta(BaseMeta):

	byline_tags = [['span[class="byline"]',0],['div[class="trb-bylines"]',0],['address[class="trb_columnistInfo_columnistPortrait"]',0],['div[id="mod-article-byline"]',0,r'((January|February|March|April|June|July|August|September|October|November|December)( \d\d?, \d\d\d\d\|)(By )?)(?P<byline>[A-Z]{1}[A-Za-z. -]+)($|, Los Angeles Times)'],['div[class="byline"]',0],['span[class="byline"]',0],['meta[name="author"]','content']]
	
	url_section_patterns = [r'http://feeds.latimes.com/~r/(latimes/)*(?P<section>[A-Za-z/]+)/~3']
	section_tags = [['meta[name="article.section"]','content']]

	opinion_sections = ['news/opinion','OpinionLa']


class HuffPoMeta(BaseMeta):

	byline_tags = [['a[rel="author"]',0],['meta[name="author"]','content']]
	#def get_byline(self):
	#	return BaseMeta.get_byline(self).split(' and ')


class SalonMeta(BaseMeta):
		
	byline_tags = [['div[class="articleInner"] span[class="byline"]',0,r'By[\s]+(?P<byline>[A-Za-z\.\- ]*)'],['a[rel="author"]',0]]


class DailyBeastMeta(BaseMeta):

	byline_tags = [['meta[name="authors"]','content'],['a[class="more-by-author"]',0],['div[class="author1"]',0]]

	url_section_patterns = [r'http://(www.thedailybeast.com/|feedproxy.google.com/~r/thedailybeast/)(?P<section>[A-Za-z\-]+)/[\S]*']
		

class YaleMeta(BaseMeta):

	byline_tags = [['div[class="entry-authors"]',0]]


class PrincetonMeta(BaseMeta):

	byline_tags = [['p[class="byline"]',0]]


class ColumbiaMeta(BaseMeta):

	byline_tags = [['div[class="article-authors"]',0]]
