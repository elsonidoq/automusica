from base import BaseCommand
from midistuff.midi_messages import MidiMessage
from electrozart import PlayedNote, Score, Instrument
import json
from collections import defaultdict
import sys
import os

class Json2Mid(BaseCommand):
    name= 'json2mid'
    def setup_arguments(self, parser):
        parser.usage= 'usage: %prog [options] infname outfname'
        #parser.add_option('-p', dest='n_processes', help='number of processes', default=1, type='int')

    def start(self, options, args, appctx):
        parser= appctx.get('parsers.midi')
        fname= args[0]
        suffix= os.path.splitext(fname)[0].split('-')[1]
        with open(fname) as f:
            data= json.load(f)
        writer= appctx.get('writers.midi')
        for i, word in enumerate(data['words']):
            self.dump_events(data['events'][i], '%s-%02d-%s.mid' % (word, i, suffix), writer)

    def dump_events(self, events, fname, writer):
        t0= min(e['time'] for e in events)
        s= Score(480*4)
        MICROSECONDS_PER_MINUTE = 60000000.0
        s.tempo= MICROSECONDS_PER_MINUTE/120
        notes= []
        raw_events= {}
        error= 0
        for e in events:
            error+= abs(e['time'] - s.ticks2seconds(round(s.seconds2ticks(e['time']),0)))
            if e['type'] == 'noteon':
                raw_events[e['note']]= e
            elif e['type'] == 'noteoff':
                ee= raw_events.pop(e['note'])
                start= int(round(s.seconds2ticks(ee['time'] - t0),0))
                duration= int(round(s.seconds2ticks(e['time']-ee['time']),0))
                notes.append(PlayedNote(e['note'], start, duration, ee['velocity']))
         
        print "Error: %s secs" % error
        i= Instrument()
        s.notes_per_instrument= {i:notes}
        s._messages= [] #[MidiMessage((434782,), 'tempo', 0)]

        writer.dump(s, fname.encode('utf8'))




