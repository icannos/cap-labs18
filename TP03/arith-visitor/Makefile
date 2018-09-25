PACKAGE = Arit
MAINFILE = arit

ifndef ANTLR4
abort:
	$(error variable ANTLR4 is not set)
endif

all: $(PACKAGE).g4
	$(ANTLR4) $^ -Dlanguage=Python3 -visitor

run: $(MAINFILE).py
	python3 $^

ex: $(MAINFILE).py
	python3 $^ < myexample

clean:
	rm -rf *~ $(PACKAGE)*.py *.pyc *.tokens  __pycache* *.interp
