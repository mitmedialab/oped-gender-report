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
    subparsers = parser.add_subparsers(help="Test mode (e.g. on stories in a csv or MC query)",dest='mode')
    testparser = subparsers.add_parser('eval',help="Extract for loaded test data")
    mcparser = subparsers.add_parser('mediacloud',help="Extract metadata for stories returned by given query")
    mcparser.add_argument('--rows',default=10,action='store',dest='rows',help='number of rows')
    mcparser.add_argument('--query',default='+publish_date:[2013-01-01T00:00:00Z TO 2013-12-31T00:00:00Z] AND +media_sets_id:1',dest='query',help='query (eg. "+publish_date:[2013-01-01T00:00:00Z TO 2013-12-31T00:00:00Z] AND +media_sets_id:1")')
    fparser = subparsers.add_parser('file',help="Extract metadata for stories listed in given file (assumes file is csv with fields for media_id, publish_date, stories_id, url, and file_name with path to file containing story's raw_first_download_file)")
    fparser.add_argument('filename',help="name of file to read story info from - assumes file is csv with stories_ids and optional path to file containing given story's raw_first_download_file")

    args = parser.parse_args()
    print args

    results = csv.writer(open('./test_sets/current_results.csv','wb'),delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
    
    if args.mode == 'eval':
        #load identifiers for evaluation storage                 
        eval_util = EvaluationUtil()
        # create evaluation folder if needed                
        eval_util.create_eval_dir()
        #create file for results in commit folder
        results = csv.writer(open(os.path.join(eval_util.eval_path, "extracted_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
        # create logfile to associate results with dates                     
        with open(os.path.join(eval_util.results_path, "byline_extraction.log"), "a") as extraction_log:
            extraction_log.write("{0}: {1}\n".format(datetime.datetime.now().isoformat(), eval_util.commit_number))
        results.writerow(['media_id']+['stories_id']+['publish_date']+['byline'] + ['female_byline'] + ['male_byline'] + ['unknown_byline']+['section_download'] + ['is_opinion'])
        URL = 'https://docs.google.com/spreadsheets/d/1WAkvfgW28HBETpoBFWdfkLtuVp1SM78bVTGbtzv7mUU/export?format=csv'
        response = requests.get(URL)
        assert response.status_code == 200, 'Wrong status code'
        csv_string = response.content
        f = StringIO.StringIO(csv_string)
        eval_base = csv.reader(f, delimiter=',')
        eval_res = csv.writer(open(os.path.join(eval_util.eval_path, "evaluated_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
        eval_res.writerow(['media_id']+['stories_id']+['url']+['extracted byline']+['actual byline']+['Is extracted byline correct?']+["If there's extra text, what is it?"]+["If there's missing text, what is it?"]+['How many names did we extract?']+['How many names in actual byline on the page?'])
        eval_base.next()
        eval_base.next()
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
        
    elif args.mode=='mediacloud':
        api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
        mc = mediacloud.api.MediaCloud(api_key)
        res = mc.sentenceList('sentence_number:1', args.query, start=0, rows=args.rows, sort='random')
        for s in res[u'response'][u'docs']:
            if str(s[u'media_id']) in MEDIA_BASEMETA_DICTIONARY:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(s[u'media_id'])]
            else:
                extractor = base_meta.BaseMeta()
            try:
                byline_download, section_download = extract_metadata(extractor, stories_id=s[u'stories_id'])
                byline_gender = gender_detector.byline_gender(byline_download)
                results.writerow([s[u'media_id']]+[s[u'stories_id']]+[s[u'publish_date']]+[s[u'url']]+[byline_download]+[section_download]+ [byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']])
            except Exception as e:
                pass

    elif args.mode == 'file':
        test = csv.DictReader(open(args.filename, 'rU'))
        for row in test:
            try:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(row['media_id'])]
            except Exception as e:
                extractor = base_meta.BaseMeta()
            try:
                byline_download, section_download = extract_metadata(extractor, file_name=row['file_name'])
                byline_gender = gender_detector.byline_gender(byline_download)
                results.writerow([row['media_id']]+[row['stories_id']]+[row['publish_date']]+[row['url']]+[byline_download]+[section_download]+ [byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']])
            except Exception as e:
                try:
                    byline_download, section_download = extract_metadata(extractor, stories_id=row['stories_id'])
                    byline_gender = gender_detector.byline_gender(byline_download)
                    results.writerow([row['media_id']]+[row['stories_id']]+[row['publish_date']]+[row['url']]+[byline_download]+[section_download]+ [byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']])
                except Exception as e:
                    pass
                pass
                    
__main__()

