#! /usr/bin/env python3

from random import randrange,random
from sys import argv

density = float(argv[1]) if len(argv)>1 else 1 

m1 = [[randrange(1<<64)*((random()<density)) for i in range(32)]
       for j in range(32)]
m2 = [[13+i+2*j for i in range(2)] for j in range(4)]

def matrixconst(M,arch):
    sizere = 0
    result = bytes()
    for ligne in M:
        for elt in ligne:
            result += elt.to_bytes(arch//8,"big")
    return result


f = open("mat32x32.bytes","wb")
f.write(matrixconst(m1,64))
f.close()

