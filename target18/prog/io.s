;-----------------------------------------------------------------------------;
;  Some input/output                                                          ;
;-----------------------------------------------------------------------------;

	let	r0 126

	print	char r0
	print	char '\n'

	print	signed r0
	print	char '\n'

	print	unsigned r0
	print	char '\n'

	lea	r0 str
	print	string r0

	print	char 126
	print	char '\n'

	print	unsigned '0'
	print	char '\n'

; Halt program (the emulator will detect this and avoid looping forever)
halt:
	jump	-13

str:
	.string "Hello, World!\n"
