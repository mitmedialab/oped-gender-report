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
import yaml

MEDIA_BASEMETA_DICTIONARY = {
	'1' : base_meta.NYTimesMeta(),
	'2' : base_meta.WashingtonPostMeta(),
	'6' : base_meta.LATimesMeta(),
    '7' : base_meta.NYPostMeta(),
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
eval_util = EvaluationUtil()

def extract_metadata(extractor, url=None, file_name=None, stories_id=None, import_full_text=False):
    extractor.make_soup(url=url,file_name=file_name,stories_id=stories_id,import_full_text=import_full_text)
    return extractor.get_byline(), extractor.get_section(), extractor.is_opinion()
    
def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument('--fulltext', action="store_true", help="export full text of stories",default=False)
    subparsers = parser.add_subparsers(help="Test mode (e.g. on stories in a csv or MC query)",dest='mode')
    testparser = subparsers.add_parser('eval',help="Extract for loaded test data")
    mcparser = subparsers.add_parser('mediacloud',help="Extract metadata for stories returned by given query")
    mcparser.add_argument('--rows',default=10,action='store',dest='rows',help='number of rows')
    mcparser.add_argument('--media',default=' OR '.join(MEDIA_BASEMETA_DICTIONARY.keys()),dest='media',action='store',help="media_id's to query, separated by ' OR '")
    fparser = subparsers.add_parser('file',help="Extract metadata for stories listed in given file (assumes file is csv with fields for media_id, publish_date, stories_id, url, and file_name with path to file containing story's raw_first_download_file)")
    fparser.add_argument('-f','--filename',help="name of file to read story info from - assumes file is csv with stories_ids and optional path to file containing given story's raw_first_download_file")
    args = parser.parse_args()

	#if args.filename:
	#	for m_id, path in MEDIA_FILEPATH_DICTIONARY:
#			if re.match('^('+path+')',args.filename):
#				extractor = MEDIA_BASEMETA_DICTIONARY[str(row['media_id'])]
#		print extract_metadata(extractor, file_name=args.filename)
#    results = csv.writer(open('./test_sets/current_results.csv','wb'),delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
    # create evaluation folder if needed        
    eval_util.create_eval_dir()
    results = csv.writer(open(os.path.join(eval_util.eval_path, "downloaded_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
    results.writerow(['media_id', 'stories_id','publish_date','url','byline_download','female','male','unknown','section','is_opinion','full_text'])
    if args.mode=='mediacloud':
        api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
        mc = mediacloud.api.MediaCloud(api_key)
        query = '+publish_date:[2010-01-01T00:00:00Z TO 2014-07-26T00:00:00Z] AND +media_id:('+args.media+')'
        res = mc.sentenceList('sentence_number:1', query, start=0, rows=args.rows, sort='random')
        for s in res[u'response'][u'docs']:
            if str(s[u'media_id']) in MEDIA_BASEMETA_DICTIONARY:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(s[u'media_id'])]
            else:
                extractor = base_meta.BaseMeta()
            try:
                byline_download, section_download, is_opinion = extract_metadata(extractor, stories_id=s[u'stories_id'], import_full_text=args.fulltext)
                byline_gender = gender_detector.byline_gender(byline_download)
                result_row = [s[u'media_id']]+[s[u'stories_id']]+[s[u'publish_date']]+[s[u'url']]+[byline_download]+[byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']]+[section_download]+ [is_opinion] + [extractor.full_text]
                results.writerow([unicode(s).encode("utf-8") for s in result_row])
                sys.stdout.write('.')
            except Exception as e:
                sys.stdout.write('x')
                pass

    elif args.mode == 'file':
        test = csv.DictReader(open(args.filename, 'rU'))
        for row in test:
            try:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(row['media_id'])]
            except Exception as e:
                extractor = base_meta.BaseMeta()
            try:
                byline_download, section_download, is_opinion= extract_metadata(extractor, file_name=row['file_name'], import_full_text=args.fulltext)
                byline_gender = gender_detector.byline_gender(byline_download)
                result_row = [row['media_id']]+[row['stories_id']]+[row['publish_date']]+[row['url']]+[byline_download]+[byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']]+[section_download]+ [is_opinion] + [extractor.full_text]
                results.writerow(result_row)
            except Exception as e:
                try:
                    byline_download, section_download, is_opinion= extract_metadata(extractor, stories_id=row['stories_id'])
                    byline_gender = gender_detector.byline_gender(byline_download)
                    result_row = [row['media_id']]+[row['stories_id']]+[row['publish_date']]+[row['url']]+[byline_download]+[byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']]+[section_download]+ [is_opinion] + [extractor.full_text]
                    results.writerow(result_row)
                except Exception as e:
                    pass
                pass
                    
__main__()

