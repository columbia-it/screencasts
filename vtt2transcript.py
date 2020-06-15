#!/usr/bin/env python3
"""
Converts VTT to HREFs

Input looks like:
WEBVTT

1
00:00:00.000 --> 00:00:03.340
this file. So we're looking here

2
00:00:03.340 --> 00:00:08.490
at the necessary documentation, which is pretty hard to read.

...
"""
import sys
import argparse
import re

parser = argparse.ArgumentParser(usage='%(prog)s [options] infile outfile')
parser.add_argument('infile', help='input VTT file')
parser.add_argument('outfile', help='output hyperlinked transcript html')
opt = parser.parse_args()

infile = open(opt.infile) if opt.infile != '-' else sys.stdin
outfile = open(opt.outfile, 'w') if opt.outfile != '-' else sys.stdout

webvtt = re.compile('^WEBVTT$')
empty = re.compile('^$')
seqno = re.compile('^\d+$')
notempty = re.compile('^.+$')
timestamp = re.compile('^(?P<hh>\d{2}):(?P<mm>\d{2}):(?P<ss>\d{2}).\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}$')

# state machine:
# state: (expected pattern, action, next state)
states = {
    's': (webvtt, None, 'blank',),
    'blank': (empty, None, 'seqno',),
    'seqno': (seqno, None, 'timestamp'),
    'timestamp': (timestamp, 'newhref', 'text',),
    'text': (notempty, 'collect', 'empty',),
    'empty': (empty, 'endhref', 'seqno',),
}

state = 's'
for line in infile:
    line = line.rstrip()
    matched = states[state][0].match(line)
    if matched:
        action = states[state][1]
        if action == None:
            pass
        elif action == 'newhref':
            secs = int(matched['hh']) * 3600 + int(matched['mm']) * 60 + int(matched['ss'])
            print('<A HREF="#" onclick="jumpTo({})">'.format(secs), file=outfile)
        elif action == 'collect':
            print(matched.group(0), file=outfile)
        elif action == 'endhref':
            print('</A>', file=outfile)
    else:
        print("match failed for line: '{}'".format(line), file=sys.stderr)
    state = states[state][2]
