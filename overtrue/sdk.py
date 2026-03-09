import re

_re_labeldef = re.compile(r'^label\s+([A-Za-z_]\w*)\s*:$')
_re_constdef = re.compile(r'^const\s+([A-Za-z_]\w*)\s*=(.+)$')

from .asm import ASM, _re_asmdef, _re_sh2, _re_sh3

_asm_config = 'overtrue/asm.config'
_asm = ASM(_asm_config)

def compile(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    lines = []
    for line in raw_lines:
        line = line.split(';', 1)[0].strip()
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
        m = _re_constdef.match(line)
        if m:
            key = m.group(1)
            val = int(m.group(2), 0)
            if key in labels:
                raise ValueError(f'Duplicate label: {key}')
            labels[key] = val
            continue
        pc += 1

    program = []
    pc = 0
    for line in lines:
        if _re_labeldef.match(line):
            continue
        if _re_constdef.match(line):
            continue
        # replace label
        if line in labels:
            line = labels[line]
        else:
            m = _re_sh2.match(line)
            if m:
                ins = m.group(1)
                z = m.group(2)
                if z in labels:
                    z = f'{labels[z]}'
                line = f'{ins} {z}'
            else:
                m = _re_sh3.match(line)
                if m:
                    ins = m.group(1)
                    z = m.group(2)
                    x = m.group(3)
                    if z in labels:
                        z = f'#{labels[z]}'
                    if x in labels:
                        x = f'#{labels[x]}'
                    line = f'{ins} {z}, {x}'
            shs = _asm.macro(line)
            if len(shs) != 1:
                raise RuntimeError(f"bad macro from '{line}' to '{shs}'")
            line = shs[0]
            line = _asm.encode(line)
        program.append(line)
        pc += 1

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
            code2s[code] = ins
    return code2s

_code2s = _load_asm_config(_asm_config)

def decompile(sh: int) -> str:
    def geti(ins: int) -> str:
        if ins in _code2s:
            return _code2s[ins]
        return str(ins)
    def geta(addr: int, io: str) -> str:
        if addr < 6:
            return f'R{addr}'
        if addr == 6:
            return 'PC'
        if addr == 7:
            return io
        return str(addr)

    dec = (sh >> 6) & 0b11
    sh &= 0x3f
    if dec == 0b00:
        return f'MOV R0, #{sh}'
    elif dec == 0b01:
        sh |= 0x40
        return geti(sh)
    elif dec == 0b10:
        src = (sh >> 3) & 0b111
        dst = sh & 0b111
        src = geta(src, 'RI')
        dst = geta(dst, 'RO')
        return f'MOV {dst}, {src}'
    else:
        sh |= 0xc0
        return geti(sh)

def run(path: str, input: list[int] = [], encoding: str = 'd', log: bool = False):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    program = []
    for line in lines:
        if not line:
            continue
        line = int(line, 0)
        program.append(line)
    _asm.reset()
    i = 0
    pout = []
    while _asm.pc < len(program):
        if _asm.fi and i < len(input):
            _asm.ri = input[i]
            i += 1
        ins = program[_asm.pc]
        _asm.machine.step(ins)
        if log:
            print(f'{decompile(ins)} -> {str(_asm)}')
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
