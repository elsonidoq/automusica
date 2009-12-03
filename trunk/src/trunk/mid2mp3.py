#!/usr/bin/python
import os
import tempfile
import subprocess as sp

def mid2ogg(midi_fname, ogg_fname):
    command= [e % locals() for e in 'timidity -Ov %(midi_fname)s -o %(ogg_fname)s'.split()]
    p= sp.Popen(command)
    return p.wait()

def ogg2mp3(ogg_fname, mp3_fname):
    command= 'gst-launch-0.10 giosrc location="%(ogg_uri)s" name=src ! decodebin name=decoder ! audioconvert ! lame quality=2 vbr=4 vbr-quality=3 ! xingmux ! id3v2mux  ! giosink location="%(mp3_uri)s"'
    
    ogg_uri= 'file://' + os.path.abspath(ogg_fname)
    mp3_uri= 'file://' + os.path.abspath(mp3_fname)
    p= sp.Popen((command % locals()).split())
    return p.wait()

def mid2mp3(midi_fname, mp3_fname=None):
    ogg_fname= tempfile.mktemp(suffix='.ogg')
    if mp3_fname is None: mp3_fname= midi_fname.replace('.mid', '.mp3')
    mid2ogg(midi_fname, ogg_fname)        
    ogg2mp3(ogg_fname, mp3_fname)

def main():
    import sys
    fnames = sys.argv[1:]
    for fname_or_folder in fnames:
        if os.path.isdir(fname_or_folder):
            for root, dirs, fnames in os.walk(fname_or_folder):
                for fname in fnames:
                    if fname.endswith('.mid'):
                        fname= os.path.join(root, fname)
                        print 'Converting', fname
                        mid2mp3(fname)

        else:
            print 'Converting', fname_or_folder
            mid2mp3(fname_or_folder)

if __name__ == '__main__':
    main()
