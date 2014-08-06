import mediacloud
import yaml
import base_meta
import csv
from byline_gender import BylineGender
import time 
import sys

def extract_metadata(extractor, url=None, file_name=None, stories_id=None, import_full_text=False):
    extractor.make_soup(url=url,file_name=file_name,stories_id=stories_id,import_full_text=import_full_text)
    byline = extractor.get_byline()
    section = extractor.get_section()
    is_opinion = extractor.is_opinion()
    return byline, section, is_opinion

start_time = time.time()
gender_detector = BylineGender()

MEDIA_BASEMETA_DICTIONARY = {
  '1' : base_meta.NYTimesMeta(),
  '2' : base_meta.WashingtonPostMeta(),
  '6' : base_meta.LATimesMeta(),
    '7' : base_meta.NYPostMeta(),
  '1150' : base_meta.WSJMeta(),
  '1757' : base_meta.SalonMeta(),
  '27502' : base_meta.HuffPoMeta(),
  '314' : base_meta.HuffPoMeta()
}


api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
print api_key
mc = mediacloud.api.MediaCloud(api_key)

ranges = ['[2013-08-01T00:00:00Z TO 2013-09-01T00:00:00Z]', '[2013-09-01T00:00:00Z TO 2013-10-01T00:00:00Z]', '[2013-10-01T00:00:00Z TO 2013-11-01T00:00:00Z]', '[2013-11-01T00:00:00Z TO 2013-12-01T00:00:00Z]', '[2013-12-01T00:00:00Z TO 2014-01-01T00:00:00Z]', '[2014-01-01T00:00:00Z TO 2014-02-01T00:00:00Z]', '[2014-02-01T00:00:00Z TO 2014-03-01T00:00:00Z]', '[2014-03-01T00:00:00Z TO 2014-04-01T00:00:00Z]', '[2014-04-01T00:00:00Z TO 2014-05-01T00:00:00Z]', '[2014-05-01T00:00:00Z TO 2014-06-01T00:00:00Z]', '[2014-06-01T00:00:00Z TO 2014-07-01T00:00:00Z]', '[2014-07-01T00:00:00Z TO 2014-08-01T00:00:00Z]']

x = ranges[int(sys.argv[1])]
star = 0
results = csv.writer(open('./'+x+'.csv','wb'),delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
results.writerow(['media_id']+['stories_id']+['publish_date']+['url']+['byline']+["byline_gender['female']"] + ["byline_gender['male']"] + ["byline_gender['unknown']"]+["section"]+ ['is_opinion'] + ['extractor.full_text'])
query = '+publish_date:'+x+' AND +media_id:('+' OR '.join(MEDIA_BASEMETA_DICTIONARY.keys())+')'
res = mc.sentenceList('sentence_number:1', query, start=star, rows=1)
numFound = res[u'response'][u'numFound']
print "Numfound: {0}".format(numFound)
while star < numFound:
    res = mc.sentenceList('sentence_number:1', query, start=star, rows=500)
    for s in res[u'response'][u'docs']:
        if str(s[u'media_id']) in MEDIA_BASEMETA_DICTIONARY:
            extractor = MEDIA_BASEMETA_DICTIONARY[str(s[u'media_id'])]
        else:
            sys.stdout.write("b")
            sys.stdout.flush()
            extractor = base_meta.BaseMeta()
        try:
            byline_download, section_download, is_opinion = extract_metadata(extractor, stories_id=s[u'stories_id'], url=s[u'url'], import_full_text=True)
            byline_gender = gender_detector.byline_gender(byline_download)
            result_row = [s[u'media_id']]+[s[u'stories_id']]+[s[u'publish_date']]+[s[u'url']]+[byline_download]+[byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']]+[section_download]+ [is_opinion] + [extractor.full_text]
            results.writerow([unicode(s).encode("utf-8") for s in result_row])
            sys.stdout.write('.')
            sys.stdout.flush()
        except Exception as e:
            try:
                sys.stdout.write('f')
                result_row = [s[u'media_id']]+[s[u'stories_id']]+[s[u'publish_date']]+[s[u'url']]
                results.writerow([unicode(s).encode("utf-8") for s in result_row])
            except Exception as e:
                sys.stdout.write('x')
                sys.stdout.flush()
                pass
            pass
    star += 500
