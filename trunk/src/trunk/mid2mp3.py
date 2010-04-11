#!/usr/bin/python
import sys
from optparse import OptionParser
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

def mid2mp3(midi_fname, mp3_fname=None, override=False):
    ogg_fname= tempfile.mktemp(suffix='.ogg')
    if mp3_fname is None: mp3_fname= midi_fname.replace('.mid', '.mp3')

    if os.path.exists(mp3_fname) and not override: 
        print mp3_fname + " Already exists"
        return

    mid2ogg(midi_fname, ogg_fname)        
    ogg2mp3(ogg_fname, mp3_fname)

from threading import Thread
class Worker(Thread):
    def __init__(self, fnames):
        super(Worker, self).__init__()
        self.fnames= fnames

    def run(self):
        for fname in self.fnames:
            print 'Converting', fname
            mid2mp3(fname)


def main():
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)
    parser.add_option('-p', dest='n_processes', help='number of processes', default=1, type='int')
    options, args= parser.parse_args(sys.argv[1:])

    if options.n_processes > 1:
        lists= split(get_all_fnames(args), options.n_processes)
        workers= map(Worker, lists)
        [w.start() for w in workers]
        for w in workers:
            w.join()
    else:
        for fname in get_all_fnames(args):
            print 'Converting', fname
            mid2mp3(fname_or_folder)

def split(l, parts):
    size= float(len(l))/parts
    res= []
    for i in xrange(parts):
        if i == parts-1:
            res.append(l[int(i*size):])
        else:
            res.append(l[int(i*size):int((i+1)*size)])
    return res        
        
def get_all_fnames(fnames_or_folders):
    res= []
    for fname_or_folder in fnames_or_folders:
        if os.path.isdir(fname_or_folder):
            for root, dirs, fnames in os.walk(fname_or_folder):
                for fname in fnames:
                    if fname.endswith('.mid'):
                        res.append(os.path.join(root, fname))
    
        else:
            res.append(fname_or_folder)

    return res
if __name__ == '__main__':
    main()
