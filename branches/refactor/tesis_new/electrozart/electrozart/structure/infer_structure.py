from electrozart import Chord 

class StructureTree(object):
    def __init__(self, info, parent=None, children=None):
        self.name= name
        self.parent= parent
        self.children= children or []
    
    @staticmethod
    def from_score(score):
        chords= Chord.chordlist(score)
        
        root= StructureTree({'score':score})
        chord_trees=[]
        for chord in chords:
            chord_trees.append(StructureTree({'chord':chord}))
        root.children= chord_trees 


            
        
        
