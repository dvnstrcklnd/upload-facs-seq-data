import os
import re
import sys
import subprocess
from datetime import datetime
from collections import defaultdict

# import pandas as pd

from util.agave_helper import BaseSpaceClient

bs = BaseSpaceClient()

# This name should match a BaseSpace Project name
bs.set_basespace_project('Protstab')

# This is the path on TACC where you want the data to go so that it can be with its friends
bs.set_tacc_service('data-sd2e-projects.sd2e-project-11')

# This is a subdirectory of tacc_path with the same name as the Aq plan
# It is not created automatically
bs.set_aq_plan('Plan_37976')

sample_list = bs.list_files()
print(len(sample_list))

sys.exit()

manifest_path = os.path.join(plan_path, 'manifest.csv')

manifest = pd.read_csv(manifest_path)

these_sample_names = [str(i) for i in list(manifest.aq_item_id)]

these_samples = [item for item in sample_list if item['name'] in these_sample_names]

print(len(these_samples))

ngs_data_path = os.path.join(plan, 'ngs_data')

for item in these_samples:
    s = item['name'].replace(' ', '%20')
    
    this_from_path = os.path.join('agave://data-sd2e-basespace-biofab', project_dir, s, "Files")
    this_to_path = os.path.join(ngs_data_path, s)
    
    if not os.path.isdir(this_to_path):
        cmd = ['files-mkdir', '-S', tacc_service, '-N', s, ngs_data_path]
        msg = subprocess.check_output(cmd)
        print(msg)

    # os.chdir(this_to_path)
    # print(os.getcwd())
    
    # TODO: Convert this to agavepy
    # cmd = ['files-get', '-r', '-S', 'data-sd2e-basespace-biofab', this_from_path]
    cmd = ['files-import', '-W', 'strcklnd@uw.edu', '-S', tacc_service, '-U', this_from_path, this_to_path]

    msg = subprocess.check_output(cmd)
    print(msg)
        