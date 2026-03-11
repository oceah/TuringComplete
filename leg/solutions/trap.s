const n = 16

MOV R0, #0
label cin:
    STR R0, RI
    INC R0
    JL cin, R0, #n

MOV R0, #0      ; rain_water
MOV R1, #0      ; left
MOV R2, #n - 1  ; right
STR #n, #0      ; left_max
STR #n + 1, #0  ; right_max

label loop:
    JGE return, R1, R2
    LDR R3, R1 ; height[left]
    LDR R4, R2 ; height[right]
    JGE hl_ge_hr, R3, R4
    ; if height[left] < height[right]:
        LDR R5, #n ; left_max
        JGE $ + 8, R5, R3
        MOV R5, R3
        STR #n, R5
        SUB R5, R3
        ADD R0, R5
        INC R1
        JMP loop
    label hl_ge_hr:
        LDR R5, #n + 1 ; right_max
        JGE $ + 8, R5, R4
        MOV R5, R4
        STR #n + 1, R5
        SUB R5, R4
        ADD R0, R5
        DEC R2
        JMP loop

label return:
    MOV RO, R0
