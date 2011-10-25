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
    def __init__(self, words, subject_data, full_screen=False, short_experiment=False):
        super(Window, self).__init__()

        self.short_experiment= short_experiment
        self.subject_data= subject_data
        self.full_screen= full_screen
        self.words= words
        self.events= []
        self.fname= get_outfname(os.path.join(here, 'data'), outfname='subject.json')

    def recieve_event(self, ev):
        if ev.type == mididings.NOTEON:
            self.events[-1].append({'type':'noteon', 'note':ev.note, 'velocity':ev.velocity, 'time':time()})
            print self.events[-1][-1]
        elif ev.type == mididings.NOTEOFF:
            self.events[-1].append({'type':'noteoff', 'note':ev.note, 'time':time()})
            print self.events[-1][-1]
        return ev 

    def save_data(self):
        print "saving to %s" % self.fname
        doc= dict(words= self.words,
                  events= self.events)
        doc.update(self.subject_data)
        with open(self.fname, 'w') as f:
            json.dump(doc, f, indent=1)

    def run(self):
        if self.full_screen:
            self.win = visual.Window(fullscr=True,monitor="testMonitor", units="deg") #create a window
        else:
            self.win = visual.Window([800,600],monitor="testMonitor", units="deg") #create a window
        quit_keys= set('lctrl q'.split())
        for i, word in enumerate(self.words):
            if self.short_experiment and i == 3: break
            if not isinstance(word, unicode): word= word.decode('utf8')
            t = visual.TextStim(text= word, win=self.win, pos=[0,0])
            t.draw()
            self.win.flip()
            self.events.append([])
            pressed_quit_keys= set()
            while True:
                l=event.waitKeys(maxWait=0.1) or []
                if quit_keys.issuperset(l): pressed_quit_keys.update(l)
                else: pressed_quit_keys= set()
                if pressed_quit_keys == quit_keys: break
                #print l
                if len(l) > 0 and any(e=='return' for e in l): break
                #refresh
                t.draw()
                self.win.flip()

            self.save_data()
            if pressed_quit_keys == quit_keys: break

        self.save_data()
        print "closing window..."
        self.win.close()
        print "quiting mididings..."
        mididings.engine.quit()
