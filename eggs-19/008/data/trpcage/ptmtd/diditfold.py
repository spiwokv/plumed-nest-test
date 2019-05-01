#!/usr/bin/python

import sys

ifile = open(sys.argv[1], "r").readlines()
up = 0
down = 0
for line in ifile:
  rmsd = float(line)
  if rmsd > 0.8:
    up = 1
  if rmsd < 0.2 and up == 1:
    down = 1
if down == 1:
  print "folded! :-)"
else:
  print "not folded! :-("
