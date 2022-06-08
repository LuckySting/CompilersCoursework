lexer grammar GoLexer;

// Keywords

BREAK                  : 'break' -> mode(NLSEMI);
DEFAULT                : 'default';
FUNC                   : 'func';
CASE                   : 'case';
MAP                    : 'map';
ELSE                   : 'else';
PACKAGE                : 'package';
CONST                  : 'const';
IF                     : 'if';
RANGE                  : 'range';
TYPE                   : 'type';
CONTINUE               : 'continue' -> mode(NLSEMI);
FOR                    : 'for';
RETURN                 : 'return' -> mode(NLSEMI);
VAR                    : 'var';

NIL_LIT                : 'nil' -> mode(NLSEMI);

IDENTIFIER             : LETTER (LETTER | UNICODE_DIGIT)* -> mode(NLSEMI);

// Punctuation

L_PAREN                : '(';
R_PAREN                : ')' -> mode(NLSEMI);
L_CURLY                : '{';
R_CURLY                : '}' -> mode(NLSEMI);
L_BRACKET              : '[';
R_BRACKET              : ']' -> mode(NLSEMI);
ASSIGN                 : '=';
COMMA                  : ',';
SEMI                   : ';';
COLON                  : ':';
PLUS_PLUS              : '++' -> mode(NLSEMI);
MINUS_MINUS            : '--' -> mode(NLSEMI);
DECLARE_ASSIGN         : ':=';
ELLIPSIS               : '...';

// Logical

LOGICAL_OR             : '||';
LOGICAL_AND            : '&&';

// Relation operators

EQUALS                 : '==';
NOT_EQUALS             : '!=';
LESS                   : '<';
LESS_OR_EQUALS         : '<=';
GREATER                : '>';
GREATER_OR_EQUALS      : '>=';

// Arithmetic operators

OR                     : '|';
DIV                    : '/';
MOD                    : '%';
LSHIFT                 : '<<';
RSHIFT                 : '>>';
BIT_CLEAR              : '&^';

// Unary operators

EXCLAMATION            : '!';

// Mixed operators

PLUS                   : '+';
MINUS                  : '-';
CARET                  : '^';
STAR                   : '*';
AMPERSAND              : '&';

// Number literals

DECIMAL_LIT            : ('0' | [1-9] ('_'? [0-9])*) -> mode(NLSEMI);
BINARY_LIT             : '0' [bB] ('_'? BIN_DIGIT)+ -> mode(NLSEMI);
OCTAL_LIT              : '0' [oO]? ('_'? OCTAL_DIGIT)+ -> mode(NLSEMI);
HEX_LIT                : '0' [xX]  ('_'? HEX_DIGIT)+ -> mode(NLSEMI);


FLOAT_LIT : (DECIMAL_FLOAT_LIT | HEX_FLOAT_LIT) -> mode(NLSEMI);

DECIMAL_FLOAT_LIT      : DECIMALS ('.' DECIMALS? EXPONENT? | EXPONENT)
                       | '.' DECIMALS EXPONENT?
                       ;

HEX_FLOAT_LIT          : '0' [xX] HEX_MANTISSA HEX_EXPONENT
                       ;

fragment HEX_MANTISSA  : ('_'? HEX_DIGIT)+ ('.' ( '_'? HEX_DIGIT )*)?
                       | '.' HEX_DIGIT ('_'? HEX_DIGIT)*;

fragment HEX_EXPONENT  : [pP] [+-]? DECIMALS;


IMAGINARY_LIT          : (DECIMAL_LIT | BINARY_LIT |  OCTAL_LIT | HEX_LIT | FLOAT_LIT) 'i' -> mode(NLSEMI);

// Rune literals

fragment RUNE               : '\'' (UNICODE_VALUE | BYTE_VALUE) '\'';//: '\'' (~[\n\\] | ESCAPED_VALUE) '\'';

RUNE_LIT                : RUNE -> mode(NLSEMI);



BYTE_VALUE : OCTAL_BYTE_VALUE | HEX_BYTE_VALUE;

OCTAL_BYTE_VALUE: '\\' OCTAL_DIGIT OCTAL_DIGIT OCTAL_DIGIT;

HEX_BYTE_VALUE: '\\' 'x'  HEX_DIGIT HEX_DIGIT;

LITTLE_U_VALUE: '\\' 'u' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT;

BIG_U_VALUE: '\\' 'U' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT;

// String literals

RAW_STRING_LIT         : '`' ~'`'*                      '`' -> mode(NLSEMI);
INTERPRETED_STRING_LIT : '"' (~["\\] | ESCAPED_VALUE)*  '"' -> mode(NLSEMI);

// Hidden tokens

WS                     : [ \t]+             -> channel(HIDDEN);
COMMENT                : '/*' .*? '*/'      -> channel(HIDDEN);
TERMINATOR             : [\r\n]+            -> channel(HIDDEN);
LINE_COMMENT           : '//' ~[\r\n]*      -> channel(HIDDEN);

fragment UNICODE_VALUE: ~[\r\n'] | LITTLE_U_VALUE | BIG_U_VALUE | ESCAPED_VALUE;

// Fragments

fragment ESCAPED_VALUE
    : '\\' ('u' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT
           | 'U' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT
           | [abfnrtv\\'"]
           | OCTAL_DIGIT OCTAL_DIGIT OCTAL_DIGIT
           | 'x' HEX_DIGIT HEX_DIGIT)
    ;

fragment DECIMALS
    : [0-9] ('_'? [0-9])*
    ;

fragment OCTAL_DIGIT
    : [0-7]
    ;

fragment HEX_DIGIT
    : [0-9a-fA-F]
    ;

fragment BIN_DIGIT
    : [01]
    ;

fragment EXPONENT
    : [eE] [+-]? DECIMALS
    ;

fragment LETTER
    : UNICODE_LETTER
    | '_'
    ;

mode NLSEMI;


// Treat whitespace as normal
WS_NLSEMI                     : [ \t]+             -> channel(HIDDEN);
// Ignore any comments that only span one line
COMMENT_NLSEMI                : '/*' ~[\r\n]*? '*/'      -> channel(HIDDEN);
LINE_COMMENT_NLSEMI : '//' ~[\r\n]*      -> channel(HIDDEN);
// Emit an EOS token for any newlines, semicolon, multiline comments or the EOF and
//return to normal lexing
EOS:              ([\r\n]+ | ';' | '/*' .*? '*/' | EOF)            -> mode(DEFAULT_MODE);
// Did not find an EOS, so go back to normal lexing
OTHER: -> mode(DEFAULT_MODE), channel(HIDDEN);