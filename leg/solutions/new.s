const left = 0
const forward = 1
const right = 2
const skip = 3
const enter = 4

MOV RO, #right
MOV RO, #forward
MOV RO, #right
MOV RO, #forward
MOV RO, #forward
MOV RO, #forward
MOV RO, #forward
MOV RO, #right
MOV RO, #forward
MOV RO, #left
MOV RO, #forward

label loop:
    MOV R0, RI
    JE next_loop, R0, #92
    LDR R1, R0
    JNE same, R1
    STR R0, #1
    JMP next_loop
    label same:
        MOV RO, #right
        MOV RO, #enter
        MOV RO, #left
        JMP loop
    label next_loop:
        MOV RO, #skip
        JMP loop
