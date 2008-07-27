from tesis.freedots import musicxml
from tesis.hmm.hidden_markov_learner import HiddenMarkovLearner
from tesis.hmm.hidden_markov_model import *
from tesis.hmm.random_variable import ConstantRandomVariable
from itertools import imap

def train_hmm(fnames, score2obs_seq):
    """
    dada una lista de archivos y una funcion de traduccion que tome una Score y
    devuelva una observation sequence entrena un hmm y lo devuelve como
    resultado
    """
    learner= HiddenMarkovLearner()
    hidden_states= set()
    for i, fname in enumerate(fnames):
        print "loading", fname
        score= musicxml.load_file(fname)

        print "\tconverting to observation seq"
        obs_seq= score2obs_seq(score)

        hidden_states.update(imap(lambda x:x[0], obs_seq))

        print "\ttraining model"
        learner.train(obs_seq)

    initial_probability= dict( ((s,1.0/len(hidden_states)) for s in hidden_states) )
    print "building result"
    return learner.get_trainned_model(initial_probability)


from tesis.freedots.playback import MidiWriter
def create_song(output_file, hmm, song_size, divisions):
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
       



def simple_score2oseq(score):
    """
    transforma una partitura en una secuencia de notas. 
    Los hidden states no representan nada mas que el tic
    en el que ocurre
    nombres que dependen 
    """
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

def hidden_chord_s2observation(score):
    """
    estados ocultos: acordes
    observaciones: notes
    """
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
