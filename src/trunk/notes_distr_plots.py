import pylab
from matplotlib import ticker
from matplotlib import rc
from electrozart.algorithms.harmonic_context import notes_distr_duration
from electrozart.algorithms.harmonic_context import notes_distr
from electrozart import Note


def format_pitch(x, pos=None):
    if int(x) != x: import ipdb;ipdb.set_trace()
    return Note(int(x)).get_pitch_name()[:-1]

import os
def plots_posteriors(score, notes, folder='posteriors'):
    #rc('text', usetex=True)
    #rc('font', family='serif')
    if not os.path.exists(folder):
        os.makedirs(folder)

    nd= notes_distr.NotesDistr(score)
    p= nd.score_profile
    y= [i[1] for i in sorted(p, key=lambda x:x[0])]
    x= [i[0].pitch for i in sorted(p, key=lambda x:x[0])]
    e= pylab.plot(x, y, label='score profile', color='black')[0]
    e.axes.set_xlabel('Nota')
    e.axes.set_ylabel('Probabilidad')
    ax= e.axes.xaxis
    ax.set_major_formatter(ticker.FuncFormatter(format_pitch))
    ax.set_major_locator(ticker.MultipleLocator())
    pylab.savefig(os.path.join(folder, 'prior-profile.png'))
    pylab.close()

    for strongnes in (0.5, 1, 2, 4, 8, 16):
        nd= notes_distr.NotesDistr(score, global_profile_prior_weight=strongnes)
        label='alpha %s' % strongnes
        p= nd.pitches_distr(notes)
        y= [i[1] for i in sorted(p, key=lambda x:x[0])]
        x= [i[0].pitch for i in sorted(p, key=lambda x:x[0])]
        e= pylab.plot(x, y, label=label, color='black')[0]
        e.axes.set_xlabel('Nota')
        e.axes.set_ylabel('Probabilidad')
        ax= e.axes.xaxis
        ax.set_major_formatter(ticker.FuncFormatter(format_pitch))
        ax.set_major_locator(ticker.MultipleLocator())

        pylab.savefig(os.path.join(folder, 'posterior-profile-%s.png' % strongnes))
        pylab.close()
    
def plots_duration(score):
    for strongnes in (0.5, 2, 4, 8, 16):
        nd= notes_distr_duration.NotesDistrDuration(score, duration_profile_prior_strength=strongnes)
        plot_noteorted(nd)


def plot_noteorted(nd):
    pylab.close()
    for k, p in sorted(nd.duration_profile.iteritems()):
        label='duration %s' % k
        y= [i[1] for i in sorted(p.items(), key=lambda x:x[0])]
        x= [i[0].pitch for i in sorted(p.items(), key=lambda x:x[0])]
        pylab.plot(x, y, label=label)
        #pylab.savefig('profile-%s-probsorted.png' % k)
    #pylab.close()

        #pylab.plot([i[1] for i in sorted(p.items(), key=lambda x:x[0])])
        #pylab.savefig('profile-%s.png' % k)
        #pylab.close()

    label='original'
    y= [i[1] for i in sorted(nd.score_profile, key=lambda x:x[0])]
    x= [i[0].pitch for i in sorted(nd.score_profile, key=lambda x:x[0])]
    pylab.plot(x,y, label=label)
    pylab.legend(loc='best')
    pylab.savefig('profiles-note-sorted-%s.png' % nd.params['duration_profile_prior_strength'])

    pylab.close()
