import cStringIO
import os.path
import zipfile

from music import *
from utils.rational import lcm

from utils import ElementTree as etree

class MusicXMLParser:
    """Parse, transform and read a MusicXML file"""
    def __init__(self, filename, score):
        self.score = score
        self.partList = None
        self.currentMeasure = None
        self.lastNote = None
        self.currentChord = None
        self.addToChord = False

        # Compressed MusicXML (.mxl)
        if os.path.splitext(filename)[1] == '.mxl':
            archive = zipfile.ZipFile(filename, "r")
            container = etree.XML(archive.read("META-INF/container.xml"))
            rootfile = container.find("rootfiles/rootfile").get("full-path")
            doc = etree.parse(cStringIO.StringIO(archive.read(rootfile)))
        else:
            doc = etree.parse(filename)
        root = doc.getroot()
        partwise = None
        if root.tag == 'score-timewise':
            parts = dict((part.get('id'),
                          etree.SubElement(root, part.tag, part.attrib))
                         for part in root.find('measure'))
            for measure in list(root.findall('measure')):
                for part in measure:
                    etree.SubElement(parts[part.get('id')],
                                     measure.tag, measure.attrib).extend(part)
                root.remove(measure)
            root.tag = 'score-partwise'
        if root.tag == 'score-partwise':
            partwise = root
        if partwise is not None:
            self.read_score(partwise)
    def read(cls, filename, score=None):
        if score is None:
            score = Score()
        cls(filename, score)
        return score
    read = classmethod(read)

    def read_score(self, node):
        """Read a score-partwise top-level XML node."""
        self.score.worknumber = node.findtext("work/work-number")
        self.score.worktitle = node.findtext("work/work-title")
        self.score.movementnumber = node.findtext("movement-number")
        self.score.movementtitle = node.findtext("movement-title")
        self.partList = node.find("part-list")
        divisions = set(int(e.text) for e in
                        node.findall("part/measure/attributes/divisions"))
        if len(divisions) > 1:
            self.score.divisions = lcm(*divisions)
        else:
            self.score.divisions = divisions.pop()
        for child in node:
            if child.tag=="identification":
                for item in child:
                    if item.tag=="creator" and item.get("type")=="composer":
                        self.score.composer = item.text
            elif child.tag=="part":
                self.read_part(child)
    def read_part(self, node):
        part = Part()
        # Traverse the part-list for information matching our part ID
        for child in self.partList:
            if child.tag=="score-part" and child.get("id")==node.get("id"):
                for element in child:
                    if element.tag=="part-name" and element.text:
                        part.name = element.text.strip() or None
                    elif element.tag=="midi-instrument":
                        for item in element:
                            if item.tag=="midi-channel":
                                part.midi.channel = int(item.text)
                            elif item.tag=="midi-program":
                                part.midi.program = int(item.text)
        self.activeSlur = {}
        # Iterate over all children
        for child in node:
            if child.tag=="measure":
                measure = self.read_measure(child)
                measure.parent = part
                part.measures.append(measure)
        self.score.add(part)
    def read_measure(self, node):
        tick = 0
        measure = Measure(number=node.get("number"),
                          implicit=node.get('implicit', "no").lower() == "yes")
        self.currentMeasure = measure
        for child in node:
            if child.tag == 'print':
                if child.get('new-system', "no").lower() == "yes":
                    measure.newSystem = True
                elif child.get('new-page', "no").lower() == "yes":
                    measure.newSystem = True
            elif child.tag == 'attributes':
                for attrib in child:
                    if attrib.tag == 'divisions':
                        self.durationMultiplier = int(self.score.divisions/(int(attrib.text) or 1))
                    elif attrib.tag == 'clef':
                        clef = Clef(sign=attrib.findtext("sign").strip())
                        if attrib.findtext("line"):
                            clef.line = int(attrib.findtext("line"))
                        if attrib.findtext("clef-octave-change"):
                            clef.octaveChange = int(
                                attrib.findtext("clef-octave-change"))
                        if attrib.get("number"):
                            clef.staff = int(attrib.get("number"))
                        measure.add(clef)
                    elif attrib.tag == 'time':
                        nominator = None
                        denominator = None
                        for timetag in attrib:
                            if timetag.tag == 'beats':
                                nominator = int(timetag.text)
                            elif timetag.tag == 'beat-type':
                                denominator = int(timetag.text)
                        measure.time_signature = (nominator, denominator)
                    elif attrib.tag == 'key':
                        for keychild in attrib:
                            if keychild.tag == 'fifths':
                                measure.key_signature = int(keychild.text)
                    elif attrib.tag == 'transpose':
                        measure.transpose = Transposition(
                            chromaticSteps=int(attrib.findtext("chromatic")),
                            octave=int(attrib.findtext("octave-change") or 0))
                        if attrib.find("diatonic"):
                            measure.transpose.diatonicSteps = int(
                                attrib.findtext("diatonic"))
            elif child.tag == "harmony":
              root= child.find('root')
              root_alter= root.findtext('root-alter')
              if root_alter is None: root_alter= 0
              harm_chord= HarmonyChord(\
                      len(measure.musicdata), \
                      root.findtext('root-step'),\
                      root_alter, \
                      child.findtext('kind'))
              measure.harmonies.append(harm_chord)
            elif child.tag == 'note':
                note = self.readNote(child)
                note.measure = measure
                note.start_tick = tick
                if self.addToChord is True:
                    note.start_tick = self.currentChord.notes[0].start_tick
                    self.currentChord.add(note)
                else:
                    measure.add(note)
                    tick += note.duration
                    self.lastNote = note
                    self.currentChord = None
            elif child.tag == 'backup':
                tick -= int(child.findtext("duration")) * self.durationMultiplier
            elif child.tag == 'forward':
                tick += (int(child.findtext("duration"))
                         * self.durationMultiplier)
        return measure
    def readNote(self, node):
        self.addToChord = False
        note = Note(head=node.findtext('type'), dots=len(list(node.findall('dot'))))
        for child in node:
            if child.tag=="chord":
                if self.lastNote and self.currentChord is None:
                    self.currentChord = Chord(self.lastNote)
                    self.currentChord.measure = self.lastNote.measure
                    self.currentMeasure.musicdata[self.currentMeasure.musicdata.index(self.lastNote)] = self.currentChord
                if self.currentChord:
                    self.addToChord = True
            elif child.tag == 'duration':
                note.duration = int(child.text) * self.durationMultiplier
            elif child.tag == 'accidental':
                note.accidental = child.text.strip()
            elif child.tag == 'voice':
                note.voice = int(child.text)
            elif child.tag == 'staff':
                note.staff = int(child.text)
            elif child.tag == 'pitch':
                note.pitch = Pitch(step=child.findtext("step"),
                                   octave=child.findtext("octave"))
                note.pitch.alter = float(child.findtext("alter") or 0)
            elif child.tag == 'notations':
                for notation in child:
                    if notation.tag == 'articulations':
                        articulationsMap = {'accent': ACCENT,
                                            'breath-mark': BREATH_MARK,
                                            'staccato': STACCATO,
                                            'staccatissimo': STACCATISSIMO,
                                            'tenuto': TENUTO}
                        for articulation in notation:
                            if articulation.tag in articulationsMap:
                                note.articulations.add(articulationsMap[articulation.tag])
                    elif notation.tag == 'slur':
                        number = int(notation.get('number', '1'))
                        if notation.get('type')=="start":
                            self.activeSlur[number] = Slur()
                        elif notation.get('type')=="stop" and number in self.activeSlur:
                            self.activeSlur[number].add(note)
                            del self.activeSlur[number]
                    elif notation.tag == 'technical':
                        for technical in notation:
                            if technical.tag == 'fingering':
                                note.fingering = int(technical.text)
                            elif technical.tag == 'open-string':
                                note.fingering = 0
            elif child.tag == 'lyric':
                Lyric(text=child.findtext('text'),
                      syllabic=child.findtext('syllabic'),
                      note=note)
        # FIXME: Calculate head and dots statically if not given
        for slur in self.activeSlur.itervalues():
            slur.add(note)
        return note

