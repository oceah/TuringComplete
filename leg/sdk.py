import re

_re_labeldef = re.compile(r'^label\s+([A-Za-z_]\w*)\s*:$')
_re_jxx = re.compile(r'^(J[A-Z]*)\s+(.+?)\s*((?:,\s*.+?\s*)*)$')

from .asm import ASM, _re_asmdef

_asm_config = 'leg/asm_config'
_asm = ASM(_asm_config)

def compile(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    lines = []
    for raw in raw_lines:
        line = raw.split(';', 1)[0].strip()
        if not line:
            continue
        for sh in _asm.macro(line):
            lines.append(sh)

    labels = {}
    pc = 0
    for line in lines:
        m = _re_labeldef.match(line)
        if m:
            name = m.group(1)
            if name in labels:
                raise ValueError(f'Duplicate label: {name}')
            labels[name] = pc
            continue
        pc += 4

    raw_lines = lines
    lines = []
    pc = 0
    for line in raw_lines:
        if _re_labeldef.match(line):
            continue
        # repalce label
        m = _re_jxx.match(line)
        if m:
            label = m.group(2)
            if label in labels:
                label = labels[label]
            elif label.startswith('$'):
                label = label.replace('$', str(pc))
                label = eval(label)
            line = f'{m.group(1)} {label} {m.group(3)}'
        shs = _asm.macro(line)
        if len(shs) != 1:
            raise RuntimeError(f"sdk.cl(): bad macro from \"{line}\" to \"{shs}\"")
        line = shs[0]
        lines.append(line)
        pc += 4

    program = []
    for sh in lines:
        ins, addr0, addr1, addr2 = _asm.encode(sh)
        program.append(ins)
        program.append(addr0)
        program.append(addr1)
        program.append(addr2)
    return program

def _load_asm_config(path: str) -> dict[int, str]:
    code2s = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        m = _re_asmdef.match(line)
        if not m:
            continue
        ins = m.group(1)
        code = int(m.group(2), 0)
        if code not in code2s:
            code2s[code] = [ins]
    return code2s

_code2s = _load_asm_config(_asm_config)

def decompile(sh: tuple[int, int, int, int]) -> str:
    def geti(code: int) -> str:
        if code in _code2s:
            return _code2s[code][0]
        return str(code)
    def geta(addr: int, io: str) -> str:
        if addr < 6:
            return f'R{addr}'
        if addr == 6:
            return 'PC'
        if addr == 7:
            return io
        return str(addr)

    raw_ins, x, y, z = sh
    x = f'#{x}' if raw_ins & 0x80 else geta(x, 'RI')
    y = f'#{y}' if raw_ins & 0x40 else geta(y, 'RI')
    ins = geti(raw_ins & 0x3f)
    z = str(z) if ins.startswith('J') else geta(z, 'RO')

    if ins in ['ADD', 'SUB', 'AND', 'OR', 'XOR']:
        if z == x:
            return f'{ins} {z}, {y}'
        if ins != 'SUB' and z == y:
            return f'{ins} {z}, {x}'
    if ins == 'ADD':
        if y == '#0':
            return f'MOV {z}, {x}'
        if x == z and y == '#1' or x == '#1' and y == z:
            return f'INC {z}'
    elif ins == 'SUB':
        if x == z and y == '#1':
            return f'DEC {z}'
    elif ins.startswith('J'):
        if raw_ins & 0x80 and raw_ins & 0x40:
            x = int(x[1:], 0)
            y = int(y[1:], 0)
            if ins == 'JE':
                c = x == y
            elif ins == 'JNE':
                c = x != y
            elif ins == 'JL':
                c = x < y
            elif ins == 'JLE':
                c = x <= y
            elif ins == 'JG':
                c = x > y
            elif ins == 'JGE':
                c = x >= y
            return f'JMP {z}' if c else 'NOP'
        if ins == 'JE' or ins == 'JNE':
            if x == '#0':
                return f'{ins} {z}, {y}'
            if y == '#0':
                return f'{ins} {z}, {x}'

    return f'{ins} {z}, {x}, {y}'

def run(path: str, input: list[int] = [], encoding: str = 'd', log: bool = False):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    program = []
    for i in range(len(lines) // 4):
        ins = int(lines[i * 4])
        addr0 = int(lines[i * 4 + 1])
        addr1 = int(lines[i * 4 + 2])
        addr2 = int(lines[i * 4 + 3])
        program.append((ins, addr0, addr1, addr2))
    _asm.reset()
    i = 0
    pout = []
    while _asm.pc // 4 < len(program):
        if _asm.fi and i < len(input):
            _asm.ri = input[i]
            i += 1
        ins, addr0, addr1, addr2 = program[_asm.pc // 4]
        _asm.machine.step(ins, addr0, addr1, addr2)
        if log:
            print(f'{decompile((ins, addr0, addr1, addr2))} -> {str(_asm)}')
        out = _asm.ro
        if out is not None:
            if encoding == 'x':
                pout.append(f'0x{format(out, '02x')}')
            elif encoding == 'd':
                pout.append(format(out, 'd'))
            elif encoding == 'b':
                pout.append(f'0b{format(out, '08b')}')
            elif encoding == 'utf-8':
                pout.append(chr(out))
    if pout:
        sep = '' if encoding == 'utf-8' else ' '
        print(sep.join(pout))
