import leg.sdk as sdk

def compile_and_run(
        asm_path: str, 
        input: list[int] | str = [], 
        encoding: str = 'd',
        log: bool = True
    ):
    exe_path = asm_path.split('.')[0]
    exe = sdk.compile(asm_path)
    with open(exe_path, 'w', encoding='utf-8') as f:
        for sh in exe:
            print(sh, file=f)
    sdk.run(exe_path, input, encoding, log)

# water world
compile_and_run('leg/solutions/trap.s', [0,1,0,2,1,0,1,3,2,1,2,1], encoding='d', log=True)
# upper case
compile_and_run('leg/solutions/upper.s', 'hello, world!', encoding='utf-8', log=True)
