from utils.fraction import Fraction
def get_duration_str(duration):
    if duration.numerador() == 1:
        duration_str= '%s' % duration.denominador()
    elif duration.numerador() == 3:
        assert duration.denominador() % 2 == 0
        duration_str= '%s.' % (duration.denominador()/2)
    else:
        raise Exception('figura que no se handlear')

    return duration_str

def get_silence_str(silence):
    return 'r%s' % get_duration_str(silence.duration)

def get_pitch_str(note):
    pitch_str= note.get_pitch_name()
    pitch_str= pitch_str.replace('#', 'is')

    octave_number= int(pitch_str[-1])
    pitch_str= pitch_str[:-1].lower()
    pitch_str= pitch_str + "'"*(octave_number-4)#2 #(octave_number-octave_number/2)
    return pitch_str

def get_note_str(note):
    pitch_str= get_pitch_str(note)
    return '%s%s' % (pitch_str, get_duration_str(note.duration))

def split_durations(duration, multiply_duration):
    """
    params:
      duration :: Fraction
    separa la duracion en duraciones que suman eso mismo para ligarlas
    """
    duration= duration*multiply_duration

    res= []
    if duration.numerador() > duration.denominador():
        res.append(Fraction(1,1))
        duration= Fraction(duration.numerador() - duration.denominador(), duration.denominador())

    d= { 1  : [1], 
         2  : [2],
         3  : [3],
         4  : [4],
         5  : [4, 1],
         6  : [4, 2],
         7  : [4, 3],
         9  : [4, 5], 
         10 : [5, 5],
         11 : [6, 5],
         12 : [6, 6],
         13 : [6, 7]}

    l= [duration.numerador()]
    while True:
        for i in xrange(len(l)):
            e= d[l[i]]
            if len(e) > 1:
                l[i:i+1]= e
                break
        else:
            break
    
    assert all((len(d[e]) == 1 for e in l))

    #import ipdb;ipdb.set_trace()
    #l= d[duration.numerador()]
    if len(l) == 1: 
        res.append(duration)
        return res 

    for e in l:
        res.append(Fraction(e, duration.denominador()))
    return res
