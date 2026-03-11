JMP main

; R0 = rand(R0: seed)
label rand:
    PUSH R1
    ; temp1 = seed xor (seed shr 1)
    SHR R1, R0, #1
    XOR R0, R1
    ; temp2 = temp1 xor (temp1 shl 1)
    SHL R1, R0, #1
    XOR R0, R1
    ; next_seed = temp2 xor (temp2 shr 2)
    SHR R1, R0, #2
    XOR R0, R1
    POP R1
    RET

; R0 = mod(R0, R1) = R0 % R1
label mod:
    label div_loop:
        JL div_end, R0, R1
        SUB R0, R1
        JMP div_loop
    label div_end:
        RET

label main:
    MOV R0, RI
    label loop:
        CALL rand
        MOV R1, #4
        PUSH R0
        CALL mod
        MOV RO, R0
        POP R0
        JMP loop
