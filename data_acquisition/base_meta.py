import csv
import re
import mediacloud
import BeautifulSoup #using BeautifulSoup to make dealing with regex simpler
import urllib2
import sys
import lxml.etree
import json

class BaseMeta():

	url = ""
	soup = BeautifulSoup.BeautifulSoup("")

	def __init__(self, url=None, soup=None):
		if url:
			self.url = url
		if soup:
                	self.soup = soup

	def make_soup(self, stories_id=None, url=None, file_name=None):
		self.url = ""
		self.soup = BeautifulSoup.BeautifulSoup("")
		if stories_id:
			api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
			mc = mediacloud.api.MediaCloud(api_key)
			story = mc.story(stories_id,raw_1st_download=1)
                        try:
                                self.url = story[u'url']
                                self.soup = BeautifulSoup.BeautifulSoup(story[u'raw_first_download_file'])
                        except Exception as e:
                                pass
		elif url:
			self.url = url
			self.soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(url).read())
		elif file_name:
			self.url = file_name
			self.soup = BeautifulSoup.BeautifulSoup(open(file_name,'r').read())
                        
	byline_tags = []
        byline_javascript = []
	def get_byline(self, byline_tags=None):
		if byline_tags:
			self.byline_tags = byline_tags
		for t in self.byline_tags:
			if self.soup.find(t[0],{t[1]:t[2]}) is not None:
				if t[0]=='meta':
					return self.soup.find(t[0], {t[1]:t[2]})['content']
				else:
					return self.soup.find(t[0], {t[1]:t[2]}).text
		return ''

	url_section_patterns = []	
	section_tags = []
	def get_section(self, url_section_patterns=None, section_tags=None): ##currently acts as get_opinio
		if url_section_patterns:
			self.url_section_patterns = url_section_patterns
		if section_tags:
			self.section_tags = section_tags
		for reg in self.url_section_patterns:
			if re.match(reg,self.url):
				return re.match(reg,self.url).group('section')
		for tag in self.section_tags:
			if self.soup.find(tag[0],{tag[1]:tag[2]}) is not None:
				if tag[0]=='meta':
					return self.soup.find(tag[0], {tag[1]:tag[2]})['content']
				else:
					return self.soup.find(tag[0], {tag[1]:tag[2]}).text
                return ''

	opinion_sections = []
	def is_opinion(self, opinion_sections=None):
		if opinion_sections:
			self.opinion_sections = opinion_sections
		return get_section().lower() in opinion_sections
                       

class NYTimesMeta(BaseMeta):

	byline_tags = [['meta','name','author'],['span','class','byline-author'],['meta','name','clmst'],['meta','name','byl'],['h6','class','byline'],['meta','name','CLMST'],['p','class','byline']]
        
	url_section_patterns = [r'http://www.nytimes.com/[0-9]{4}/[0-9]{2}/[0-9]{2}/(?P<section>[A-Za-z0-9/]+)/']
	section_tags = [['meta','name',re.compile('cg',re.I)]]
        
	opinion_sections = ['opinion']
        

class WashingtonPostMeta(BaseMeta):

	byline_tags = [['meta','name','authors'],['span', 'class', 'blog-byline'], ['meta', 'name', 'dc.creator'],['meta','name','DC.creator'],['div','id','byline'],['p','class','posted'],['span','class','pb-byline']]
        def get_byline(self):
                return self.parse_byline(BaseMeta.get_byline(self))
        byline_patterns = [r'\|{1}(\s+)?(?P<byline>[A-Za-z. -]+)']
        def parse_byline(self, byline):
                for reg in self.byline_patterns:
                        if re.match(reg, byline):
                                return re.match(reg, byline).group('byline')
                return byline

	url_section_patterns = [r'http://feeds.washingtonpost.com/c/34656/f/[0-9]+/s/[A-Za-z0-9]+/(sc/[0-9]+/l|l)/0L0Swashingtonpost0N0C(?P<section>[A-Za-z0-9]+?)s0C[A-Za-z0-9]+/story01.htm',r'http://www.washingtonpost.com/wp-dyn/content/article/[0-9]{4}/[0-9]{2}/[0-9]{2}/AR[0-9]+.html?(nav|wprss)=rss_(?P<section>[A-Za-z0-9]+)(/columns$|/industries$|s$|$)']
	section_tags = [['meta', 'name', 'section']]

	opinion_sections = ['opinion','blog']


class WSJMeta(BaseMeta):
    
	byline_tags = [['meta','name','article.author'],['meta', 'name', 'author'],['h3','class','byline'],['span','id','byline']]
	
	section_tags = [['meta', 'name', 'article.section']]


class LATimesMeta(BaseMeta):

	byline_tags = [['span', 'class', 'byline'], ['div','class','trb-bylines'], ['address','class','trb_columnistInfo_columnistPortrait'], ['meta', 'name', 'author'],['div','id','mod-article-byline']]
        def get_byline(self):
                byline = BaseMeta.get_byline(self)
#                if byline == '':
 #                       if self.soup.find('p', text=re.compile(r'(&#0160;){0,1}--( )?[A-Za-z\. \-]+(&#0160;){0,1}')) is not None:
                                #byline = re.match(r'(&#0160;){0,1}--( )?(?P<byline>[A-Za-z\. \-]+)(&#0160;){0,1}',self.soup.find('p', text=re.compile(r'(&#0160;){0,1}--( )?[A-Za-z\. \-]+(&#0160;){0,1}'))).group('byline')
                return self.parse_byline(byline)
        byline_patterns = [r'((January|February|March|April|June|July|August|September|October|November|December)( \d\d?, \d\d\d\d\|)(By )?)(?P<byline>[A-Z]{1}[A-Za-z. -]+)($|, Los Angeles Times)']
        def parse_byline(self, byline):
                for reg in self.byline_patterns:
                        if re.match(reg, byline):
                                return re.match(reg, byline).group('byline')
                return byline
    
	url_section_patterns = [r'http://feeds.latimes.com/~r/(latimes/)*(?P<section>[A-Za-z/]+)/~3']
	section_tags = [['meta', 'name', 'article.section']]

	opinion_sections = ['news/opinion','OpinionLa']


class HuffPoMeta(BaseMeta):

	byline_tags = [['meta','name','author']]
	#def get_byline(self):
	#	return BaseMeta.get_byline(self).split(' and ')


class SalonMeta(BaseMeta):
        
	byline_tags = [['span','class','byline'],['a','rel','author']]


class DailyBeastMeta(BaseMeta):

	byline_tags = [['meta','name','authors'],['a','class','more-by-author'],['div','class','author1']]

        url_section_patterns = [r'http://(www.thedailybeast.com/|feedproxy.google.com/~r/thedailybeast/)(?P<section>[A-Za-z-]+)/(~3|item)/']
        

class YaleMeta(BaseMeta):

	byline_tags = [['div','class','entry-authors']]


class PrincetonMeta(BaseMeta):

	byline_tags = [['p','class','byline']]


class ColumbiaMeta(BaseMeta):

	byline_tags = [['div','class','article-authors']]
