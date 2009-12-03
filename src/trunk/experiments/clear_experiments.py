#!/usr/bin/python
import shutil
import os
import sys

start_dir= sys.argv[1]
delete_dir= sys.argv[2]

for root, dirs, files in os.walk(start_dir):
    if os.path.basename(root) == delete_dir:
        ans= raw_input('delete %s? [Y/n]' % root)
        if ans.lower() == 'y' or ans == '':
            shutil.rmtree(root)
