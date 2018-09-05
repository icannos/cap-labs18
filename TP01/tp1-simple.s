lea r1 data
setctr a1 r1
readse a1 8 r2
print signed r2

halt:
    jump halt

data:
    .const 8 #00000111
