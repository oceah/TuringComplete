JMP begin

; R0: disk_nr
; R1: source
; R2: dest
; R3: spare
label move:
    JNE move_dir_nr_is_not_0, R0
    ; disk_nr is 0
        ; move disk from source to dest
        MOV RO, R1
        MOV RO, #5
        MOV RO, R2
        MOV RO, #5
        RET    
    label move_dir_nr_is_not_0:
        ; move(disk_nr - 1, source, spare, dest)
        DEC R0
        XCH R2, R3
        CALL move
        INC R0
        XCH R2, R3
        ; move disk from source to dest
        MOV RO, R1
        MOV RO, #5
        MOV RO, R2
        MOV RO, #5
        ; move(disk_nr - 1, spare, dest, source)
        DEC R0
        XCH R1, R3
        CALL move
        INC R0
        XCH R1, R3
        RET

label begin:
    MOV R0, RI
    MOV R1, RI
    MOV R2, RI
    MOV R3, RI
    CALL move
