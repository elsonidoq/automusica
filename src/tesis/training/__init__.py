from tesis.freedots import musicxml
from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from tesis.hmm.hidden_markov_model import *
from tesis.hmm.random_variable import ConstantRandomVariable
from itertools import imap

def train_hmm(fnames, file2obs_seq):
    """
    dada una lista de archivos y una funcion de traduccion que tome un archivo y
    devuelva una observation sequence entrena un hmm y lo devuelve como
    resultado
    """
    learner= HiddenMarkovLearner()
    hidden_states= set()
    for i, fname in enumerate(fnames):
        print "\tconverting `%s` to observation seq" % fname
        obs_seq= file2obs_seq(fname)

        hidden_states.update(imap(lambda x:x[0], obs_seq))

        print "\ttraining model"
        learner.train(obs_seq)

    initial_probability= dict( ((s,1.0/len(hidden_states)) for s in hidden_states) )
    print "building result"
    return learner.get_trainned_model(initial_probability)

from midistuff.writers.to_score import Score, Instrument
from midistuff.midi_messages import MidiMessage
def create_song(output_file, hmm, song_size, divisions):
    """
    dado un nombre de archivo, un hmm y un numero que determine el largo de la
    observation seq, genera un midi y lo escribe en output_file
    """
    obs= list(SizedRandomObservation(hmm, song_size))
    score= Score(divisions)
    instrument= Instrument()
    instrument.patch= 1
    acum_time= 5
    score.messages= [MidiMessage((96, 0, 3, 0, 0), 'smtp_offset', 0), MidiMessage((4, 2, 24, 8), 'time_signature', 0), MidiMessage((1, 0), 'key_signature', 0), MidiMessage((521739,), 'tempo', 0)]
    for i, o in enumerate(obs):
        pitch= o.values()[0]
        duration= o.keys()[0].get_value()
        score.note_played(instrument, pitch, acum_time, duration, 200)
        acum_time+= duration

    score.to_midi(output_file)
    return []

from tesis.freedots.playback import MidiWriter
def create_song_old(output_file, hmm, song_size, divisions):
    """
    dado un nombre de archivo, un hmm y un numero que determine el largo de la
    observation seq, genera un midi y lo escribe en output_file
    """
    obs= SizedRandomObservation(hmm, song_size)
    notes= [o.items()[0][1] for o in obs]
    notes[0].start_tick= 0
    notes[0].divisions=10
    for prev, next in zip(notes, notes[1:]):
        next.start_tick= prev.start_tick + prev.duration
    notes= map(lambda n:NoteWrapper(n, divisions), notes)        
        
    mw= MidiWriter(output_file)
    for n in notes:
        mw.write_note(n)
    mw.eof()
    return notes

class NoteWrapper(object):
    def __init__(self, note, divisions):
        self.divisions= divisions 
        self.midi= note.midi
        self.midiPitch= note.midiPitch
        self.start_tick= note.start_tick
        self.duration= note.duration
        self.pitch= note.pitch
       



def simple_score2oseq(fname):
    """
    transforma una partitura en una secuencia de notas. 
    Los hidden states no representan nada mas que el tic
    en el que ocurre
    nombres que dependen 
    """
    score= musicxml.load_file(fname)
    tic_number= 1
    res= []
    for part in score.parts:
        for measure in part.measures:
            for note in measure.musicdata.justNotes():
                tic_number+= 1
                # el diccionario es de variable aleatoria en observacion
                # en este caso la variable aleatoria debe ser "constante"
                # TODO: ver si hay una mejor forma de plantearlo
                var= ConstantRandomVariable(note, 'note')
                res.append((tic_number, {var:note}))



    return res

from midistuff.writers.to_score import MidiToScore
from midistuff.readers.MidiInFile import MidiInFile
class MidiObsSeq(object):
    def __init__(self, patch):
        """
        patch es el instrumento que me va a interesart seguir
        """
        self.patch= patch

    def __call__(self, fname):
        hdlr= MidiToScore()
        midi_in = MidiInFile(hdlr, fname)
        midi_in.read()
        for instrument, notes in hdlr.score.notes_per_instrument.iteritems():
            if instrument.patch == self.patch:
                return self._build_obs_seq(notes)
    
    def _build_obs_seq(self, notes):
        res= []
        for note in notes:
            duration_var= ConstantRandomVariable(note.duration, 'duration')
            res.append((note.note, {duration_var:note.duration}))

        return res
        
    
def hidden_chord_s2observation(fname):
    """
    estados ocultos: acordes
    observaciones: notes
    """
    score= musicxml.load_file(fname)
    res= []
    for p in score.parts:
        for m in p.measures:
            notes= m.musicdata.justNotes()

            # TODO: mover esto al parser de scores
            harmonies= m.harmonies
            for prev, next in zip(harmonies, harmonies[1:]):
                prev.stoping_note= next.starting_note
            if len(harmonies) > 0: harmonies[-1].stoping_note= len(notes)

            if len(harmonies) == 0:
                actual_harmony= None
            else:
                # a partir de aca harmonies es un iterador
                harmonies= enumerate(m.harmonies)
                # j se corresponde con el indice de actual_harmony en
                # harmonies
                j, actual_harmony= harmonies.next()
            
            for i, n in enumerate(notes):
                # si no hay acorde, no hay acorde
                if actual_harmony is None:
                    chord_name= 'nochord'
                else:
                    if i >= actual_harmony.starting_note:
                        chord_name= actual_harmony.chord_name + actual_harmony.kind
                    else:
                        chord_name= 'nochord'
                    # me fijo si debo actualizar actual_harmony
                    if i >= actual_harmony.stoping_note:
                        if j < len(m.harmonies)-1:
                            j, actual_harmony= harmonies.next()
                        else:
                            actual_harmony= None

                var= ConstantRandomVariable(n, 'note')
                res.append((chord_name, {var:n}))

    return res
