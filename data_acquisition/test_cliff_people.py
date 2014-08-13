#TODO: words written by men and women

import csv
import numpy as np
import matplotlib.pyplot as plt
import pylab as P
import os
import sys
import cliff

lines = []

#CHOOSE A FOLDER FROM ABOVE
#folder = "./test_results/30bf9fd5bb824eb49e89c8a828276348c0b1570c/"
folder = "./annual_data/"

files = ["[2013-08-01T00:00:00Z TO 2013-09-01T00:00:00Z].csv",
"[2013-09-01T00:00:00Z TO 2013-10-01T00:00:00Z].csv",
"[2013-10-01T00:00:00Z TO 2013-11-01T00:00:00Z].csv",
"[2013-11-01T00:00:00Z TO 2013-12-01T00:00:00Z].csv",
"[2013-12-01T00:00:00Z TO 2014-01-01T00:00:00Z].csv",
"[2014-01-01T00:00:00Z TO 2014-02-01T00:00:00Z].csv",
"[2014-02-01T00:00:00Z TO 2014-03-01T00:00:00Z].csv",
"[2014-03-01T00:00:00Z TO 2014-04-01T00:00:00Z].csv",
"[2014-04-01T00:00:00Z TO 2014-05-01T00:00:00Z].csv",
"[2014-05-01T00:00:00Z TO 2014-06-01T00:00:00Z].csv",
"[2014-06-01T00:00:00Z TO 2014-07-01T00:00:00Z].csv",
"[2014-07-01T00:00:00Z TO 2014-08-01T00:00:00Z].csv"]

top = 0
for filename in files:
    #with open (os.path.join(folder,"month_06_2014.csv")) as f:
    with open (os.path.join(folder,files)) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            lines.append(row)
    lines.pop(top)
    top = len(lines)

print lines[0].keys()

import requests
import json

#SUMMARIZE SECTION IDENTIFICATION
MEDIA= {
  '1': "new york times",
  '2': "washington post",
  '6':"la times",
  '7': "new york post",
  '1150': "wall street journal",
  '1757': "salon",
  '1707': "daily beast",
  '1750': "telegraph",
  '314' : "huffington post",
"27502":"huffington post" #assuming these are the same for now
}

media = {}

for line in lines:
    mediakey = MEDIA[line['media_id']]
    section = line['section']
    if(not mediakey in media):
        media[mediakey] = {}
    if(not section in media[mediakey]):
        media[mediakey][section] = 0
    media[mediakey][section] += 1
        
        
for key in media.keys():
    articles = 0
    for section in media[key].keys():
        articles += media[key][section]
    print "{0}: {1} sections, {2} articles".format(key,len(media[key]),articles)
    for section in media[key].keys():
        if(section.lower().find("opinion")>=0):
            print "    {0}: {1}".format(section,media[key][section])

# GROUP BYLINES BY MEDIA ORGANISATION
# AND SUMMARIZE
media_people = {}
mentioned_people = {}

from byline_gender import BylineGender
import time
b = BylineGender()
        
sections = []
for line in lines:
    if(line['section'].lower().find("opinion")>=0):
        section = line['section']
        mediakey = MEDIA[line['media_id']]
        byline_text = line['byline']    
        sys.stdout.write('.')

        byline_names = b.get_full_names(byline_text)
        for person in cliff.people(line['extractor.full_text']):
          if(not mediakey in mentioned_people.keys()):
            mentioned_people[mediakey] = {}

          name = person['name']
          if(not name in mentioned_people.keys()):
            mentioned_people[mediakey][name] = {'count':0,'mentioners':{}}
            mentioned_people[mediakey][name]['gender'] = b.single_name_gender_ascii(name)
          mentioned_people[mediakey][name]['count'] += person['count']
          for byline in byline_names:
            if not byline in mentioned_people[mediakey][name]['mentioners'].keys():
              mentioned_people[mediakey][name]['mentioners'][byline] = 0
            mentioned_people[mediakey][name]['mentioners'][byline] += person['count']
       
        for byline in byline_names:
            if(not mediakey in media_people.keys()):
                media_people[mediakey] = {}
            if(not byline in media_people[mediakey].keys()):
                media_people[mediakey][byline] = 0
            media_people[mediakey][byline] += 1
            
print "---"
print sections
for key in media_people.keys():
    print "{0}: {1} bylines".format(key,len(media_people[key]))

import pdb;pdb.set_trace()

print "COMPLETE"
