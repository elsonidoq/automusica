def get_metrical_grid(pulses, notes_by_ioi, pitch_profile, volume_normalizer):
    complete_solutions= []
    for pulse in pulses:
        remaining_pulses= [p for p in pulses if p != pulse]
        sol= _get_metrical_grid(remaining_pulses, [pulse], complete_solutions)

    if len(complete_solutions) == 0:
        return []
    else:
        res= max(complete_solutions, key=lambda s: evaluate_solution(s, notes_by_ioi, pitch_profile, volume_normalizer))
        return res


def _get_metrical_grid(remaining_pulses, partial_solution, complete_solutions):
    partial_sol_updated=False
    for pulse in remaining_pulses:
        index= get_insertion_index(partial_solution, pulse)
        if index is not None:
            partial_sol_updated= True
            new_solution= partial_solution[:]
            new_solution.insert(index, pulse)
            new_remainin_pulses= [p for p in remaining_pulses if p != pulse]
            _get_metrical_grid(new_remainin_pulses, new_solution, complete_solutions)

    if not partial_sol_updated and len(partial_solution)>1:
        complete_solutions.append(partial_solution)

def get_insertion_index(partial_solution, pulse):
    index= None
    for i, (prev, next) in enumerate(zip(partial_solution, partial_solution[1:])):
        if pulse.is_compatible(next) and prev.is_compatible(pulse):
            return i+1
    else:
        if partial_solution[-1].is_compatible(pulse):
            return len(partial_solution)
        elif pulse.is_compatible(partial_solution[0]):
            return 0



def evaluate_solution(metrical_grid, notes_by_ioi, pitch_profile, volume_normalizer):
    # XXX
    # ESTOY FAVORECIENDO PULSOS CHICOS
    res= 0
    for pulse in metrical_grid:
        for n in notes_by_ioi[pulse.period]:
            if n.start % pulse.period != pulse.offset: continue
            res+= pitch_profile[n.get_canonical()] 
            res+= volume_normalizer(n.volume)
    res= float(res)/len(metrical_grid)

    error= 0
    cnt= 0
    for i, pulse in enumerate(metrical_grid):
        if i == 0:
            error+= pulse.get_error(metrical_grid[1])
            cnt+=1
        elif i == len(metrical_grid)-1:
            error+= pulse.get_error(metrical_grid[i-1])
            cnt+=1
        else:
            error+= pulse.get_error(metrical_grid[i-1])
            error+= metrical_grid[i+1].get_error(pulse)
            cnt+=2

    error= error/cnt

    return res/error            

def is_metrical_grid(pulses):
    for i, p1 in enumerate(pulses):
        for p2 in pulses[i+1:]:
            if not p1.is_compatible(p2): return False
   
    return True




def check_metrical_grid(metrical_grid, score):
    nom, denom= score.time_signature
    denom= 2**denom
    if denom == 4:
        beat= score.divisions
    elif denom == 8:
        beat= score.divisions/2
    else:
        import ipdb;ipdb.set_trace()

    beat= float(beat)
    found_beat= any((p.period/beat - 1) <= 0.05 for p in metrical_grid)
    #if not found_beat: import ipdb;ipdb.set_trace()
    import ipdb;ipdb.set_trace()
    if nom % 3 == 0:
        correct= any((p.period/beat/3 - 1) <= 0.05 for p in metrical_grid)
    elif nom % 2 == 0:
        correct= any((p.period/beat/2 - 1) <= 0.05 for p in metrical_grid)
    
    return found_beat, found_beat and correct

