#! /usr/bin/env python3
import subprocess
from random import randrange,random

WS = 64 #word size 
DS = 0.1 # density of nonnegative in the matrix
NM = 50#number of matrices

base = """
0111 000 110{0:032b}
0111 001 110{1:032b}
0111 011 10{2:08b}
0111 100 10{3:08b}
0111 101 10{4:08b}
0111 110 110{5:032b}
"""

command = "../emu/emu --text -s /tmp/output.obj --geometry 16k:16k:2M:327680 --load 10000:/tmp/mat.obj"
 

f = open("matmodel.obj")
queue = f.read()
f.close()

def extract_num(ch):
    """extracts string from data"""
    first = ch.find("|")
    last = ch.find("|",first+1)
    return int(ch[first+1:last])
    
def gen_matrice(row,col):
    """returns the memory binary representation of a random row x col matrix"""
    rpmat = bytes()
    for i in range(row*col):
        rpmat += (randrange(1<<WS)*(random()<DS)).to_bytes(WS//4,byteorder='big')
    return rpmat

for i in range(1,NM):
    #creates the matrix
    
    filemat = open("/tmp/mat.obj","wb")
    filemat.write(gen_matrice(i,i))
    filemat.close()
    #make the code
    sortie = open("/tmp/output.obj","w")
    sortie.write(base.format(0x10000,0x10000+i*i*WS,i,i,i,0x10000+2*i*i*WS)
                 +queue)
    sortie.close()
    #execute it
    process = subprocess.Popen(command.split(),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output,error = process.communicate()
    #treat the output
    data = str(output).split('\\n')
    print(str(i) + "; " +
          "; ".join(list(map(lambda x:str(extract_num(x)),data[????]))))
    
