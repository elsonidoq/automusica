import os
from datetime import datetime

def get_outfname(out_basepath, infname= None, override=False, outfname=None):        
    if outfname is None and infname is None: raise Exception()

    outpath= os.path.abspath(os.path.join(out_basepath, datetime.now().strftime('%Y-%m-%d')))
    if not os.path.isdir(outpath):
        print "Creating dir", outpath
        os.makedirs(outpath)
    if os.path.exists('output'): os.unlink('output')
    os.system('ln -s %s output' % outpath)

    if outfname is None: outfname= os.path.basename(infname).lower()
    if outfname in os.listdir(outpath):
        # -4 por el .mid +1 por el -
        basename, ext= os.path.splitext(outfname)
        versions= [fname[len(basename)+1:-len(ext)] for fname in os.listdir(outpath) if fname.startswith(basename) and fname.endswith(ext)]
        versions= [s for s in versions if len(s) > 0]
        for i in reversed(xrange(len(versions))):
            if not versions[i].isdigit():
                versions.pop(i)
            else:
                versions[i]= int(versions[i])
        if len(versions) == 0:
            versions= [0]
        outfname= '%s-%s%s' % (basename, max(versions)+1, ext)
    
    outfname= os.path.join(outpath, outfname)
    return outfname



