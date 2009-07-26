from utils.hmm.random_variable import ConstantRandomVariable
from electrozart import Score

class ConditionalMidiObsSeq(object):
    def __call__(self, score):
        for instrument in score.instruments:
            if self.condition(instrument):
                notes= score.get_notes(instrument=instrument)# , relative_to='crotchet')
                return self._build_obs_seq(notes)
    
        raise Exception("no instrument found")

    def _build_obs_seq(self, notes):
        res= []
        for note in notes:
            pitch= volume= -1
            if not note.is_silence:
                pitch= note.pitch
                volume= note.volume

            #if volume == -1 or pitch == -1:import ipdb;ipdb.set_trace()
            pitch_var= ConstantRandomVariable(pitch, 'pitch')
            vol_var= ConstantRandomVariable(volume, 'volume')
            start_var= ConstantRandomVariable(note.start, 'start')
            duration_var= ConstantRandomVariable(note.duration, 'duration')
            res.append((note.duration, {pitch_var : pitch,
                                        vol_var : volume,
                                        start_var : note.start,
                                        duration_var: note.duration})) 

        return res

    def condition(self, instrument):
        raise NotImplementedException

class FirstVoiceObsSeq(ConditionalMidiObsSeq):
    def __init__(self, relative=False):
        super(FirstVoiceObsSeq, self).__init__(self)
        self.relative= relative

    def __call__(self, score):
        i= score.notes_per_instrument.keys()[0]
        if self.relative:
            notes= score.get_first_voice(relative_to='crotchet')
        else:
            notes= score.get_first_voice()
        return self._build_obs_seq(notes)

class MidiPatchObsSeq(ConditionalMidiObsSeq):
    def __init__(self, patch):
        """
        patch es el instrumento que me va a interesart seguir
        """
        ConditionalMidiObsSeq.__init__(self)
        self.patch= patch
    
    def condition(self, instrument):
        return instrument.patch == self.patch 


class MidiChannelObsSeq(ConditionalMidiObsSeq):
    def __init__(self, channel):
        """
        channel es el canal que importa
        """
        ConditionalMidiObsSeq.__init__(self)
        self.channel= channel
    
    def condition(self, instrument):
        return self.channel == instrument.channel
        

class MidiObsSeqOrder3(object):
    def __init__(self, obsseq):
        self.obsseq= obsseq
    def __call__(self, score):
        res= self.obsseq(score)
        res= [((s0,s1,s2), d2) for ((s0, d0), (s1, d1), (s2, d2)) in zip(res, res[1:], res[2:])]
        return res

