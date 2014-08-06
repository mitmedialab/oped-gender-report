from gender_detector import GenderDetector
import nltk
import re
import requests
import StringIO
import csv
import string

class BylineGender():
  def __init__(self):
    self.detector = GenderDetector('us')
    self.load_name_org_online()

  def byline_gender(self,byline):
    gender_result = {"female":0, "male":0,"unknown":0}
    for name in self.get_first_names(byline):
      if(name is None):
        gender_result["unknown"] += 1
      else:
        gender_result[str(self.detector.guess(name))] += 1
    return gender_result

  def single_name_gender(self,name):
    if(name is None or len(name.strip()) == 0):
      return "unknown" 
    n = self.get_first_names(name.strip())
    if len(n) > 0 and n[0] is not None:
      return self.detector.guess(n[0])
    return "unknown"

  # needs error handling
  def load_name_org_online(self):
    self.online_names = {}
    url="https://docs.google.com/spreadsheets/d/11R_pj7n2lhVNfVohyp-_aNxucSsMYCwixLTGp-u-9eQ/export?format=csv"
    try:
      response = requests.get(url)
      csv_string = response.content
      f = StringIO.StringIO(csv_string)
      eval_base = csv.reader(f, delimiter=',')
      eval_base.next()
      for row in eval_base:
        org = row[0]
        name = re.sub(r'\+', " ", row[1])
        gender = row[3]
        if(not org in self.online_names.keys()):
          self.online_names[org]= {}
        if gender in ['male','female','unknown','ignore']:
          self.online_names[org][name] = gender
          print "{0},{1},{2}".format(org,name,gender)
    except:
      print "download unsuccessful"
        
  def org_name_gender(self,org,name):
    manual_gender=None
    exclude = set(string.punctuation)
    name = ''.join(ch for ch in name if ch not in exclude)
    if org in self.online_names.keys():
      if name in self.online_names[org].keys():
        manual_gender = self.online_names[org][name]
    if manual_gender in ['male','female','unknown','ignore']:
      return manual_gender
    return self.single_name_gender(name)


  def strip_extras(self, byline):
    byline = re.sub(r'general sir ','',byline)
    byline = re.sub(r'american way: ','',byline)
    byline = re.sub(r'president','',byline)
    byline = re.sub(r'sir','',byline)
    byline = re.sub(r'gov(\.)?','',byline)
    byline = re.sub(r'rep(\.)?','',byline)
    byline = re.sub(r'prof','',byline)
    byline = re.sub(r'professor','',byline)
    byline = re.sub(r'.*?rt rev(d)?','',byline)
    byline = re.sub(r'\n.*','',byline)
    #telegraph cleaning
    #byline = re.sub(r'london-based.*','',byline)
    #byline = re.sub(r'london researcher.*','',byline)
    #byline = re.sub(r' of the.*','',byline)
    #byline = re.sub(r'telegraph tv critic','',byline)
    #byline = re.sub(r'broadcaster','',byline)
    #byline = re.sub(r'interview: ','',byline)
    #byline = re.sub(r'commentary: ','',byline)
    #byline = re.sub(r'telegraph travel writer','',byline)
    #byline = re.sub(r'on gigolo','',byline)
    byline = re.sub(r'more stories by ','',byline)
    byline = re.sub(r'view author.*','',byline)
    byline = re.sub(r'founder of.*','',byline)
    byline = re.sub(r' is (a)?.*','',byline)
    byline = re.sub(r' covers.*','',byline)
    byline = re.sub(r' in .*','',byline)
    byline = re.sub(r' info.*','',byline)
    byline = re.sub(r' writes .*','',byline)
    byline = re.sub(r'graphic(s)? by(:)?','',byline)
    byline = re.sub(r'compiled ','',byline)
    byline = re.sub(r'exclusive ','',byline)
    byline = re.sub(r'special dispatch' ,'',byline)
    byline = re.sub(r'as told to ','',byline)
    byline = re.sub(r' for .*','',byline)
    byline = re.sub(r'  .*','',byline)
    byline = re.sub(r'interview(ed)?(s)? ','',byline)
    byline = re.sub(r' at.*','',byline)
    #cleaning Telegraph "by"
    byline = re.sub(r'^(by|By|BY) ','',byline)
    byline = re.sub(r'.*? by ','',byline)
    #remove multiple spaces in the middle of a name
    byline = re.sub(r'\s\s',' ',byline)
    byline = re.sub(r'\s\s',' ',byline)
    byline = re.sub(r'^dr ','',byline)
    byline = byline.strip().encode("utf-8")
    return byline

  # TODO: deal with commas
  def get_full_names(self, byline):
    if byline is None:
      return []
    byline = byline.strip().lower()
    if byline is None or re.search('[0-9]',byline) is not None:
      return []
    spaces = byline.count(' ')
    commas = byline.count(',')
    conjunctions = byline.count(' and ')
    semicolons = byline.count(';')
    bylines_result = []
    if(semicolons > 0):
      for name in byline.split(";"):
        if(name.count(";") > 0 or name.count(",") > 0 or name.count(" and ") > 0):
          bylines_result = bylines_result + self.get_full_names(name)
        else:
          bylines_result.append(self.strip_extras(name.strip()))
    elif(conjunctions >0):
      for name in byline.split(' and '):
        if(name.count(";") > 0 or name.count(",") > 0 or name.count(" and ") > 0):
          bylines_result = bylines_result + self.get_full_names(name)
        else:
          bylines_result.append(self.strip_extras(name.strip()))
    elif(commas == 0 and conjunctions == 0 and semicolons == 0):
      bylines_result.append(self.strip_extras(byline))
    elif(spaces >=2 and commas >=1):
      for name in byline.split(','):
        if(name.count(";") > 0 or name.count(",") > 0 or name.count(" and ") > 0):
          bylines_result = bylines_result + self.get_full_names(name)
        else:
          bylines_result.append(self.strip_extras(name.strip()))

    for junk in ['','based']:
      if junk in bylines_result:
        bylines_result.remove(junk)

    return bylines_result

  def get_first_names(self, byline):
    if byline is None or re.search('[0-9]',byline) is not None:
      return []
    byline = byline.strip()
    spaces = byline.count(' ')
    commas = byline.count(',')
    conjunctions = byline.count(' and ')
    bylines_result = []
    if(commas == 0 and conjunctions == 0):
      bylines_result.append(self.get_first_name_from_fullname(byline))
    if(conjunctions >0):
      for name in byline.split(' and '):
        bylines_result.append(self.get_first_name_from_fullname(name.strip()))
    if(spaces < 3 and commas == 1):
      bylines_result.append(self.get_first_name_from_reversename(byline))
    return bylines_result

  # assumes there's a single comma
  def get_first_name_from_reversename(self, byline):
    split_byline = [x.strip() for x in byline.split(',')]
    # set offset to 0 since the surname has already been stripped
    return self.get_first_name_from_fullname(split_byline[1], 0)

  def get_first_name_from_fullname(self, byline, offset=None):
    if(offset == None):
      offset = -1
    tokens = nltk.word_tokenize(byline)
    first_name = ""
    for i in range(0, (len(tokens)+offset)):
      if(tokens[i].count(".") > 0 or len(tokens[i]) == 1):
        continue
      return tokens[i]
    return None

  def test_first_names(self):
    test_strings = [
      ["J. Nathan Matias", ["Nathan"]],
      ["J. Matias", [None]],
      ["J Matias", [None]],
      ["J N Matias", [None]],
      ["J. N. Matias", [None]],
      ["JN Matias", ["JN"]],
      ["Matias, J. Nathan",["Nathan"]],
      ["Mishkin, Pamela", ["Pamela"]],
      ["Pamela Mishkin", ["Pamela"]],
      ["Nathan Matias and Pamela Mishkin", ["Nathan", "Pamela"]],
      ["J. Nathan Matias and Pamela Mishkin", ["Nathan", "Pamela"]]
    ]
    for test_string in test_strings:
      names = self.get_first_names(test_string[0])
      print 'Got: [%s]' % ', '.join(map(str, names))
      print 'Expected: [%s]' % ', '.join(map(str, test_string[1]))
      print '--------'
