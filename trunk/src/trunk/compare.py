from __future__ import with_statement
from collections import defaultdict
import os
import sys 
from electrozart.parsing.midi import MidiScoreParser, MidiPatchParser, MidiScoreParserCache 

def main():
    solo_patch= 25
    fnames= sys.argv[1:]
    fnames.sort()

    matrix= defaultdict(dict)
    for i, fname1 in enumerate(fnames):
        for j, fname2 in enumerate(fnames[i:]):
            analysis= compare(fname1, fname2, solo_patch)
            matrix[i][i+j]= matrix[i+j][i]= analysis
            #bfname1= os.path.basename(fname1)
            #bfname2= os.path.basename(fname2)
            #print '%s%svs%s%s' % (bfname1, ' '*(15-len(bfname1)), ' '*(15-len(bfname1)), bfname2)
            #for k, v in analysis.items():
            #    print '%s%s%s' % (k,' '*(40-len(k)),v)
            #print        
    
    desc_table= '<table border="1"><tr><td><strong>position</strong></td><td><strong>experiment</strong></td></tr><tr><td>'  + '</td></tr><tr><td>'.join('%s</td><td>%s' % (i[0]+1, i[1]) for i in enumerate(fnames)) + '</td></tr></table>'
    row= '</td><td>'.join(map(str, range(1, len(matrix)+1)))
    row= '<tr><td></td><td>%s</td></tr>' % row
    rows= [row]
    for i, comparations in matrix.iteritems():
        row= '</td><td>'.join('%.02f' % analysis['same_notes'] for i, analysis in sorted(comparations.iteritems(), key=lambda x:x[0]))
        row= '<tr><td>%s</td><td>%s</td></tr>' % (i+1, row)
        rows.append(row)
                
    rows= '\n'.join(rows)                
    analysis_table= '<table border="1">\n%s\n</table>' % rows

    solo_len= analysis['solo1_len']

    html= '<html><body>\n%s\n<br><br><strong>solo length:</strong>%s\n%s\n</body></html>' % (desc_table, solo_len, analysis_table)
    with open('out.html', 'w') as f:
        f.write(html)

def compare(fname1, fname2, solo_patch):
    parser= MidiScoreParser()
    score1= parser.parse(fname1)
    score2= parser.parse(fname2)

    i1= get_solo_instrument(score1, solo_patch)
    i2= get_solo_instrument(score2, solo_patch)

    solo1= score1.get_notes(instrument= i1)
    solo2= score2.get_notes(instrument= i2)

    different_onsets= 0
    same_notes= 0

    solo1_idx= solo2_idx= 0
    while solo1_idx < len(solo1) and solo2_idx < len(solo2):
        n1= solo1[solo1_idx]
        n2= solo2[solo2_idx]

        if n1.start != n2.start: 
            different_onsets+= 1
            if n1.start < n2.start:
                solo1_idx+=1
            else:
                solo2_idx+=1
        else:
            if n1.pitch == n2.pitch: 
                same_notes+=1
            solo1_idx+=1                
            solo2_idx+=1
    
    if solo2_idx < len(solo2):
        import ipdb;ipdb.set_trace()

    if solo1_idx < len(solo1):
        import ipdb;ipdb.set_trace()
            
    if solo1[-1].end != solo2[-1].end: 
        import ipdb;ipdb.set_trace()

    #return float(same_notes)/len(solo1)
    return {'different_onsets':different_onsets, 
            'same_notes':float(same_notes)/len(solo1),            
            'solo1_len':len(solo1),
            'solo2_len':len(solo2)}

def get_solo_instrument(score, patch):
    candidates= [i for i in score.instruments if i.patch == patch]
    if len(candidates) != 1: import ipdb;ipdb.set_trace()
    return candidates[0]


if __name__ == '__main__':
    main()
