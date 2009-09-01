from sys import argv
from datetime import datetime
from time import time
from os import walk, mkdir, path
from shutil import copy2

params= dict(experiments='experiments')

def main():
    if not path.exists(params['experiments']):
        print "experiments directory not found, creating one"
        mkdir(params['experiments'])

    dirs= walk(params['experiments']).next()[1] 
    existing_fnames= {}
    last_dir= None
    if len(dirs) > 0:
        last_dir= path.join(params['experiments'], max(dirs))
        existing_fnames= walk(last_dir).next()[-1]
        existing_fnames= dict((fname, path.getmtime(path.join(last_dir, fname))) for fname in existing_fnames)

    today= datetime.fromtimestamp(time()).isoformat()
    today= today[:today.find('T')]
    new_dir= path.join(params['experiments'], today)
    if not path.exists(new_dir):
        mkdir(new_dir)

    nfiles= 0
    for fname in walk('.').next()[-1]:
        if not fname.endswith('.mid'): continue
        mtime= path.getmtime(fname)
        if last_dir is not None:
            other_mtime= existing_fnames.get(fname)
            if other_mtime == mtime: continue

        nfiles+=1
        copy2(fname, path.join(new_dir, fname))
    print nfiles, 'files copied'
main()        
        



        

