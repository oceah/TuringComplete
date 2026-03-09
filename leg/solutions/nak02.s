JMP begin

; R0 = mod(R0, R1) = R0 % R1
label mod:
    label div_loop:
        JL div_end, R0, R1
        SUB R0, R1
        JMP div_loop
    label div_end:
        RET

label begin:
    MOV R0, RI
    MOV R1, #4
    CALL mod
    JE mod4_2, R0, #2
    JE mod4_3, R0, #3
    label mod4_0:
        MOV RO, #3
        JMP begin
    label mod4_2:
        MOV RO, #1
        JMP begin
    label mod4_3:
        MOV RO, #2
        JMP begin
