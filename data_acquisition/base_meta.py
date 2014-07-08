import BeautifulSoup
import csv
import re
import mediacloud

MEDIA_DICT = {
    '1' : NYTimesMeta(),
    '2' : WashingtonPostMeta(),
    '1150' : WSJMeta(),
    '6' : LATimesMeta(),
    '1757' : SalonMeta(),
    '314' : HuffPoMeta()
    #Yale
    #Columbia
}

class BaseMeta():
    
    byline_tags = []
    section_tags = []
    
    def __init__(self, byline_tags=None, section_tags=None):
        if byline_tags:
            self.byline_tags = byline_tags
        if section_tags:
            self.section_tags = section_tags
    
    def get_byline(self, soup):
        bylines = []
        for t in self.byline_tags:
            if soup.find(t[0],{t[1],t[2]}) is not None:
                if t[0]=='meta':
                    bylines.append(soup.find(t[0], {t[1]:t[2]})['content'])
                else:
                    bylines.append(soup.find(t[0], {t[1]:t[2]}).text)
                return bylines
        return bylines

    def get_section(self, soup):
        sections = []
        for t in self.section_tags:
            if soup.find(t[0],{t[1],t[2]}) is not None:
                if t[0]=='meta':
                    sections.append(soup.find(t[0], {t[1]:t[2]})['content'])
                else:
                    sections.append(soup.find(t[0], {t[1]:t[2]}).text)
                return sections
        return sections

class NYTimesMeta(BaseMeta):

    byline_tags = [['meta','name','author'],['span','class','byline-author'],['meta','name','clmst']]
    section_tags = [['meta','name',re.compile('cg',re.I)]]

class WashingtonPostMeta(BaseMeta):

    byline_tags = [['span', 'class', 'blog-byline'], ['meta', 'name', re.compile('dc.creator',re.I)]]
    section_tags = [['meta', 'name', 'section']]

class WSJMeta(BaseMeta):
    
    byline_tags = [['meta', 'name', 'author']]
    section_tags = [['meta', 'name', 'article.section']]

class LATimesMeta(BaseMeta):

    byline_tags = [['span', 'class', 'byline'], ['div','class','trb-bylines'], ['address','class','trb_columnistInfo_columnistPortrait'], ['meta', 'name', 'author'],['div','id','mod-article-byline']]
    section_tags = [['meta', 'name', 'article.section']]

class SalonMeta(BaseMeta):

    byline_tags = [['span','class','byline']]

class HuffPoMeta(BaseMeta):
    
    byline_tags = [['meta', 'name', 'author']]

class YaleMeta(BaseMeta):
    
    byline_tags = [[]]

class ColumbiaMeta(BaseMeta):
    
    byline_tags = [[]]
