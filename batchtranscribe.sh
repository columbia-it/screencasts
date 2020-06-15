#!/bin/sh
# transcribes Quicktime video via AWS transcribe service and converted into video tracks for captioning.
# 1. convert .mov to .mp4
# 2. run through AWS transcription (time consuming)
# 3. generates a new HTML file that wraps this transcription
if [ $# -eq 0 ];
then
    echo "Usage: $0 filename..."
fi

for f in $*
do
    if echo $f | grep -q '.mov$'
    then
	b=`echo $f | sed -e 's/.mov$//'`
	mp4="$b.mp4"
	# standard scaling options: http://ffmpeg.org/ffmpeg-utils.html#Video-size
	ffmpeg -i $f -vcodec h264 -acodec mp2 -r 15  -vf "scale=qhd" $mp4
    elif  echo $f | grep -q '.mp4$'
    then
	 b=`echo $f | sed -e 's/.mp4$//'`
	 mp4="$f"
    fi
    base=`basename $b`
    vtt="$b.vtt"
    srt="$b.srt"
    python aws-transcribe.py --srt $srt $mp4 $vtt
    sed -e "s:FILE:$base:g" <base.html >$b.html
done

