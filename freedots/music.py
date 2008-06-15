"""Core module defining classes needed to represent a musical score."""
from math import log
import itertools

from utils.rational import Rational

### Constants:

ACCENT, BREATH_MARK, STACCATO, STACCATISSIMO, TENUTO = range(5)

### Classes:

class Score(object):
    """A score contains all the parts, staves and voices of one particular
movement of music."""
    def __init__(self, work=None, movement=None, composer=None):
        self.worknumber = None
        self.worktitle = None
        if work:
            if isinstance(work, basestring):
                self.worktitle = work
            elif isinstance(work, tuple):
                self.worknumber, self.worktitle = work
        self.movementnumber = None
        self.movementtitle = None
        if movement:
            if isinstance(movement, basestring):
                self.movementtitle = movement
            elif isinstance(movement, tuple):
                self.movementnumber, self.movementtitle = movement
            
        self.composer = composer
        self.parts = []
    def __iter__(self):
        return iter(self.parts)
    def part(self, index):
        """Retrieve a specific part either by name or numerical index."""
        if isinstance(index, basestring):
            for part in self:
                if part.name == index:
                    return part
            raise IndexError(index)
        return self.parts[index]
    def __repr__(self):
        if self.worktitle and self.worknumber:
            title = "title="+repr((self.worknumber, self.worktitle))
        elif self.worktitle:
            title = "title="+repr(self.worktitle)
        elif self.worknumber:
            title = "title="+repr(self.worknumber)
        else:
            title = ""
        if self.movementtitle and self.movementnumber:
            movement = "movement="+repr((self.movementnumber, self.movementtitle))
        elif self.movementtitle:
            movement = "movement="+repr(self.movementtitle)
        elif self.movementnumber:
            movement = "movement="+repr(self.movementnumber)
        else:
            movement = ""
        partCount = "%d parts" % len(self.parts)
        return "<%s %s>" % (self.__class__.__name__,
                            ", ".join(filter(lambda x: x!="", [title,
                                                               movement,
                                                               partCount])))
    def add(self, part):
        """Add a new part to this score."""
        self.parts.append(part)
        part.score = self
        return self

class Part(object):
    class MIDIInstrument:
        def __init__(self, channel=1, program=1):
            self.channel = channel
            self.program = program
        
    def __init__(self, name=None):
        self.name = name
        self.midi = Part.MIDIInstrument()
        self.measures = [] 
        self.score = None
    @property
    def divisions(self):
        if self.score:
            return self.score.divisions
    def groupBySystems(self):
        systems = []
        currentSystem = []
        systems.append(currentSystem)
        for measure in self.measures:
            if measure.newSystem:
                currentSystem=[]
                systems.append(currentSystem)
            currentSystem.append(measure)
        return systems
    def __iter__(self):
        return iter(self.measures)
    def time(self):
        if len(self.measures)>0:
            return self.measures[0].time()
    def key(self):
        if len(self.measures)>0:
            return self.measures[0].key()
    def __repr__(self):
        return "<%s name=%s, %d measures in %d systems>" % (self.__class__.__name__,
                                                            repr(self.name),
                                                            len(self.measures),
                                                            len(self.groupBySystems()))

class Musicdata(object):
    def __init__(self, *items):
        self._data = list(items)
    def append(self, item):
        self._data.append(item)
    def index(self, value):
        return self._data.index(value)
    def __iter__(self):
        return iter(self._data)
    def __len__(self):
        return len(self._data)
    def __getitem__(self, index):
        return self._data[index]
    def __setitem__(self, index, value):
        self._data[index]=value
    def __eq__(self, other):
        return isinstance(other, type(self)) and self._data==other._data
    def justNotes(self):
        return self.__class__(*filter(lambda obj: isinstance(obj, (Note, Chord)),
                                      self._data))
    def equalNotes(self, other):
        return self.justNotes()==other.justNotes()
    def staves(self):
        staff_dict = {}
        for item in self._data:
            staff_dict.update([(item.staff,item)])
        return len(staff_dict)
    def staff(self, index):
        staff_dict = {}
        for item in self._data:
            if not item.staff in staff_dict: staff_dict[item.staff] = []
            staff_dict[item.staff].append(item)
        return self.__class__(*staff_dict.values()[index])
    def voices(self):
        voice_dict = {}
        for item in self.justNotes():
            voice_dict.update([(item.voice,item)])
        return len(voice_dict)
    def voice(self, index):
        voice_dict = {}
        for item in self.justNotes():
            if not item.voice in voice_dict: voice_dict[item.voice]=[]
            voice_dict[item.voice].append(item)
        return self.__class__(*voice_dict.values()[index])

