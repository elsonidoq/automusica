from crp import ChineseRestaurantProcess 
from collections import defaultdict
from electrozart.algorithms import Algorithm
from math import log
from electrozart.algorithms import ExecutionContext, AcumulatedInput, PartialNote
from electrozart import Chord
from random import randint, choice



class PartialChord(PartialNote):
    def finish(self):
        return Chord(self.start, self.duration, self.notes)

class PhraseAlgorithm(Algorithm):
    def __init__(self, divisions, alpha, chord_maker):
        self.divisions= divisions
        self.alpha= alpha
        self.chord_maker= chord_maker

    def start_creation(self):
        if hasattr(self, 'ec'): return
        self.ec= ExecutionContext()
        self.chord_maker.start_creation()
        # XXX sacar lo de divisions de TODOS lados, hay que manejar fracciones
        self.ec.crp= ChineseRestaurantProcess(self.alpha)
        self.ec.phrase_unit= choice([2,4]) * self.divisions
        #self.ec.phrase_unit= self.divisions
        self.ec.phrase_length= randint(2, 4) 

        self.ec.phrase_length= self.ec.phrase_length * self.ec.phrase_unit

        #self.ec.phrase_unit= 4 * self.divisions
        #self.ec.phrase_length= 3 * self.ec.phrase_unit

        self.ec.chords= []
        self.ec.phrase_cache= {}
        self.ec.this_phrase_id= 0
        self.ec.phrases= []
        self.ec.phrase= self.generate_phrase(0)

    def train(self, score): self.chord_maker.train(score)
    def print_info(self): 
        print 'phrase unit', self.ec.phrase_unit/self.divisions
        print 'phrase lenght', self.ec.phrase_length/self.ec.phrase_unit

        print "phrases", self.ec.phrases
        self.chord_maker.print_info()

    def _generate_phrase(self, phrase_id):
        phrase= []
        actual_phrase_length= 0
        phrase_length= self.ec.phrase_length
        input= AcumulatedInput()
        input.phrase_id= phrase_id

        first_start= None
        while actual_phrase_length < phrase_length:
            result= PartialChord()
            self.chord_maker.next(input, result, [])
            chord= result.finish()

            if first_start is None: first_start= chord.start

            chord.start-= first_start
            
            phrase.append(chord)
            actual_phrase_length+= chord.duration

        if phrase[-1].end > phrase_length:
            phrase[-1].duration= phrase_length-phrase[-1].start
        
        return phrase

    def generate_phrase(self, offset):
        phrase_id= self.ec.crp.next() #% 2
        self.ec.phrases.append(phrase_id)
        if phrase_id not in self.ec.phrase_cache:
            phrase= self._generate_phrase(phrase_id)
            self.ec.phrase_cache[phrase_id]= phrase
        else:
            phrase= self.ec.phrase_cache[phrase_id]

        result= []
        if phrase[0].start > 0: import ipdb;ipdb.set_trace()
        for i, chord in enumerate(phrase):
            if i == 0: volume= 80
            else: volume= 50
            result.append(Chord(chord.start+offset, chord.duration, chord.notes, volume))
        self.ec.this_phrase_id= phrase_id
        return result

            
    def next(self, input, result, prev_notes):
        if not hasattr(result, 'start'):
            input.phrase_id= self.ec.this_phrase_id 
            return

        result.volume= 70
        if result.start % self.ec.phrase_length == 0: result.volume= 100
        while True:
            if len(self.ec.phrase) == 0:
                self.ec.phrase= self.generate_phrase(self.ec.chords[-1].end)
                if self.ec.phrase[0].start != self.ec.chords[-1].end: import ipdb;ipdb.set_trace()

            phrase= self.ec.phrase
            while len(phrase) > 0 and phrase[0].end <= result.start:
                chord= phrase.pop(0)
                self.ec.chords.append(chord)

            if len(phrase) > 0: 
                assert phrase[0].end > result.start
                assert phrase[0].start <= result.start
                input.now_notes= phrase[0].notes
                break


        
        
