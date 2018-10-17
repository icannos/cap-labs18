PACKAGE = Mu
MAINFILE = Main
TESTFILE?=tests/step1/test01.mu
ASM=$(TESTFILE:%.mu=%.s)
OBJ=$(TESTFILE:%.mu=%.obj)
TRACE=$(TESTFILE:%.mu=%.trace)
SIMU=../../../target18/asm2017/emu/emu
ASSEMBLER=../../../target18/asm2017/asm.py
MYNAME=AlanTuring

ifndef ANTLR4
abort:
	$(error variable ANTLR4 is not set)
endif


all: antlr run

antlr: $(PACKAGE).g4 
	$(ANTLR4) $< -Dlanguage=Python3 -visitor -no-listener

.PHONY: run
run: $(ASM)
$(ASM): ${wildcard *.py} $(TESTFILE)
	python3 $(MAINFILE).py $(TESTFILE)

$(OBJ): $(ASM)
	python3 $(ASSEMBLER) $<

.PHONY: trace
trace: $(TRACE)
	cat $<
$(TRACE): $(OBJ) $(SIMU)
	$(SIMU) q $(OBJ) >$@

$(SIMU):
	cd $(dir $(SIMU)) && $(MAKE)

clean:
	rm -rf *~ $(PACKAGE)Lexer* $(PACKAGE)Parser* *.pyc *.tokens  __pycache* .cache/ *.interp
	rm -f tests/step1/*.s tests/step1/*.bin
	rm -f tests/step2/*.s tests/step2/*.bin
	rm -f tests/mine/*.s tests/mine/*.bin


../../TP03/Mu-evalntype/MuParser.py:
	make -C ../../TP03/Mu-evalntype/

../../target18/asm.py:
	make -C ../../leia/simulateur/


tests: ../../TP03/Mu-evalntype/MuParser.py ../../target18/asm.py antlr
	python3 -m pytest -v -rs ./test_codegen.py


tar: clean
	cd ..; tar cvfz $(MYNAME).tgz Mu-codegen/ --transform 's/Mu-codegen/$(MYNAME)/' --exclude='Mu-codegen/tests/step*'