class Clef(object):
    """A clef (from the French for "key") is a musical symbol used to indicate
    the pitch of written notes.  Placed on one of the lines at the
    beginning of the staff, it indicates the name and pitch of the notes on
    that line.  This line serves as a reference point by which the names of
    the notes on any other line or space of the staff may be determined."""
    defaultLines = {'G': 2, 'F': 4, 'C': 3}
    def __init__(self, sign='G', line=None, octaveChange=None):
        self.sign = sign
        if line:
            self.line = line
        else:
            if self.sign in Clef.defaultLines:
                self.line = Clef.defaultLines[self.sign]
        self.octaveChange = octaveChange
        self.staff = None
    def __eq__(self, other):
        return isinstance(other, type(self)) and \
               self.sign == other.sign and \
               self.line == other.line and \
               self.octaveChange == other.octaveChange
    def __repr__(self):
        return "%s(sign=%r)>" % (self.__class__.__name__, self.sign)

class Transposition(object):
    """Indicates what must be added to the written pitch to get the correct
sounding pitch."""
    def __init__(self, chromaticSteps=0, octave=0, diatonicSteps=None):
        self.chromaticSteps = int(chromaticSteps)
        self.octave = int(octave)
        self.diatonicSteps = diatonicSteps
    def chromatic(self):
        return (self.octave*12)+self.chromaticSteps

class Measure(object):
    """A measure (or bar) is a segment of time defined as a given
number of beats of a given duration."""
    def __init__(self, number=None, implicit=False):
        self.number = number
        self.implicit = implicit
        self.parent = None
        self.newSystem = False
        self.key_signature = None
        # http://en.wikipedia.org/wiki/Time_signature
        self.time_signature = None
        self.transpose = None
        self.musicdata = Musicdata()
    @property
    def midi(self):
        """Get MIDI specific settings from the part this measure belongs to."""
        return self.parent.midi
    @property
    def divisions(self):
        """Get the divisions per quarter note from the part this measure
belongs to."""
        return self.parent.divisions
    def num(self):
        return self.parent.measures.index(self)+1
    def ticks(self):
        return int(Rational(*self.time())/(Rational(1,4)/self.divisions))
    def previousMeasures(self):
        prev = []
        if self.parent:
            prev = self.parent.measures[:self.parent.measures.index(self)]
            prev.reverse()
        return prev
    def key(self):
        if self.key_signature:
            return self.key_signature
        for measure in self.previousMeasures():
            if measure.key_signature:
                return measure.key_signautre
        return 0
    def time(self):
        if self.time_signature:
            return self.time_signature
        for measure in self.previousMeasures():
            if measure.time_signature:
                return measure.time_signature
        return (4, 4)
    def transposition(self):
        if self.transpose:
            return self.transpose
        for measure in self.previousMeasures():
            if measure.transpose:
                return measure.transpose
        return Transposition()
    def staves(self):
        return self.musicdata.staves()
    def staff(self, index):
        return self.musicdata.staff(index)
    def lyrics(self):
        string = u""
        for note in self.musicdata.justNotes():
            if note.lyric:
                string += unicode(note.lyric)
        return string
    def add(self, item):
        self.musicdata.append(item)
        item.measure = self
    def __repr__(self):
        return "<%s %s (%r/%r)>" % (self.__class__.__name__,
                                    self.number,
                                    self.time()[0], self.time()[1])

class Slur(object):
    """A symbol in Western musical notation indicating that the notes it
embraces are to be played without separation.
A slur is denoted with a curved line generally placed over the notes if
the stems point downward, and under them if the stems point upwards."""
    def __init__(self, *notes):
        self.notes = []
        map(self.add, notes)
    def add(self, note):
        self.notes.append(note)
        note.slur.append(self)

class Lyric:
    def __init__(self, text, syllabic, note):
        self.text = unicode(text)
        self.syllabic = syllabic
        self.note = note
        self.note.lyric = self
    def __str__(self):
        string = self.text
        if self.syllabic == 'single' or self.syllabic == 'end':
            string += " "
        return string

