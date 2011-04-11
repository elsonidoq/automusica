import os
from datetime import datetime

def get_outfname(infname, out_basepath, override=False):        
    outpath= os.path.abspath(os.path.join(out_basepath, datetime.now().strftime('%Y-%m-%d')))
    if not os.path.isdir(outpath):
        print "Creating dir", outpath
        os.makedirs(outpath)
    if os.path.exists('output'): os.unlink('output')
    os.system('ln -s %s output' % outpath)

    outfname= os.path.basename(infname).lower()
    if outfname in os.listdir(outpath):
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
    
    outfname= os.path.join(outpath, outfname)
    return outfname