load_file = MusicXMLParser.read

def save_file(score, file):
    """Save a score object in MusicXML format."""
    divisions = max((note.getValue()*4).d
                    for part in score
                    for measure in part
                    for note in measure.musicdata.justNotes())
    root = etree.Element("score-partwise")
    if score.worktitle or score.worknumber:
        work = etree.SubElement(root, "work")
        if score.worktitle:
            etree.SubElement(work, "work-title").text = score.worktitle
        if score.worknumber:
            etree.SubElement(work, "work-number").text = score.worknumber
    if score.movementnumber:
        etree.SubElement(root, "movement-number").text = score.movementnumber
    if score.movementtitle:
        etree.SubElement(root, "movement-title").text = score.movementtitle
    partID = dict((p, "P%d"%(i+1)) for i, p in enumerate(score))
    for part in score:
        partElement = etree.SubElement(root, "part", {'id': partID[part]})
        for measureNumber, measure in enumerate(part):
            measureElement = etree.SubElement(partElement, "measure",
                                              {'number': measure.number or measureNumber+1})
            if measureNumber == 0:
                etree.SubElement(etree.SubElement(measureElement,
                                                  "attributes"),
                                 "divisions").text = str(divisions)
    etree.ElementTree(root).write(file, encoding="utf-8")

