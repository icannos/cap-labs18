leti r1 7
leti r2 7
cmp r1 r2
jumpif sge ge_label
end:
jump end

ge_label:
lea r0 ge_string
print string r0
jump end

ge_string:
	.string "s Greater or equal"