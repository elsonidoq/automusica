#!/usr/bin/python
from __future__ import with_statement
from optparse import OptionParser
import yaml
import os

def build_run(include_fname, mid_fnames):
    output_dir= os.path.abspath(os.path.join(os.path.dirname(include_fname), os.path.basename(include_fname).replace('.yaml', '') + '_runs'))
    if os.path.exists(output_dir): 
        os.system('rm -rf %s/*' % output_dir)
    else:
        os.makedirs(output_dir)

    mids_output_dir= os.path.abspath(os.path.join(output_dir, 'mids'))
    if not os.path.exists(mids_output_dir): os.makedirs(mids_output_dir)

    for mid_fname in mid_fnames:
        yaml_fname= os.path.join(output_dir, os.path.basename(mid_fname).replace('mid', 'yaml'))
        content= dict(include=[os.path.abspath(include_fname)],
                      args= [os.path.abspath(mid_fname)],
                      options= {'output-dir':mids_output_dir})

        with open(yaml_fname, 'w') as f:
            yaml.dump(content, f)

def main(argv):
    usage= 'usage: %prog [options] yaml_include_fname mid_fnames'
    parser= OptionParser(usage=usage)

    options, args= parser.parse_args(argv[1:])
    if len(args) < 2: parser.error('not enaught args')
     
    include_fnames= [fname for fname in args if fname.endswith('.yaml') and os.path.basename(fname) != 'common.yaml']
    mid_fnames= [fname for fname in args if fname.endswith('.mid')]

    for include_fname in include_fnames:
        print "building for", include_fname
        build_run(include_fname, mid_fnames)
    print "done!"
if __name__ == '__main__':
    from sys import argv
    main(argv)
