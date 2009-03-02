cp $1 tmp.mid
midi2ly tmp.mid
convert-ly tmp-midi.ly > tmp-midi.c.ly
lilypond tmp-midi.c.ly
rm tmp.mid tmp-midi.ly tmp-midi.c.ly
mv tmp-midi.c.pdf $1.pdf
rm tmp-midi.c.ps
echo "output in $1.pdf"
