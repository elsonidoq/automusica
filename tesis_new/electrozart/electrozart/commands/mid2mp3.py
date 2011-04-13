from base import BaseCommand
import sys
import os
import tempfile
import subprocess as sp
from random import random
from time import sleep

class Mid2Mp3(BaseCommand):
    name= 'mid2mp3'
    def setup_arguments(self, parser):
        parser.usage= 'usage: %prog [options] infname outfname'
        parser.add_option('-p', dest='n_processes', help='number of processes', default=1, type='int')

    def start(self, options, args, appctx):
        all_fnames= get_all_fnames(args)
        if options.n_processes > 1:
            Worker.all_fnames= len(all_fnames) 
            lists= split(all_fnames, options.n_processes)
            workers= map(Worker, lists)
            for w in workers:
                w.start()
                sleep(random() * 2)

            for w in workers:
                w.join()
        else:
            for fname in all_fnames:
                print 'Converting', fname
                mid2mp3(fname)

def mid2ogg(midi_fname, ogg_fname):
    command= [e % locals() for e in 'timidity -Ov %(midi_fname)s -o %(ogg_fname)s'.split()]
    p= sp.Popen(command, stdout=-1, stderr=-1)
    return p.wait()

def ogg2mp3(ogg_fname, mp3_fname):
    command= 'gst-launch-0.10 giosrc location="%(ogg_uri)s" name=src ! decodebin name=decoder ! audioconvert ! lame quality=2 vbr=4 vbr-quality=3 ! xingmux ! id3v2mux  ! giosink location="%(mp3_uri)s"'
    
    ogg_uri= 'file://' + os.path.abspath(ogg_fname)
    mp3_uri= 'file://' + os.path.abspath(mp3_fname)
    p= sp.Popen((command % locals()).split(), stdout=-1, stderr=-1)
    return p.wait()

def mid2mp3(midi_fname, mp3_fname=None, override=False):
    ogg_fname= tempfile.mktemp(suffix='.ogg')
    if mp3_fname is None: mp3_fname= midi_fname.replace('.mid', '.mp3')

    if os.path.exists(mp3_fname) and not override: 
        print mp3_fname + " Already exists"
        return 0

    res= mid2ogg(midi_fname, ogg_fname)        
    if res != 0: return res
    res= ogg2mp3(ogg_fname, mp3_fname)
    return res

from threading import Thread
class Worker(Thread):
    counter= 0
    all_fnames= None
    def __init__(self, fnames):
        super(Worker, self).__init__()
        self.fnames= fnames

    def run(self):
        for fname in self.fnames:
            #print 'Converting', fname
            if mid2mp3(fname) != 0: break
            Worker.counter+=1
            print Worker.counter, 'of', Worker.all_fnames



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
