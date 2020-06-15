#!/bin/sh
# Batch convert the (corrected) VTT transcripts to a hyperlinked transcript.
if [ $# -eq 0 ];
then
    echo "Usage: $0 filename..."
fi

for f in $*
do
    b=`echo $f | sed -e 's/.vtt$//'`
    vtt="$b.vtt"
    html="$b-transcript.html"
    python vtt2transcript.py $vtt $html
done

