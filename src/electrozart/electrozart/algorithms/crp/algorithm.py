from crp import ChineseRestaurantProcess 
from collections import defaultdict
from electrozart.algorithms import Algorithm
from math import log
from electrozart.algorithms.applier import ExecutionContext
from electrozart import Chord



class CRPAlgorithm(Algorithm):
    def __init__(self, nparts, interval_size, rythm_model, harmony_model):
        self.crp= None
        self.nparts= nparts
        # es el de rythm
        self.interval_size= interval_size
        self.rythm_model= rythm_model
        self.harmony_model= harmony_model

    def start_creation(self, context_score):
        notes= context_score.get_notes(skip_silences=True) 
        max_note= max(notes, key=lambda n:n.start+n.duration)
        score_duration= max_note.start + max_note.duration
        nintervals= score_duration/self.interval_size
        self.alpha= self.nparts/log(nintervals, 2)
        self.crp= ChineseRestaurantProcess(self.alpha)

        self.execution_context= ExecutionContext()
        self.execution_context.last_robsid= None
        self.execution_context.parts= []
        self.execution_context.chordlist= Chord.chordlist(context_score)
        self.execution_context.parts_dict= defaultdict(self.crp.next) 
        self.cnt= 0

    def draw_models(self, prefix, state2str):
        for robsid, robs in self.rythm_model.execution_context.robses.iteritems():
            model= robs.get_model()
            model.draw('%s-rythm-%s.png' % (prefix, robsid), state2str)

        for robsid, robs in self.harmony_model.execution_context.robses.iteritems():
            model= robs.get_model()
            model.draw('%s-harmony-%s.png' % (prefix, robsid), state2str)
        
    def train(self, score): pass 

    def print_info(self):
        for start, model in self.execution_context.parts: 
            print float(start)/self.interval_size, '->', model
        
        print 'total parts:', self.crp.ntables
        
    def _actual_chord(self, start):
        chords= [c for c in self.execution_context.chordlist if c.start >=start]
        if len(chords) == 0: return self.execution_context.chordlist[-1]
        return chords[0]

    def next(self, input, result, prev_notes):
        #import ipdb;ipdb.set_trace()
        moment= 0
        if len(prev_notes) > 0: 
            moment= prev_notes[-1].end
        #if self.execution_context.last_robsid is None:
        #    model= self.crp.next()
        #    self.execution_context.last_robsid= model
        #    input.harmony_robsid= model
        #    input.rythm_robsid= model
        #    self.execution_context.parts.append((0, model))
        #else:
        robsid= self.crp.next()
        #import ipdb;ipdb.set_trace()
        robs= self.harmony_model.get_current_robs(robsid)
        robs= self.rythm_model.get_current_robs(robsid)
        if self.execution_context.last_robsid is not None:
            if robsid != self.execution_context.last_robsid:
                self.execution_context.parts.append((prev_notes[-1].end, robsid))


            robs= self.rythm_model.get_current_robs(robsid)
            prev_robs= self.rythm_model.execution_context.robses[self.execution_context.last_robsid]
            robs.actual_state= prev_robs.actual_state 

            robs= self.harmony_model.get_current_robs(robsid)
            prev_robs= self.harmony_model.execution_context.robses[self.execution_context.last_robsid]
            robs.actual_state= prev_robs.actual_state 

        self.execution_context.last_robsid= robsid            
            #if robs.actual_state == 0:
            #    #model= self.crp.next()
            #    #model= (self.execution_context.last_robsid+1) % 2
            #    if self.cnt % 5 == 0: model= (self.execution_context.last_robsid+1) % 2
            #    else: model= self.execution_context.last_robsid
            #    self.cnt+=1
            #    self.execution_context.last_robsid= model
            #    self.execution_context.parts.append((prev_notes[-1].end, model))
            #else:
            #    model= self.execution_context.last_robsid

        input.harmony_robsid= robsid
        input.rythm_robsid= robsid