class Note(object):
    headnames = ['long', 'breve', 'whole', 'half', 'quarter', 'eighth',
                 '16th', '32nd', '64th', '128th', '256th']
    def __setattr__(self, item, value):
        if item == 'head' and isinstance(value, basestring):
            self.__dict__[item] = Note.headnames.index(value.strip())
        else:
            self.__dict__[item] = value
    def __init__(self, head=None, dots=None, pitch=None, accidental=None):
        self.head, self.dots, self.pitch = head, dots, pitch
        self.accidental = accidental
        self.measure = None
        self.duration = 0
        self.staff = None
        self.voice = None
        self.slur = []
        self.lyric = None
        self.articulations = set()
        self.fingering = None
    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
               self.staff == other.staff and \
               self.voice == other.voice and \
               self.pitch == other.pitch and \
               self.head == other.head and \
               self.dots == other.dots and \
               self.duration == other.duration
    @property
    def divisions(self):
        return self.measure.divisions
    @property
    def midi(self):
        return self.measure.midi
    def calculateHeadAndDotsFromDuration(self):
        if self.duration > 0 and self.measure:
            duration = (Rational(1,4)/self.measure.divisions)*self.duration
            for dots in range(7):
                for head in range(len(self.__class__.headnames)):
                    if duration == Rational(8, 2**head) - Rational(4, 2**head)/2**dots:
                        return (head, dots)
            raise ValueError("Unable to calculate notehead and dots from duration %r in measure %s" % (duration, self.measure.number))
    def getHead(self):
        """Return the notehead as a number starting at 0."""
        if self.head is not None:
            return self.head
        else:
            head, dots = self.calculateHeadAndDotsFromDuration()
            return head
    def getDots(self):
        if self.dots is not None:
            return self.dots
        else:
            head, dots = self.calculateHeadAndDotsFromDuration()
            return dots
    def getValue(self):
        """Return the note value including possibly augmentations by dots."""
        return (2*Rational(4, 2**self.getHead())
                - Rational(4, 2**self.getHead())/2**self.getDots())
    def __repr__(self):
        info = self.__class__.headnames[self.getHead()]
        if self.getDots()>0:
            info += " (%d dots, %r)" % (self.getDots(), self.getValue())
        if not self.pitch:
            info += " rest"
        return "<%s %s>" % (self.__class__.__name__, info)
    def slursRight(self):
        if len(self.slur)==1:
            slur = self.slur[0]
            return len(slur.notes[slur.notes.index(self)+1:])
        return 0
    def midiPitch(self):
        if self.pitch:
            return self.pitch.getMIDIpitch()+self.measure.transposition().chromatic()
    

class Pitch(object):
    stepnames = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    def __setattr__(self, item, value):
        if item == 'step' and isinstance(value, basestring):
            stepname = value.strip()
            self.__dict__[item] = Pitch.stepnames.index(stepname[0].upper())
        elif item == 'octave':
            self.__dict__[item] = int(value)
        elif item == 'alter':
            self.__dict__[item] = float(value)
        else:
            self.__dict__[item] = value
    def __init__(self, step=0, octave=4, alter=0):
        self.step, self.octave, self.alter = step, octave, alter
    def __eq__(self, other):
        return isinstance(other, type(self)) and \
               self.step==other.step and \
               self.octave==other.octave and \
               self.alter==other.alter
    def __repr__(self):
        alter = ""
        if self.alter != 0:
            alter = ", alter=%r" % self.alter
        return "%s(%r, %r%s)" % (self.__class__.__name__,
                                 Pitch.stepnames[self.step],
                                 self.octave, alter)
    def getMIDIpitch(self):
        return min(int(((self.octave+1)*12)
                       + [0,2,4,5,7,9,11][self.step]
                       + self.alter),
                   127)

class Chord(object):
    class IntervalIterator:
        def __init__(self, chord, descending):
            notes = chord.notes[:]
            notes.sort(semitoneDifference)
            if descending:
                notes.reverse()
            self.noteIter = iter(notes)
            self.fromNote = self.noteIter.next()
        def __iter__(self):
            return self
        def next(self):
            fromNote, toNote = self.fromNote, self.noteIter.next()
            diatonicSteps = (toNote.pitch.step+(toNote.pitch.octave*7)) - (fromNote.pitch.step+(fromNote.pitch.octave*7))
            self.fromNote = toNote
            return (fromNote, diatonicSteps, toNote)
    # FIXME: Add support for chords across multiple staves (and voices?)
    def __init__(self, *notes):
        self.notes = list(notes)
        self.staff = None
        self.voice = None
        self.measure = None
    def add(self, note):
        if note.pitch:
            self.notes.append(note)
        # FIXME
        self.staff = note.staff
        self.voice = note.voice
    def note(self, index, descending=False):
        notes = self.notes[:]
        notes.sort(semitoneDifference)
        if descending:
            notes.reverse()
        return notes[index]
    @property
    def lyric(self):
        self.note(0).lyric
    def iterintervals(self, descending=False):
        return Chord.IntervalIterator(self, descending)
    def clef(self):
        """Return the clef that is active for this chord.

        Iterates backwards in time over all elements to determine the last
        clef change.  If no clef is found, the G-clef is returned."""
        for event in itertools.chain(
            reversed(
            self.measure.musicdata[:self.measure.musicdata.index(self)]
            ),
            (item for measure in self.measure.previousMeasures()
             for item in reversed(measure.musicdata))):
            if isinstance(event, Clef):
                if event.staff is None:
                    return event
                else:
                    if event.staff == self.staff:
                        return event
        return Clef()

def semitoneDifference(a, b):
    return a.pitch.getMIDIpitch()-b.pitch.getMIDIpitch()
