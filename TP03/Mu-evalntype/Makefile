PACKAGE = Mu
MAINFILE = Main
#change with your own name:
MYNAME = JohnDoe

TESTFILE?=ex/test00.mu

ifndef ANTLR4
abort:
	$(error variable ANTLR4 is not set)
endif

all: run

MuLexer.py MuParser.py: $(PACKAGE).g4
	$(ANTLR4) $< -Dlanguage=Python3 -visitor -no-listener

main-deps: MuLexer.py MuParser.py MuEvalVisitor.py MuTypingVisitor.py

run: $(MAINFILE).py main-deps
	python3  $< $(TESTFILE)

# tests all files in ex/test*.mu
tests: test_evaluator.py main-deps
	python3 -m pytest -v $< 

BASEDIR=${shell pwd | xargs basename}
tar: clean
	cd ..; tar cvfz $(MYNAME).tgz $(BASEDIR) --transform 's/$(BASEDIR)/$(MYNAME)/'
	@echo "Created ../$(MYNAME).tgz"

clean:
	rm -rf *~ $(PACKAGE)Parser.py $(PACKAGE)Lexer.py $(PACKAGE)Visitor.py *.pyc *.tokens  __pycache* ex/*~ .cache* ex-types/*~ *.interp
