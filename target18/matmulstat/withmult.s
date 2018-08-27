;------------------------------------------------------------------------------;
;                       Multiplication de Matrices                             ;
;                           Benchmark de test                                  ;
;------------------------------------------------------------------------------;
;;; le fichier a été compilé à partir de celui-ci, puis les 5 premières
;;; constantes ont été remplacées par @1 (16 fois) @2(16 fois) n(8 fois)
;;; p(8 fois) q(8 fois) Ainsi, le jeu de test pourra seulement remplacer
;;; ces caractères par des valeurs sans avoir à tout recompiler
	leti r0 100000
	leti r1 100000

	leti r3 127
	leti r4 127
	leti r5 127
	leti r6 0x10000	;on trouvera la multiplication ici
	call multmatrix

	leti r0 3
	leti r1 2
	leti r2 0x10000
	call blitmatrix

end:
	jump end

	;; matrice n*p : n*p cases consécutives de taille A(ici 64)
	;; les p premières lignes sont la ligne 1, les p suivantes 2…
	
	;; blitmarix : petit outil de debug : lit les cases de la matrice
	;; de taille r0*r1 en position r2 une à une et les met dans
	;; r4

	
blitmatrix:
	
	setctr a0 r2
	push 64 r7
	call multlibmult
	
	pop 64 r7
blitloop:
	readze a0 64 r0
	sub2i r2 1
	jumpif nz blitloop
	return

	;; multipliaction de matrices :
	;; r0 r1 r2 r3 r4 r5 r6 r7
	;; @0 @1 ?? n  p  q  @2
	;; écrit dans @2 la matrice produit de la matrice
	;; n*p en @0 et la matrice p*q en @1
	;; appel non-terminal ! besoin push/pop r7

	;; principe : conserver les constantes utiles sur la pile (A pour Arch)
	;; +-------+
	;; |   n   | Ces constantes serviront à réinitialiser les
	;; |  npA  | compteurs de boucle et déplacer les pointeurs
	;; |  nqA  |
	;; |   p   | une multiplication étant TRÈS coûteuse, on ne fait
	;; |  pqA  | ces opérations qu'une fois
	;; | (q-1)A|

	;; @0 et @1 sont stockées dans a0 et a1, @2 dans r6

	;; les constantes 6, 64 = 2**6, 192=3*64 dépendent de l'architecture 
	;; initialisation de la pile

	
multmatrix:
	setctr a0 r0
	setctr a1 r1
	push 64 r3

	let r0 r3
	let r1 r4
	push 64 r7
	call multlibmult
	pop 64 r7
	shift left r2 6
	push 64 r2
	let r1 r5
	push 64 r7
	call multlibmult
	pop 64 r7
	shift left r2 6
	push 64 r2

	push 64 r4

	let r0 r4
	
	;; on simule le fait d'avoir une multiplication dans l'ALU
	;; et les instructions. En vrai cela prendrait (instr) + 3*reg
	add2i r0 0 		
	
	shift left r2 6
	push 64 r2

	sub2i r1 1
	shift left r1 6
	push 64 r1

columns_loop:
lines_loop:
	leti r2 0
scalar_prod_loop:
	readze a0 64 r0
	readze a1 64 r1

	push 64 r7
	call multlibmult
	pop 64 r7

	getctr a1 r0
	pop 64 r1
	push 64 r1
	add2 r0 r1
	setctr a1 r0
	sub2i r4 1
	jumpif nz scalar_prod_loop

	getctr a1 r0
	setctr a1 r6
	write a1 64 r2

	pop 64 r1
	add2 r6 r1
	add2i r6 64
	pop 64 r2

	sub2 r0 r2
	setctr a1 r0

	pop 64 r4
	push 64 r4
	push 64 r2
	push 64 r1

	sub2i r3 1
	jumpif nz lines_loop

	add2i r0 64
	setctr a1 r0

	getctr sp r0
	add2i r0 192
	setctr sp r0

	pop 64 r1
	sub2 r6 r1
	add2i r6 64
	
	getctr a0 r3
	pop 64 r2

	sub2 r3 r2
	setctr a0 r3
	pop 64 r3
	push 64 r3
	push 64 r2
	push 64 r1
	sub2i r0 192
	setctr sp r0

	sub2i r5 1
	jumpif nz columns_loop

	return
	
multlibmult:
	;; r2 <- r1*r0
	;; r1, r0 remain
	push 64 r0
	push 64 r1
	leti r2 0
	push 64 r7
	call multlibsum
	pop 64 r7
	pop 64 r1
	pop 64 r0
	return

	;; r2 <- r2 + r1*r0
	;; r0, r1 destroyed
multlibsum:
	shift right r0 1
	jumpif nc multlibsk
	add2 r2 r1
multlibsk:
	shift left r1 1
	cmpi r0 0
	jumpif nz multlibsum
	return
