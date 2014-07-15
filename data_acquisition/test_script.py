import optparse
import base_meta
import mediacloud
import csv
from byline_gender import BylineGender

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

gender_detector = BylineGender()

def extract_metadata(extractor, url=None, file_name=None, stories_id=None):
    #try:
    extractor.make_soup(url=url,file_name=file_name,stories_id=stories_id)
    return extractor.get_byline(), extractor.get_section()
    #except Exception as e:
    #    return None, type(e)
    
def __main__():

    parser = optparse.OptionParser()
    parser.add_option("-t", "--test", help="test base_meta.py on default dataset", dest="file_name")
    parser.add_option("-m", "--mediacloud", help="run base_meta.py on specified query", dest="mc_query")
    parser.add_option("-n", "--number", help="number of stories to process", dest="number")
    (opts, args) = parser.parse_args()

    if opts.file_name:
        #load identifiers for evaluation storage                                                                                                    
        eval_util = EvaluationUtil()
        # create evaluation folder if needed                                                                                                     
        eval_util.create_eval_dir()

        results = csv.writer(open(os.path.join(eval_util.eval_path, "extracted_results.csv"), 'wb'), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)

        # create logfile to associate results with dates                                                                                       
        with open(os.path.join(eval_util.results_path, "byline_extraction.log"), "a") as extraction_log:
            extraction_log.write("{0}: {1}\n".format(datetime.datetime.now().isoformat(), eval_util.commit_number))

        results.writerow(['media_id']+['stories_id']+['publish date']+['url']+['byline from first download']+['section from first download'] + ['female_byline'] + ['male_byline'] + ['unknown_byline'])

        test = csv.DictReader(open('./test_sets/test_set_index.csv','rU'))
        for row in test:
            if str(row['media_id') in MEDIA_BASEMETA_DICTIONARY:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(row['media_id'])]
            else:
                extractor = base_meta.BaseMeta()
            byline_download, section_download = extract_metadata(extractor, file_name=(MEDIA_FILEPATH_DICTIONARY[str(row['media_id'])]+str(row['stories_id'])+'.html'))
            byline_gender = gender_detector.byline_gender(byline_download)
                   results.writerow([row['media_id']]+[row['stories_id']]+[row['publish date']]+[row['url']]+[byline_download]+[section_download]+ [byline_gender['female']] + [byline_gender['male']] + [byline_gender['unknown']])

    elif opts.mediacloud:
        api_key = yaml.load(open('config.yaml'))['mediacloud']['api_key']
        mc = mediacloud.api.MediaCloud(api_key)
        num = opts.number if opts.number else 10
        res = mc.sentenceList('sentence_number:1', opts.mc_query, start=0, rows=num, sort='random')
        for s in res[u'response'][u'docs']:
            media_id = s[u'media_id']
            if str(media_id) in MEDIA_BASEMETA_DICTIONARY:
                extractor = MEDIA_BASEMETA_DICTIONARY[str(media_id)]
            else:
                extractor = base_meta.BaseMeta()
            byline_url, section_url = extract_metadata(extractor, url=s[u'url'])
            byline_download, section_download = extract_metadata(extractor, stories_id=s[u'stories_id'])
            results.writerow([row[0]]+[row[1]]+[row[2]]+[row[3]]+[byline_download]+[section_download])

__main__()
