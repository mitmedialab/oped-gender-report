import requests
import json
import yaml

CLIFF_URL = yaml.load(open('config.yaml'))['cliff']['url']

def people(content):
  req = requests.post(CLIFF_URL,params={"q":content})
  try:
    j = json.loads(req.text)
    if(len(j[u'results'])>0):
      return j[u'results'][u'people']
    else:
      print j.keys()
  except:
    return []
  return []
