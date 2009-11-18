#!/usr/bin/python
import os
import subprocess

def dot_builder(infname, outfolder):
    tempalte= 'dot -Tpng %(infname)s > %(outfname)s'
    outfname= os.path.join(outfolder, os.path.basename(infname).replace('.dot', '.png'))
    p= subprocess.Popen(tempalte % locals(), shell=True)

def lilypond_builder(infname, outfolder):
    templates= ("lilypond -b eps -o %(outprefix)s %(infname)s",
                "convert %(pdf_fname)s %(png_fname)s",
                "rm %(pdf_pattern)s",
                "rm %(eps_pattern)s",
                "rm %(tex_pattern)s",)

    infolder= os.path.dirname(infname)
    png_fname= os.path.join(outfolder, os.path.basename(infname).replace('.ly', '.png'))
    pdf_pattern= png_fname.replace('.png', '*.pdf')
    tex_pattern= png_fname.replace('.png', '-systems.tex*')
    pdf_fname= png_fname.replace('.png', '.pdf')
    eps_pattern= png_fname.replace('.png', '*.eps')
    outprefix= png_fname.replace('.png', '')

    for template in templates:
        template%= locals()
        print template
        p= subprocess.Popen(template, shell=True, stdout=-1)
        p.wait()
        
builders= dict(dot = dot_builder,
               ly  = lilypond_builder) 

images_src_dir= 'images_src'
images_dst_dir= 'images'

import sys
if __name__ == '__main__':
    if len(sys.argv) > 1: fnames= sys.argv[1:]
    else: fnames= os.walk(images_src_dir).next()[-1]

    for fname in fnames:
        if '.' not in fname: continue
        extension= fname[fname.rindex('.')+1:]
        if extension not in builders:
            print 'WARNING: not building %s' % fname
        else:
            builders[extension](os.path.join(images_src_dir, fname), images_dst_dir) 
        

