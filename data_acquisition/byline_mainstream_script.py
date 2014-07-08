import BeautifulSoup
import csv
import mediacloud
import yaml

f = open('config.yaml')
api_key = yaml.load(f)['mediacloud']['api_key']
mc = mediacloud.api.MediaCloud(api_key)

#build media_dict                                                                                                                                                                  
media_dict = dict()
rfile_dict = open("media_byline_dictionary.csv", 'rU')
reader_dict = csv.reader(rfile_dict)
for row in reader_dict:
    if row[0] not in media_dict:
        media_dict[str(row[0])] = []
    media_dict[str(row[0])].append([row[1],row[2],row[3]])
    
#build results file

wfile = open("extracted_bylines.csv", 'wb')
writer = csv.writer(wfile, delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)

badwfile = open("failed_bylines.csv", 'wb')
badwriter = csv.writer(badwfile, delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)

#generate test set

res = mc.sentenceList('sentence_number:1', '+publish_date:[2010-01-01T00:00:00Z TO 2014-6-01T00:00:00Z] AND +media_sets_id:1', start=0, rows=50, sort='random')

for s in res[u'response'][u'docs']:
    stories_id = s[u'stories_id']
    media_id = s[u'media_id']
    url = s[u'url']
    try:
        bylineFound = False
        raw_content = mc.story(stories_id,raw_1st_download=1)[u'raw_first_download_file']
        soup = BeautifulSoup.BeautifulSoup(raw_content)
        if str(media_id) in media_dict:
            for tag_set in media_dict[str(media_id)]:
                if bylineFound is False and soup.find(tag_set[0], {tag_set[1]:tag_set[2]}) is not None:
                    bylineFound = True
                    if tag_set[0]=='meta':
                        byline = soup.find(tag_set[0], {tag_set[1]:tag_set[2]})['content']
                    else:
                        byline = soup.find(tag_set[0], {tag_set[1]:tag_set[2]}).text
                    foundwith = tag_set[0] + '[' + tag_set[1] + '=' + tag_set[2] + ']'
                    writer.writerow([media_id]+[url]+[stories_id]+[foundwith]+[byline])
            if bylineFound is False:
                badwriter.writerow([media_id]+[url]+[stories_id]+['Included not found'])
        else:
            badwriter.writerow([media_id]+[url]+[stories_id]+['Not included'])
    except Exception as e:
        badwriter.writerow([media_id]+[url]+[stories_id]+[type(e)])
