from base import BaseCommand
from collections import defaultdict
import sys
import os
from random import random
from time import sleep,time
import mididings

from threading import Thread
def ignore(ev): return ev
    
class Reciever(Thread):
    def run(self):
        mididings.run(mididings.Process(ignore))
        
class SendJack(BaseCommand):
    name= 'send-jack'
    def setup_arguments(self, parser):
        parser.usage= 'usage: %prog [options] infname outfname'
        #parser.add_option('-p', dest='n_processes', help='number of processes', default=1, type='int')

    def start(self, options, args, appctx):
        mididings.config(client_name='fname', out_ports=1, in_ports=0)
        r= Reciever()
        r.start()
        raw_input('enter to start...')
        try:
            self._start(options, args, appctx)
        finally:
            mididings.engine.quit()
            
    def _start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        fname= args[0]
        print "parsing..."
        score= parser.parse(fname)
        print "playing..."
        note_offs= defaultdict(list)
        t0= time()
        for note in score.get_notes(skip_silences=True):
            start= score.ticks2seconds(note.start)
            while time() - t0 < start: 
                min_noteoff= None
                t= time()
                if len(note_offs) > 0:
                    min_noteoff=min(note_offs)
                    sleep_time=min(start, min_noteoff) -time()+t0
                else:
                    sleep_time= start -time()+t0
                if sleep_time < 0: import ipdb;ipdb.set_trace()
                sleep(sleep_time)
                
                if min_noteoff is not None:
                    for pitch in note_offs.pop(min_noteoff):
                        ev= mididings.event.NoteOffEvent(0,1,pitch)
                        mididings.engine.output_event(ev)

            ev= mididings.event.NoteOnEvent(0,1,note.pitch, note.volume)
            mididings.engine.output_event(ev)

            note_offs[score.ticks2seconds(note.end)].append(note.pitch)

