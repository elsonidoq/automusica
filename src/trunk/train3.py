#!/usr/bin/python
from __future__ import with_statement
from itertools import groupby
from time import time

from math import log
from md5 import md5
import cPickle as pickle
import random
import os
from os import path
from datetime import datetime


from utils.melisma.meter import meter
from utils.fraction import Fraction

from run_experiments import Experiment

from optparse import OptionParser
from electrozart.algorithms.hmm.melody.narmour_hmm import NarmourInterval
from electrozart import Instrument

def get_node_name(score, ticks):
    if isinstance(ticks, NarmourInterval):
        return repr(ticks)
    n_quarters= 0
    while ticks >= score.divisions:
        ticks-= score.divisions
        n_quarters+= 1

    if ticks > 0:
        f= Fraction(ticks, score.divisions)
        if n_quarters > 0: return "%s + %s" % (n_quarters, f)
        else: return repr(f)
    return "%s" % n_quarters 

def main(argv):
    usage= 'usage: %prog [options] infname outfname'
    parser= OptionParser(usage=usage)
    parser.add_option('--rythm-instr', dest='rythm_instr', help='If its an integer, is interpreted as a patch, if it is a tuple, (patch, channel)')
    parser.add_option('--melody-instr', dest='melody_instr', help='If its an integer, is interpreted as a patch, if it is a tuple, (patch, channel)')
    parser.add_option('-l', '--level', dest='level', default=3, type='int', help='if the partition algorithm is MGRID, especifies the level from which the score is going to be parted')
    parser.add_option('--n-measures', dest='n_measures', default=1, type='int', help='if the partition algorithm is MEASURE, especifies the number of measures to take as a unit')
    parser.add_option('--part-alg', dest='partition_algorithm', default='MEASURE', help='select the partition algorithm, only MEASURE and MGRID are available. Default MEASURE')
    parser.add_option('--seed', dest='seed',help='random seed', type='int')

    parser.add_option('--output-dir', dest='output_dir', default='output-mids', help='the default output dir')
    parser.add_option('-O', '--override', dest='override', help='if the outputfile exists, overrides. Default False', default=False, action='store_true')
    parser.add_option('--pitch-offset', dest='offset', default=0, type='int')
    parser.add_option('--disable-part-repetition', dest='enable_part_repetition', default=True, action='store_false')
    parser.add_option('--simple-narmour-model', dest='simple_narmour_model', default=False, action='store_true')
    parser.add_option('--global-notes-distr', dest='notes_distr_duration', default=True, action='store_false', help='uso por duracion o global? Default indexo por duracion')
    parser.add_option('-p', '--set-param', dest='params', action='append')
    parser.add_option('-s', '--save-info', dest= 'save_info', default=False, action='store_true')
    parser.add_option('-S', '--only-save-info', dest= 'only_save_info', default=False, action='store_true')
    parser.add_option('--folksong-narmour', dest= 'folksong_narmour', default=False, action='store_true')
    parser.add_option('--load-narmour', dest= 'load_narmour_pickle')
    parser.add_option('--save-narmour', dest= 'save_narmour_pickle')
    parser.add_option('--no-phrase-narmour', dest= 'phrase_narmour', default=True, action='store_false')



    options, args= parser.parse_args(argv[1:])
    if len(args) < 1: parser.error('not enaught args')


    if options.params:
        params= {}
        for line in options.params:
            left_side, value= line.split('=')
            class_path, param_name= left_side[:left_side.rindex('.')], left_side[left_side.rindex('.')+1:]

            class_params= params.get(class_path, {})
            class_params[param_name]= value
            params[class_path]= class_params

        e= Experiment(params)
        e.set_params()

    def parse_instr(preffix):
        patch_attr= preffix + 'patch'
        channel_attr= preffix + 'channel'
        instr_attr= preffix + 'instr'

        if getattr(options, instr_attr) is None:
            setattr(options, patch_attr, None)
            setattr(options, channel_attr, None)
        else:
            instr= eval(getattr(options, instr_attr))
            if isinstance(instr, int):
                setattr(options, patch_attr, instr)
                setattr(options, channel_attr, None)
            else:
                setattr(options, patch_attr, instr[0])
                setattr(options, channel_attr, instr[1])

    parse_instr('rythm_')
    parse_instr('melody_')

    rythm_patch= options.rythm_patch
    melody_patch= options.melody_patch
    level= options.level

    partition_algorithm= options.partition_algorithm
    if partition_algorithm not in ('MGRID', 'MEASURE'):
        parser.error('unknown partition algorithm')

    if options.seed is None: options.seed= int(time())
    #print "seed 1"
    #options.seed= 1
    #options.patch= 5

    return train3(options, args)


from electrozart.composers.narmour_markov import NarmourMarkov
from electrozart.composers.support_notes import SupportNotesComposer
from electrozart.composers.yaml import YamlComposer

