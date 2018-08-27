grammar Arit2;

// MIF08@Lyon1 and CAP@ENSL, arit evaluator

// Header in Python, comment it out to use grun
@header {
# header - mettre les variables globales 
import sys
idTab = {};
    
class UnknownIdentifier(Exception):
    pass
}

prog: ID {print("prog = "+str($ID.text));} ;


COMMENT
 : '#' ~[\r\n]* -> skip
 ;

ID : ('a'..'z'|'A'..'Z')+;
WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines
INT: '0'..'9'+;
NEWLINE: [\n]+;
