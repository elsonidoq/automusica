# -*- coding: utf-8 -*-
from random import seed, shuffle
from time import sleep, time
import sys
from optparse import OptionParser
from interface import Window
import mididings
from psychopy import gui

import os
here= os.path.abspath(os.path.dirname(__file__))

def main():
    parser= OptionParser()
    parser.add_option('--full-screen', dest='full_screen', default=False, action='store_true')
    parser.add_option('--no-data', dest='ask_for_data', default=True, action='store_false')
    parser.add_option('--short-experiment', dest='short_experiment', default=False, action='store_true')

    options, args= parser.parse_args(sys.argv[1:])
    
    if options.ask_for_data: subject_data= ask_for_data()
    else: subject_data= dict(age=26, sex='m', musical_training=15)

    w= Window(words=load_words(), subject_data=subject_data, 
              full_screen=options.full_screen, short_experiment=options.short_experiment)
    w.start()
    
    mididings.config(client_name='exp', backend='jack')
    mididings.run(mididings.Process(w.recieve_event))
    
def load_words():
    with open(os.path.join(here, 'categorias.txt')) as f:
        lines= f.read().split('\n')
    
    lines= [[w.strip() for w in e.split('\t') if w.strip()] for e in lines]
    transp= [[],[],[],[]]
    for line in lines:
        for i, w in enumerate(line):
            transp[i].append(w)

    [shuffle(l) for l in transp]
    res= []
    tot= sum(len(l) for l in transp)
    while len(res) < tot:
        idxs= range(4)
        shuffle(idxs)
        for idx in idxs:
            res.append(transp[idx].pop(0))

    return res

def ask_for_data():
    #XXX
    data= ['','','', '']
    while True:
        myDlg = gui.Dlg()
        myDlg.addText('Datos')
        myDlg.addField('Nombre', data[0])
        myDlg.addField('Edad:', data[1])
        myDlg.addField('Genero (m/f):', data[2])
        myDlg.addField('Experiencia musical en anhos', data[3])
        myDlg.show()
        if not myDlg.OK: continue

        error= None
        data= myDlg.data
        if not data[0].strip():
            error= 'Falta el nombre'
        elif not data[1].strip().isnumeric():
            error= 'La edad debe ser numerica'
        elif data[2].lower() not in ['m','f']:
            error= 'El género debe ser o `m` o `f`'
        elif not data[3].strip().isnumeric():
            error= 'Anhos de experiencia musical debe ser numerico'
        
        if error is None: break
        myDlg = gui.Dlg()
        myDlg.addText(error)
        myDlg.show()
    
    the_seed= time()
    seed(the_seed)
    data= dict(seed=the_seed, name=data[0], age=int(data[1]), sex= data[2], musical_training=int(data[3]))
    return data

        

if __name__ == '__main__':
    main()