from electrozart.parsing.midi import MidiScoreParser
from electrozart.writing.notes import NotesScoreWriter
from electrozart.writing.midi import MidiScoreWriter

def train3(options, args):
    print "using seed", options.seed

    infname= args[0]
    if len(args) >= 2:
        outfname= args[1]
    else:
        import electrozart
        outpath= path.abspath(path.join(electrozart.__path__[0], '../..', options.output_dir, datetime.now().strftime('%Y-%m-%d')))
        if not path.isdir(outpath):
            print "Creating dir", outpath
            os.makedirs(outpath)
        if os.path.exists('output'): os.unlink('output')
        os.system('ln -s %s output' % outpath)

        outfname= path.basename(infname).lower()
        if outfname in os.listdir(outpath) and not options.override:
            # -4 por el .mid +1 por el -
            versions= [fname[len(outfname)-4+1:-4] for fname in os.listdir(outpath) if fname.startswith(outfname[:-4])]
            versions= [s for s in versions if len(s) > 0]
            for i in reversed(xrange(len(versions))):
                if not versions[i].isdigit():
                    versions.pop(i)
                else:
                    versions[i]= int(versions[i])
            if len(versions) == 0:
                versions= [0]
            outfname= '%s-%s.mid' % (outfname[:-4], max(versions)+1)
        
        outfname= path.join(outpath, outfname)


    # fnames
    info_folder= outfname.replace('.mid', '-info')
    params_file= outfname[:-3] + 'log'
    diff_file= outfname[:-3] + 'diff'
    svn_file= outfname[:-3] + 'svn'
    solo_fname= outfname.replace('.mid', '-solo.mid')
    perc_fname= outfname.replace('.mid', '-perc.mid')
    wolp_fname= outfname.replace('.mid', '-wolp.mid')
    outfname= outfname.lower()

    parser= MidiScoreParser()
    score= parser.parse(infname)
    #score= quantize(score)
    
    composer= NarmourMarkov()
    composer= YamlComposer()
    composer= SupportNotesComposer()
    if options.only_save_info:
        composer.build_models(score, **options.__dict__)
        print "\n\nSAVING INFO\n\n"
        if os.path.exists(info_folder):
            import shutil
            shutil.rmtree(info_folder)
        os.makedirs(info_folder)
        composer.save_info(info_folder, score)
        print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, info_folder)
        return

    composed_score, instrument= composer.compose(score, **options.__dict__)
    # XXX
    composer.original_score= score
    composer.composed_score= composed_score
    orig_composed_score= composed_score.copy()

    writer= NotesScoreWriter()
    writer= MidiScoreWriter()
    writer.dump(composed_score, outfname)

    solo_notes= composed_score.get_notes(instrument=instrument)
    piano= Instrument(patch=None)
    composed_score.notes_per_instrument= {piano: solo_notes}
    writer.dump(composed_score, solo_fname)

    lp_notes= set(score.get_first_voice())
    notes_wolp= []
    composed_score.notes_per_instrument= {instrument: solo_notes}
    for i in score.instruments:
        if i == instrument: continue
        composed_score.notes_per_instrument[i]= [n for n in score.get_notes(instrument=i) if n not in lp_notes]

    writer.dump(composed_score, wolp_fname)

    import to_percusion
    perc_notes= to_percusion.get_percusion_track(solo_notes)
    orig_composed_score.notes_per_instrument[instrument]= perc_notes
    instrument.is_drums= True
    writer.dump(orig_composed_score, perc_fname)

    # draw things
    if options.save_info:
        os.makedirs(info_folder)

        composer.save_info(info_folder, score)
    
    params= composer.params
    params['options']= options.__dict__
    params['args']= args
        
    print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, info_folder)
    save_state(composer, params_file, diff_file, svn_file)

    print 'done!'

    return composer

def save_state(composer, params_file, diff_file, svn_file):
    from pprint import pprint
    with open(params_file, 'w') as f:
        pprint(composer.params, f)

    import subprocess
    with open(diff_file, 'w') as f:
        p= subprocess.Popen('svn diff .'.split(), stdout=subprocess.PIPE)
        f.write(p.stdout.read())

    with open(svn_file, 'w') as f:
        p= subprocess.Popen('svn info'.split(), stdout=subprocess.PIPE)
        f.write(p.stdout.read())

def print_files(params_file, diff_file, svn_file, outfname, solo_fname, wolp_fname, perc_fname, info_folder):
    print "info folder", info_folder
    print "params file", params_file
    print "diff file", diff_file
    print "svn info file", svn_file
        
    from utils.console import get_terminal_size
    width, height= get_terminal_size()
    print "*"*width
    print "midi file ", outfname
    print "solo file ", solo_fname
    print "perc file ", perc_fname
    print "wolp file ", wolp_fname
    print "*"*width

if __name__ == '__main__':
    import sys
    composer= main(sys.argv)
    

    
