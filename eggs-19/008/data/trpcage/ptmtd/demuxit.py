#!/usr/bin/python

import os

def readlog(i, orders):
  order = orders[-32:]
  ifile = open("mtd"+str(i+1)+"_0.log", "r").readlines()
  for line in ifile:
    if line[:7]=="Repl ex":
      exchanges = []
      for j in range(31):
        if line[j*5+11] == "x":
          exchanges.append(1)
        else:
          exchanges.append(0)
      for j in range(31):
        if exchanges[j] == 1:
          order[j], order[j+1] = order[j+1], order[j]
      orders = orders + order
      #print exchanges
      #print order
  orders = orders + order
  return orders

n = 14

for i in range(n):
  command = "cp ../pt1_"+str(i+1)+"/mtd"+str(i+1)+"_0.log ."
  os.system(command)

orders = range(32)
for i in range(n):
  orders = readlog(i, orders)

#for i in range(int(float(len(orders))/32.0)):
#  for j in range(32):
#    print orders[32*i+j],
#  print

for j in range(32):
  command = "gmx trjcat -f "
  for i in range(n):
    command = command + " ../pt1_"+str(i+1)+"/mtd"+str(i+1)+"_"+str(j)+".trr"
  command = command + " -o mtd"+str(j)+" -settime <<EOF\n"
  nsteps = [0,1000,2000,3000,4000,5000,10000,15000,20000,25000,30000,35000,40000,45000]
  for nstep in nsteps:
    command = command + str(nstep) + "\n"
  command = command + "EOF"
  os.system(command)
  command = "gmx trjconv -s ../minim.tpr -f mtd"+str(j)+" -o mtd"+str(j)+"nj -pbc mol << EOF\n1\nEOF"
  os.system(command)
  command = "gmx rms -s ../box.gro -f mtd"+str(j)+"nj -o rmsd"+str(j)+" << EOF\n4\n4\nEOF"
  os.system(command)

cv1 = []
for j in range(32):
  cvs1 = []
  #for i in range(n):
  ifile = open("rmsd"+str(j)+".xvg", "r").readlines()
  for k in range(len(ifile)):
    if ifile[k][0] not in ["#", "@"]:
      sline = str.split(ifile[k])
      if float(sline[0]) > 0.0:
        cvs1.append(float(sline[1]))
  cv1.append(cvs1)
print len(cvs1)
print len(orders)

for sel in range(32):
  ofile = open("rmsd_demuxed"+str(sel)+".txt", "w")
  for i in range(len(cv1[0])):
    myorders = orders[32*i:32*(i+1)]
    myindex = myorders.index(sel)
    ofile.write(" %f\n" % (cv1[myindex][i]))
  ofile.close()

