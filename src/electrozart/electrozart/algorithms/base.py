from electrozart import PlayedNote, Silence
class ExecutionContext(object): pass
class AcumulatedInput(object): pass

class PartialNote(object): 
    def finish(self):
        if hasattr(self, 'pitch') and self.pitch > 0 and \
           hasattr(self, 'volume') and self.volume > 0:
            is_silence= False
        else:
            is_silence= True

        if is_silence:
            return Silence(self.start, self.duration)
        else:
            return PlayedNote(self.pitch, self.start, self.duration, self.volume)

class Algorithm(object):
    def start_creation(self): pass
    def next(self, input, result, prev_notes): pass
    def print_info(self): pass
    def draw_models(self, prefix): pass
    def train(self, score): pass

