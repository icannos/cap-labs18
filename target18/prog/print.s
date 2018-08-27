;;;  bug ?
;; stack management
lea r6 stack
        leti r1 10
        sub3i r0 r6 0
        setctr a0 r0
	print unsigned r0
        write a0 16 r1
	print signed r1
        leti r2 14
        sub3i r0 r6 16
        setctr a0 r0
	print unsigned r0
	print signed r2
        write a0 16 r2
	print signed 42
	print signed r2		; n'imprime pas.
;;postlude
stackend:
.const 4242 #0
stack:
