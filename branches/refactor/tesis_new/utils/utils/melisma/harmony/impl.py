import os
import subprocess as sp
import tempfile
from electrozart.writing.notes import NotesScoreWriter

here= os.path.dirname(os.path.abspath(__file__))
meter_path= os.path.join(here, 'bin/meter')
harmony_path= os.path.join(here, 'bin/harmony')

meter_bin= os.path.join(meter_path, 'meter')
harmony_bin= os.path.join(harmony_path, 'harmony')

meter_params= os.path.join(meter_path, 'parameters')
harmony_params= os.path.join(harmony_path, 'parameters')

def harmony(score):
    writer= NotesScoreWriter()
    notes_file= tempfile.mktemp()
    writer.dump(score, notes_file)
    
    CMD1= '%(meter_bin)s -p %(meter_params)s %(notes_file)s' % dict(meter_params= meter_params, 
                                                                    meter_bin=meter_bin, 
                                                                    notes_file=notes_file)
    CMD2= '%(harmony_bin)s -p %(harmony_params)s ' % dict(harmony_bin=harmony_bin,
                                                          harmony_params=harmony_params)

    p1= sp.Popen(CMD1.split(), stdout=sp.PIPE)
    p2= sp.Popen(CMD2.split(), stdin=p1.stdout, stdout=sp.PIPE)
    stdout, stderr= p2.communicate()
    return stdout
