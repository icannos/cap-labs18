var x:int;
var f, s:float;
var b : bool;

x=42;
f=3.8;
s=x*f;
b = s > " blabla";
log (b);

# EXPECTED
# Line 8 col 4: invalid type for relational operands: float and string
# EXITCODE 1
