JMP main

label is_alpha:
    JL is_not_alpha, R0, 'a'
    JG is_not_alpha, R0, 'z'
    MOV R0, #1
    RET
    label is_not_alpha:
        MOV R0, #0
        RET

label is_space:
    JNE is_not_alpha, R0, ' '
    MOV R0, #1
    RET
    label is_not_space:
        MOV R0, #0
        RET

label main:
    MOV R1, RI
    MOV R0, R1
    CALL is_alpha
    JNE getchar_is_alpha, R0
        ; is not alpha
        MOV R0, R1
        CALL is_space
        JNE getchar_is_space, R0
            ; is not space
            JMP main_end
        label getchar_is_space:
            MOV R2, #0
            JMP main_end
    label getchar_is_alpha:
        JE is_first_alpha, R2
        JMP main_end
    label is_first_alpha:
        SUB R1, #32
        MOV R2, #1
    label main_end:
        MOV RO, R1
        JMP main
