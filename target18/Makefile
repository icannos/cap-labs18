#! /usr/bin/make -f

all:	
	python3 matmulstat/makematrix.py
	(cd prog; make all)
	(cd emu; make emu)
	(cd chip8; make)

clean:
	(cd prog; make clean)
	(cd emu; make distclean)
	$(RM) *.bytes *.huff
