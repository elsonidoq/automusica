
def f(score):
    notes= score.get_notes(skip_silences=True)
    pitchs= [n.pitch for n in notes]
    
    melodic_accent= []
    for i in xrange(len(pitchs)-2):
        motion1= pitchs[i+1]-pitchs[i]
        motion2= pitchs[i+2]-pitchs[i+1]

        if motion1 == 0 and motion2 == 0:
            melodic_accent.append([0.00001, 0.0])
        elif motion1!=0 and motion2==0:
            melodic_accent.append([1, 0.0])
        elif motion1==0 and motion2!=0:
            melodic_accent.append([0.00001, 1])
        elif motion1>0 and motion2<0:
            melodic_accent.append([0.83, 0.17])
        elif motion1<0 and motion2>0:
            melodic_accent.append([0.71, 0.29])
        elif motion1>0 and motion2>0:
            melodic_accent.append([0.33, 0.67])
        elif motion1<0 and motion2<0:
            melodic_accent.append([0.5, 0.5])

    res= [1, melodic_accent[0][0]]
    for prev, next in zip(melodic_accent, melodic_accent[1:]):
        l= [prev[1], next[0]]
        l= [e for e in l if e > 0]
        if len(l) == 0: res.append(0)
        elif len(l) == 1: res.append(l[0])
        else: res.append(l[0]*l[1])
    res.append(0)

    return res
