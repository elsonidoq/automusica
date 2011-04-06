
def sign(n):
    if n is None: return None
    if n>=0: return 1
    else: return -1 

def get_pitch(n):
    if isinstance(n, int): return n
    else: return n.pitch

def get_features(n1, n2, n3):
    i1_length= get_pitch(n2) - get_pitch(n1)
    i2_length= get_pitch(n3) - get_pitch(n2)
    return get_interval_features(i1_length, i2_length)

def get_interval_features(i1_length, i2_length):
    features= {}
    if abs(i1_length)>6: 
        if sign(i1_length) == sign(i2_length): 
            features['rd']= 0
        else:
            features['rd']= 1
    else: # <=6
        features['rd']= 2

    if abs(i1_length) < 6:
        if sign(i1_length) != sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 3:
            features['id']= 1
        elif sign(i1_length) == sign(i2_length) and abs(abs(i1_length) - abs(i2_length)) < 4:
            features['id']= 1
        else:
            features['id']= 0 #0 #2
    elif abs(i1_length) > 6 and abs(i1_length) >= abs(i2_length):
        features['id']= 1
    else:
        features['id']= 0


    if sign(i1_length) != sign(i2_length) and abs(i1_length) - abs(i2_length) > 2:
        features['cl']= 2
    elif sign(i1_length) != sign(i2_length) and abs(i1_length) - abs(i2_length) < 3:
        features['cl']= 1
    elif sign(i1_length) == sign(i2_length) and abs(i1_length) - abs(i2_length) > 3:
        features['cl']= 1
    else:
        features['cl']= 0


    if abs(i2_length) < 3:                            features['pr']= 0
    elif 3 <= abs(i2_length) <= 5:                    features['pr']= 1
    #else: features['pr']= 2
    elif abs(i2_length) >=6 and abs(i2_length) < 12:  features['pr']= 2
    elif abs(i2_length) >= 12:                        features['pr']= 3

    if abs(i1_length + i2_length) <= 2:
        features['rr']= 1
    else:
        features['rr']= 0
    #features['rr']= min(abs(i1_length+i2_length), 3)

    #features['id pr cl']= features['id'], features['pr'], features['cl']
    #features.pop('id')
    #features.pop('pr')
    #features.pop('cl')

    return features


def all_features_values():
    res={}

    #for id_val in (0, 1):
    #    for cl_val in (0, 1, 2):
    #        for pr_val in (0, 1, 2):
    #            res['id pr cl'].append((id_val, pr_val, cl_val))
    
    res['id']= range(2)
    res['cl']= range(3)
    res['pr']= range(4)
    res['rd']= range(3)
    res['rr']= range(2)
    return res


