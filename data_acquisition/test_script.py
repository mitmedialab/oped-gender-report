#TO-DO: Switch to clearer argument structure, decide how to deal with case where there is no raw_first_download_file

import argparse
import base_meta
import mediacloud
import csv
from byline_gender import BylineGender
from evaluation_util import *
import StringIO
import requests
import re, sys, os

MEDIA_BASEMETA_DICTIONARY = {
  '1' : base_meta.NYTimesMeta(),
  '2' : base_meta.WashingtonPostMeta(),
  '6' : base_meta.LATimesMeta(),
  '1150' : base_meta.WSJMeta(),
  '1757' : base_meta.SalonMeta(),
  '1707' : base_meta.DailyBeastMeta(),
  '314' : base_meta.HuffPoMeta()
}

MEDIA_FILEPATH_DICTIONARY = {
  '1' : './test_sets/nytimes/',
  '2' : './test_sets/washingtonpost/',
  '6' : './test_sets/latimes/',
  '1707' : './test_sets/dailybeast/',
  '1757' : './test_sets/salon/',
  '314' : './test_sets/huffpo/',
  '1150' : './test_sets/wsj/'
}

DEFAULT_TEST_FILE = './test_sets/test_set_index.csv'

gender_detector = BylineGender()

def extract_metadata(extractor, url=None, file_name=None, stories_id=None):
  extractor.make_soup(url=url,file_name=file_name,stories_id=stories_id)
  return extractor.get_byline(), extractor.get_section(), extractor.is_opinion()

def __main__():

  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  group.add_argument('-f','--filename',action='store',help="Extract for stories listed in given file (assumes file is csv with fields for media_id, publish_date, stories_id, url, and file_name with path to file containing story's raw_first_download_file)")
  parser.add_argument('-t',)
  group.add_argument('-l','--large_test',action='store_true',help="Extract for all stories in test set")
  group.add_argument('-s','--small_test',action='store_true',help="Extract for stories in small test set")
  args = parser.parse_args()

  if args.filename:
    for m_id, path in MEDIA_FILEPATH_DICTIONARY:
      if re.match('^('+path+')',args.filename):
        extractor = MEDIA_BASEMETA_DICTIONARY[str(row['media_id'])]
    print extract_metadata(extractor, file_name=args.filename)

  elif args.large_test or args.small_test:
    #load identifiers for evaluation storage         
    eval_util = EvaluationUtil()
    # create evaluation folder if needed        
    eval_util.create_eval_dir()
    #create file for results in commit folder
    results = csv.writer(open(os.path.join(eval_util.eval_path, "extracted_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
    # create logfile to associate results with dates           
    with open(os.path.join(eval_util.results_path, "byline_extraction.log"), "a") as extraction_log:
      extraction_log.write("{0}: {1}\n".format(datetime.datetime.now().isoformat(), eval_util.commit_number))
    results.writerow(['media_id']+['stories_id']+['publish_date']+['byline'] + ['female_byline'] + ['male_byline'] + ['unknown_byline']+['section'] + ['is_opinion'])

    if args.large_test:
      URL = 'https://docs.google.com/spreadsheets/d/1WAkvfgW28HBETpoBFWdfkLtuVp1SM78bVTGbtzv7mUU/export?format=csv'
    elif args.small_test:
      URL = 'https://docs.google.com/spreadsheets/d/1WAkvfgW28HBETpoBFWdfkLtuVp1SM78bVTGbtzv7mUU/export?format=csv' ##REPLACE WITH SMALL TEST URL

    response = requests.get(URL)
    assert response.status_code == 200, 'Wrong status code'
    csv_string = response.content
    f = StringIO.StringIO(csv_string)
    eval_base = csv.reader(f, delimiter=',')
    eval_base.next()
    eval_base.next()

    eval_res = csv.writer(open(os.path.join(eval_util.eval_path, "evaluated_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
    eval_res.writerow(['media_id']+['stories_id']+['url']+['extracted byline']+['actual byline']+['Is extracted byline correct?']+["If there's extra text, what is it?"]+["If there's missing text, what is it?"]+['How many names did we extract?']+['How many names in actual byline on the page?'])
    for row in eval_base:
      if str(row[0]) in MEDIA_BASEMETA_DICTIONARY:
        extractor = MEDIA_BASEMETA_DICTIONARY[str(row[0])]
      else:
        extractor = base_meta.BaseMeta()
      byline_download, section_download, is_opinion = extract_metadata(extractor, file_name=(MEDIA_FILEPATH_DICTIONARY[str(row[0])]+str(row[1])+'.html'))
      byline_gender = gender_detector.byline_gender(byline_download)
      results.writerow([row[0]]+[row[1]]+[row[2]]+[byline_download]+ [byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']]+[section_download]+[is_opinion])
      if row[5].lower() == 'y':
        actual = row[4]
      else:
        actual = row[6]
      if byline_download.lower().strip() == actual.lower().strip():
        correct = 'y'
        extra_text = ''
        number = row[8]
        contains = ''
        missing = ''
      else:
        correct = 'n'
        pattern = '([\s\S]*)'+actual.strip().lower()+'([\s\S]*)'
        m = re.match(pattern,byline_download.strip().lower())
        if m:
          extra_text = m.group(1) + ';' + m.group(2)
          number = byline_gender['female']+byline_gender['male']+byline_gender['unknown']
          contains = 'y'
          missing = ''
        else:
          contains = 'n'
          extra_text = ''
          number = byline_gender['female']+byline_gender['male']+byline_gender['unknown']
          split_bl = actual.split(';;')
          split_bdload = byline_download.split(';;')
          missing = ''
          for s in split_bl:
            if not any(re.match(pattern, r.strip().lower()) for r in split_bdload):
              missing += s+';;;'
      eval_res.writerow([row[0]]+[row[1]]+[row[2]]+[byline_download]+[actual]+[correct]+[extra_text]+[missing]+[number]+[row[8]])

__main__()
