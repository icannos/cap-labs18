PACKAGE = Mu
DIR = $(shell basename $(PWD))
MAINFILE = Main
TESTFILE?=tests/test00.mu
ASM=$(TESTFILE:%.mu=%.s)
OBJ=$(TESTFILE:%.mu=%.obj)
TRACE=$(TESTFILE:%.mu=%.trace)
SIMU = ../../target18/emu/emu
ASSEMBLER=../../../target18/asm2017/asm.py
MYNAME=AlanTuring

ifndef ANTLR4
abort:
	$(error variable ANTLR4 is not set)
endif


all: antlr run

antlr: $(PACKAGE).g4 
	$(ANTLR4) $< -Dlanguage=Python3 -visitor -no-listener

.PHONY: run $(ASM)
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
	rm -f tests/*.s tests/*.dot tests/*.dot.pdf tests/*.obj
	rm -f testsdataflow/*.s testsdataflow/*.dot
	rm -f testsdataflow/*.dot.pdf testsdataflow/*.obj


../../TP03/Mu-evalntype/MuParser.py:
	make -C ../../TP03/Mu-evalntype/

tests: ../../TP03/Mu-evalntype/MuParser.py $(SIMU) antlr
	python3 -m pytest -v -rs ./test_smartcodegen.py


tar: clean
	cd ..; tar cvfz $(MYNAME).tgz $(DIR) --transform 's/Mu-codegen/$(MYNAME)/'
	@echo "Created ../$(MYNAME).tgz"
