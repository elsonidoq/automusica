from playback import play
import braillemusic
import brlapi
import time

"""Interactive braille music score viewer."""

class BrailleItem(object):
    """A container to link braille patterns to underlying python objects."""
    def __init__(self, text, object):
        self.object = object
        self.text = text
    def __len__(self):
        return len(unicode(self.text))
    def __unicode__(self):
        return self.text
    def click(self, index):
        play(self.object)

class BrailleSegment(object):
    """A container for a segment of multiple BrailleItem objects."""
    def __init__(self, *items):
        self.items = list(items)
    def __getitem__(self, index):
        return self.items[index]
    def __len__(self):
        return len(self.items)
    def __getslice__(self, start, end):
        return BrailleSegment(*self.items[start:end])
    def __unicode__(self):
        return u''.join(map(unicode, self.items))
    def append(self, item):
        self.items.append(item)
    def click(self, index):
        if len(self.items)>0:
            item_index = 0
            length = len(unicode(self[item_index]))
            while index >= length and item_index < len(self.items)-1:
                item_index += 1
                length += len(unicode(self[item_index]))
            if index <= length:
                self[item_index].click(index-(length-len(unicode(self[item_index])))-1)
        
class BrailleViewer(braillemusic.AbstractFormatter):
    def __init__(self, score):
        self.score = score
        self.braille_display = brlapi.Connection()
        self.columns, self.lines = map(int, self.braille_display.displaySize)
        self.running = False
        self.content = []
        self.currentSegment = BrailleSegment()
        self.content.append(self.currentSegment)
        self.keymap = {brlapi.KEY_CMD_LNUP: self.lineUp,
                       brlapi.KEY_CMD_LNDN: self.lineDown,
                       brlapi.KEY_CMD_CHRRT: self.elementRight,
                       brlapi.KEY_CMD_CHRLT: self.elementLeft,
                       brlapi.KEY_CMD_ROUTE: self.click}
        self.format(score)
    def main(self):
        try:
            self.braille_display.enterTtyMode()
        except brlapi.OperationError:
            self.braille_display.enterTtyMode(int(raw_input("TTY Number: ")))
        self.running = True
        self.current_line = 0
        self.start_at = 0
        self.update_display()
        try:
            while self.running:
                self.read_key()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        self.stop()
    def stop(self):
        if self.running:
            self.braille_display.leaveTtyMode()
            self.running = False
    def startOfScore(self, score):
        pass
    def newSystem(self, system):
        self.currentSegment = BrailleSegment()
        self.content.append(self.currentSegment)
        super(BrailleViewer, self).newSystem(system)
    def startOfStaff(self, staff):
        pass
    def startOfMeasure(self, measure):
        self.whitespace(object=measure)
    def addSymbol(self, symbol, object=None):
        self.currentSegment.append(BrailleItem(symbol, object))
    def update_display(self):
        line = self.content[self.current_line][self.start_at:]
        self.braille_display.writeText(unicode(line))
    def lineUp(self, arg):
        if self.current_line > 0:
            self.current_line -= 1
            self.update_display()
    def lineDown(self, arg):
        if self.current_line < len(self.content)-1:
            self.current_line += 1
            self.update_display()
    def elementRight(self, arg):
        if len(self.content[self.current_line])>self.start_at+1:
            self.start_at += 1
            self.update_display()
    def elementLeft(self, arg):
        if self.start_at>0:
            self.start_at -= 1
            self.update_display()
    def click(self, index):
        if index == 80:
            self.running = False
        else:
            self.content[self.current_line][self.start_at:].click(index)
    def read_key(self):
        try:
            key_code = self.braille_display.readKey(False)
            while key_code:
                key = self.braille_display.expandKeyCode(key_code)
                if key['command'] in self.keymap:
                    self.keymap[key['command']](key['argument'])
                key_code = self.braille_display.readKey(False)
        except KeyboardInterrupt:
            self.running = False

