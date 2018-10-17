var x, y: int;
x = 42;
y = 66;
log x + y;
x = 0;
log x + y;
y = 0;
log x + y;
# EXPECTED
# 108
# 66
# 0
