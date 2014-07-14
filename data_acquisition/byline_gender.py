from gender_detector import GenderDetector
import nltk

class BylineGender():
  def __init__(self):
    self.detector = GenderDetector('us')

  def gender(self,byline):
    gender_result = {"female":0, "male":0,"unknown":0}
    for name in self.get_first_names(byline):
      gender_result[self.detector.guess(name)] += 1
    return gender_result

  def get_first_names(self, byline):
    print byline
    byline = byline.strip()
    spaces = byline.count(' ')
    commas = byline.count(',')
    conjunctions = byline.count('and')
    bylines_result = []
    if(commas == 0 and conjunctions == 0):
      bylines_result.append(self.get_first_name_from_fullname(byline))
    if(conjunctions >0):
      for name in byline.split('and'):
        bylines_result.append(self.get_first_name_from_fullname(name.strip()))
    if(spaces < 3 and commas == 1):
      bylines_result.append(self.get_first_name_from_reversename(byline))
    return bylines_result

  # assumes there's a single comma
  def get_first_name_from_reversename(self, byline):
    split_byline = [x.strip() for x in byline.split(',')]
    return self.get_first_name_from_fullname(split_byline[1])

  def get_first_name_from_fullname(self, byline):
    tokens = nltk.word_tokenize(byline)
    first_name = ""
    for token in tokens:
      if(token.count(".") > 0 or len(token) == 1):
        continue
      return token
    return byline.split(' ')

  def test_first_names(self):
    test_strings = [
      ["J. Nathan Matias", ["Nathan"]],
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
