import  matplotlib.pyplot as plt
import pylab
import os
import matplotlib.cm as cm
from matplotlib import ticker
from electrozart import Note

from matplotlib.pyplot import figure, show
import numpy as np
from matplotlib.image import NonUniformImage
from feature_builder import get_interval_features


def plot_narmour_feature(prob_model, min_pitch, max_pitch, feature_name, folder, reference_note=None):
    if feature_name is not None: return
    max_interval= max_pitch - min_pitch
    max_interval= 12
    prob= [[None]*2*(max_interval+1) for i in xrange(2*max_interval+2)]
    if feature_name is not None: code= [[None]*2*(max_interval+1) for i in xrange(2*max_interval+2)]
    for i1_length in xrange(2*max_interval+2):
        for i2_length in xrange(2*max_interval+2):
            prob[i1_length][i2_length]= prob_model.get_interval_prob(i1_length-max_interval-1, i2_length-max_interval-1, feature_name=feature_name)
            if reference_note is not None:
                prob[i1_length][i2_length]= prob[i1_length][i2_length]*prob_model.notes_distr[Note(reference_note.pitch+i1_length+i2_length).get_canonical_note()]

            if feature_name is not None: 
                #code[i1_length][i2_length]= i1_length -max_interval-1 + i2_length -max_interval-1 
                code[i1_length][i2_length]= get_interval_features(i1_length-max_interval-1, i2_length-max_interval-1)[feature_name]
    

    x= range(2*max_interval+2)
    y= range(2*max_interval+2)

    #if feature_name is None:
    #    for reference_note in xrange(0, 12):
    #        print reference_note
    #        for i1_length in xrange(2*max_interval+2):
    #            for i2_length in xrange(2*max_interval+2):
    #                prob[i1_length][i2_length]= prob_model.get_interval_prob(i1_length-max_interval-1, i2_length-max_interval-1, feature_name=feature_name)
    #                prob[i1_length][i2_length]= prob[i1_length][i2_length]*prob_model.notes_distr[Note(reference_note+i1_length+i2_length).get_canonical_note()]

    #        prob_fname= os.path.join(folder, 'narmour_%s_%s.png' % (reference_note, feature_name))
    #        _do_plot(x, y, prob, prob_fname, max_interval)


    if feature_name == 'all': import ipdb;ipdb.set_trace()
    if feature_name is None: feature_name= 'all'
    if reference_note is not None:
        prob_fname= os.path.join(folder, 'narmour_%s_%s.png' % (reference_note, feature_name))
    else:
        prob_fname= os.path.join(folder, 'narmour_%s.png' % feature_name) 
    _do_plot(x, y, prob, prob_fname, max_interval, reference_note=reference_note)
    #if feature_name != 'all':
    #    code_fname= os.path.join(folder, 'code_narmour_%s.png' % feature_name) 
    #    _do_plot(x, y, code, code_fname, max_interval)

    
    

def _do_plot(x, y, z, fname, max_interval, reference_note=None):    
    fig = figure(figsize=(15,7.5+7.5/2))

    #fig.suptitle('Narmour')
    ax = fig.add_subplot(111)

    im = NonUniformImage(ax, interpolation=None, extent=(min(x), max(x), min(y), max(y)))
    im.set_data(x, y, z)
    ax.images.append(im)
    ax.set_xlim(min(x), max(x))
    ax.set_ylim(min(y), max(y))


    def format_interval_w_ref_note(reference_note):
        def format_interval(i, pos=None):
            if int(i) != i: import ipdb;ipdb.set_trace()
            return Note(int(reference_note.pitch + i - max_interval-1)%12).get_pitch_name()[:-1]
        return format_interval            

    def format_interval_wo_ref_note(x, pos=None):
        if int(x) != x: import ipdb;ipdb.set_trace()
        return int(x-max_interval-1) 
    
    if reference_note is not None:
        format_interval= format_interval_w_ref_note(reference_note)
    else:
        format_interval= format_interval_wo_ref_note
    
    ax.set_xlabel('Intervalo realizado')
    ax.axes.xaxis.set_major_formatter(ticker.FuncFormatter(format_interval_wo_ref_note))
    ax.axes.xaxis.set_major_locator(ticker.MultipleLocator(base=1.0))

    if reference_note is not None:
        ax.set_ylabel('Segunda nota')
    else:
        ax.set_ylabel('Intervalo implicativo')
    ax.axes.yaxis.set_major_formatter(ticker.FuncFormatter(format_interval))
    ax.axes.yaxis.set_major_locator(ticker.MultipleLocator())

    cb = plt.colorbar(im)
    pylab.grid(True)
    pylab.savefig(fname)
    pylab.close()

