grammar Mu;

prog: vardecl_l block EOF #progRule;

vardecl_l: vardecl* #varDeclList;

vardecl: VAR id_l COL typee SCOL #varDecl;

id_l
    : ID              #idListBase
    | ID COM id_l     #idList
    ;

block: stat*   #statList;

stat
    : assignment
    | if_stat
    | while_stat
    | log   
    | OTHER {print("unknown char: {}".format($OTHER.text))}
    ;

assignment: ID ASSIGN expr SCOL #assignStat;

if_stat: IF condition_block (ELSE IF condition_block)* (ELSE stat_block)? #ifStat;

condition_block: expr stat_block  #condBlock;

stat_block
    : OBRACE block CBRACE
    | stat
    ;

while_stat: WHILE expr stat_block #whileStat;


log: LOG expr SCOL #logStat;

expr
    : <assoc=right> expr POW expr          #powExpr
    | MINUS expr                           #unaryMinusExpr
    | NOT expr                             #notExpr
    | expr myop=(MULT|DIV|MOD)  expr       #multiplicativeExpr
    | expr myop=(PLUS|MINUS) expr          #additiveExpr
    | expr myop=(GT|LT|GTEQ|LTEQ)  expr    #relationalExpr
    | expr myop=(EQ|NEQ) expr              #equalityExpr
    | expr AND expr                        #andExpr
    | expr OR expr                         #orExpr
    | atom                                 #atomExpr
    ;

atom
    : OPAR expr CPAR #parExpr
    | (INT | FLOAT)  #numberAtom
    | (TRUE | FALSE) #booleanAtom
    | ID             #idAtom
    | STRING         #stringAtom
    | NIL            #nilAtom
    ;

typee
    : mytype=(INTTYPE|FLOATTYPE|BOOLTYPE|STRINGTYPE) #basicType
    ;

OR : '||';
AND : '&&';
EQ : '==';
NEQ : '!=';
GT : '>';
LT : '<';
GTEQ : '>=';
LTEQ : '<=';
PLUS : '+';
MINUS : '-';
MULT : '*';
DIV : '/';
MOD : '%';
POW : '^';
NOT : '!';

COL: ':';
SCOL : ';';
COM : ',';
ASSIGN : '=';
OPAR : '(';
CPAR : ')';
OBRACE : '{';
CBRACE : '}';

TRUE : 'true';
FALSE : 'false';
NIL : 'nil';
IF : 'if';
ELSE : 'else';
WHILE : 'while';
LOG : 'log';
VAR : 'var';

INTTYPE: 'int';
FLOATTYPE: 'float';
STRINGTYPE: 'string';
BOOLTYPE : 'bool';

ID
 : [a-zA-Z_] [a-zA-Z_0-9]*
 ;

INT
 : [0-9]+
 ;

FLOAT
 : [0-9]+ '.' [0-9]* 
 | '.' [0-9]+
 ;

STRING
 : '"' (~["\r\n] | '""')* '"'
 ;

COMMENT
 : '#' ~[\r\n]* -> skip
 ;

SPACE
 : [ \t\r\n] -> skip
 ;

OTHER
 : . 
 ;
