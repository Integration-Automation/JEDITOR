; Added after the grammar's own highlight query. A later pattern wins over an
; earlier one on the same node.

; The receiver of a method keeps the colour the editor has always given it.
((identifier) @variable.builtin
 (#match? @variable.builtin "^(self|cls)$"))