# MusicXML file simplification

def simplify_file(filename, reindent=True):
    """Make a MusicXML file easier to read by removing redundancies.
This is a utility function mostly for people who work with
MusicXML files directly.  Some programs do export pretty verbose (but
still valid) MusicXML files which can be a pain to skim through.
This function parses a MusicXML file and tries to remove some
well known redundancies (like pitch alteration values of 0 or empty
container elements).  Output is also reindented.

Some of the musedata commentaries (which are preserved by hum2xml) are copied
into their appropriate MusicXML elements (work-title, composer and
copyright)."""
    from utils.rational import gcd
    from itertools import chain
    import re

    def gcdlist(a):
        return reduce(gcd, a, a[0])

    parser = etree.XMLParser(remove_blank_text=reindent)
    doc = etree.parse(filename, parser)
    root = doc.getroot()

    # Inspect the comments around the root element for musedata information
    musedata_comment={}
    for comment in chain(root.itersiblings(preceding=True),
                         root.itersiblings()):
        match = re.match(' *INFO.*key="([A-Z]+)" value="([^"]*)" *',
                         comment.text)
        if match:
            musedata_comment[match.group(1)] = match.group(2)

    # Find out if we can safely reduce divisions
    divisions = [e for e in doc.getiterator() if e.tag=="divisions"]
    if len(divisions) == 1:
        durations = [e for e in doc.getiterator() if e.tag=="duration"]
        divisiongcd = gcdlist([int(e.text) for e in durations])
        if divisiongcd > 1:
            for d in durations:
                d.text = str(int(int(d.text)/divisiongcd))
            divisions[0].text = str(int(int(divisions[0].text)/divisiongcd))

    # Iterate over all elements in the document (in document order)
    for e in doc.getiterator():
        # Is this a file from musedata (converted via humdrum by hum2xml)?
        if (e.tag=="score-partwise" or e.tag=="score-timewise") and \
           e[0].tag=="part-list" and len(musedata_comment)>0:
            work = etree.Element("work")
            if "OPR" in musedata_comment:
                title = etree.SubElement(work, "work-title")
                title.text = musedata_comment['OPR']
            if "SCT" in musedata_comment:
                opus = etree.SubElement(work, "work-number")
                opus.text = musedata_comment['SCT']
            identification = etree.Element("identification")
            if "COM" in musedata_comment:
                composer = etree.SubElement(identification, "creator")
                composer.set("type", "composer")
                composer.text = musedata_comment['COM']
            if "YEC" in musedata_comment:
                rights = etree.SubElement(identification, "rights")
                rights.text = musedata_comment['YEC']
            if len(identification)>0: 
                e.insert(0, identification) 
            if len(work)>0:
                e.insert(0, work)
        # compress "pitch", "backward" and "forward" elements in one line
        elif e.tag=="pitch" or e.tag=="backup" or e.tag=="forward":
            e.text=""
        # Remove redundant elements from their parents
        elif (e.tag=="work" and len(e)==0) or \
             (e.tag=="identification" and len(e)==0) or \
             (e.tag=="alter" and int(e.text)==0) or \
             (e.tag=="notations" and len(e)==0):
            del e.getparent()[e.getparent().index(e)]
    # Write XML back out to the original file
    doc.write(filename, pretty_print=reindent, xml_declaration=True)
