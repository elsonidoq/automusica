# -*- coding: utf-8 -*-
from time import sleep
import mididings
import json
from time import time
from psychopy import visual, core, event
from threading import Thread
from outfname_util import get_outfname
import os
here= os.path.abspath(os.path.dirname(__file__))


class Window(Thread):
    def __init__(self, words, subject_data, full_screen=False):
        super(Window, self).__init__()

        self.subject_data= subject_data
        self.full_screen= full_screen
        self.words= words
        self.events= []

    def recieve_event(self, ev):
        if ev.type == mididings.NOTEON:
            self.events[-1].append({'type':'noteon', 'note':ev.note, 'velocity':ev.velocity, 'time':time()})
            print self.events[-1][-1]
        elif ev.type == mididings.NOTEOFF:
            self.events[-1].append({'type':'noteoff', 'note':ev.note, 'time':time()})
            print self.events[-1][-1]
        return ev 

    def save_data(self):
        fname= get_outfname(os.path.join(here, 'data'), outfname='subject.json')
        doc= dict(words= self.words,
                  events= self.events)
        doc.update(self.subject_data)
        with open(fname, 'w') as f:
            json.dump(doc, f, indent=1)

    def run(self):
        if self.full_screen:
            1/0
        else:
            self.win = visual.Window([800,600],monitor="testMonitor", units="deg") #create a window
        for word in self.words:
            t = visual.TextStim(text= word, win=self.win, pos=[0,0])
            t.draw()
            self.win.flip()
            self.events.append([])
            while True:
                l=event.waitKeys(0.1) 
                t.draw()
                self.win.flip()
                if l is not None and len(l) > 0 and any(e=='return' for e in l): break

        print "saving data.."
        self.save_data()
        print "closing window..."
        self.win.close()
        print "quiting mididings..."
        mididings.engine.quit()
