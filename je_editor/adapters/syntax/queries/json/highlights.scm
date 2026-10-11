; Added after the grammar's own highlight query. A later pattern wins over an
; earlier one on the same node.

; The grammar's query was written for the opposite precedence: it names the key
; first and every string second, which under "later wins" paints a key as a plain
; string. Naming the key again here puts it back.
(pair
  key: (string) @string.special.key)
