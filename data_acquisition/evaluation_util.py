import subprocess
import os
import datetime

class EvaluationUtil():

  def __init__(self):
    cmd = ['git', 'rev-parse', '--verify', 'HEAD']
    self.commit_number = subprocess.Popen(cmd, stdout=subprocess.PIPE ).communicate()[0].strip()
    self.results_path = "test_results"
    self.eval_path = os.path.join(self.results_path, self.commit_number)
    print self.eval_path

  # create results file
  # results files are stored in test_results/COMMIT_NUMBER/
  # extracted_bylines includes all cases of a positive byline match
  # failed_bylines includes all cases of a negative byline match
  def create_eval_dir(self):
    if not os.path.exists(self.eval_path):
          print("outputting to {0}".format(self.eval_path))
          os.makedirs(self.eval_path)
