#!/bin/sh
# https://drive.google.com/file/d/1atgDWvoWWEkK-xWT6-63X3dGgPAw9PGn/view?time=999s
if [ $# -ne 3 ]
then
    echo "Usage: $0 videourl input output"
    exit 1
fi
url="$1"
in="$2"
out="$3"
sed -e "s~HREF=\"#\" onclick=\"jumpTo(\([0-9]+\))\"~HREF=\"${url}&time=\1s\"~" < $in > $out
