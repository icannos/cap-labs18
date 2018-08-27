#! /usr/bin/env python3

from sys import stdin

entree = stdin.read()
data = list(map(float,entree.split("&")[:-1]))

print("& " + str(int(data[0])),end=" ")

for elt in data[1:]:
    print("& {0:3.2f}\\% ".format((elt/data[0])*100),end="")

print("\\\\")
