#!/usr/bin/python
import os
import subprocess

def dot_builder(infname, outfolder):
    tempalte= 'dot -Tpng %(infname)s > %(outfname)s'
    outfname= os.path.join(outfolder, os.path.basename(infname).replace('.dot', '.png'))
    p= subprocess.Popen(tempalte % locals(), shell=True)

builders= dict(dot = dot_builder) 

images_src_dir= 'images_src'
images_dst_dir= 'images'

fnames= os.walk(images_src_dir).next()[-1]
for fname in fnames:
    extension= fname[-3:]
    if extension not in builders:
        print 'WARNING: not building %s' % fname
    else:
        builders[extension](os.path.join(images_src_dir, fname), images_dst_dir) 
    

