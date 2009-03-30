from base import ScoreWriter
from midistuff.writers.MidiOutFile import MidiOutFile
from electrozart.util import Interval
from midistuff.midi_messages import MidiMessage

class MidiScoreWriter(ScoreWriter):
    def dump(self, score, fname):
        #import ipdb;ipdb.set_trace()
        tracks= self._organize_tracks(score)

        mof= MidiOutFile(fname)
        if len(score.messages) > 0:
            mof.header(1, len(tracks)+1, score.divisions)
            mof.start_of_track(0)
            for message in score.messages:
                message.apply(mof)
            mof.end_of_track()
            track_number= 1
        else:
            mof.header(1, len(tracks), score.divisions)
            track_number= 0

        for stuff in tracks:
            mof.start_of_track(track_number)
            self._save_track(mof, stuff)
            mof.end_of_track()
            track_number+= 1

        mof.eof() # currently optional, should it do the write instead of write??

    def _generate_events(self, track):
        """
        params:
          track :: [(instrument, notes)]
        """
        events= []
        for i, (instrument, notes) in enumerate(track):
            if instrument.is_drums:
                channel= 9
            else:
                channel= i+1
            for note in notes:
                if note.is_silence: continue
                args= [channel, note.pitch, note.volume]
                note_on= MidiMessage(args, 'note_on', note.start)
                note_off= MidiMessage(args, 'note_off', note.start+note.duration)
                events.append(note_on)
                events.append(note_off)

            if instrument.patch is not None:
                patch_event_time= max(min(notes, key=lambda n:n.start).start-1, 0)
                patch_event= MidiMessage([channel, instrument.patch], 'patch_change', patch_event_time) 
                events.append(patch_event)

            for msg_factory in instrument.messages:
                msg_factory.bind_channel(channel)
                event= msg_factory.get_message() 
                event.instrument= instrument
                events.append(event)

        # los note events van despues
        def mycmp(e1, e2): 
            if e1.method_name == e2.method_name: return 0
            if e1.method_name.startswith('note'): return 1
            return -1

        events.sort(cmp=mycmp)
        events.sort(key=lambda e:e.time)
        return events

    def _save_track(self, mof, stuff):
        events= self._generate_events(stuff)
        for event in events:
            mof.update_time(event.time, relative=False)
            try: event.apply(mof)
            except: import ipdb;ipdb.set_trace()

    def _organize_tracks(self, score):
        #import ipdb;ipdb.set_trace()
        intervals= {}
        for instrument, notes in score.notes_per_instrument.iteritems():
            min_tick= min(notes, key=lambda n:n.start).start
            max_tick= max(notes, key=lambda n:n.start)
            max_tick= max_tick.start + max_tick.duration
            intervals[instrument]= Interval(min_tick, max_tick)

        instruments= sorted(intervals.iteritems(), key=lambda i:i[1].x0)
        instruments= [i[0] for i in instruments]
        res= []
        for instrument in instruments:
            notes= score.notes_per_instrument[instrument]
            for i in xrange(len(res)):
                if len(res[i]) == 8: continue
                for instrument2, notes2 in res[i]:
                    if instrument2.patch == instrument.patch and \
                            intervals[instrument2].intersects(intervals[instrument]):
                        break
                else:
                    res[i].append((instrument, notes))
                    break
            else:
                res.append([(instrument, notes)])

        assert sum(map(len, res)) == len(score.notes_per_instrument)
        return res


