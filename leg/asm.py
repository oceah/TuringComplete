from .machine import Machine

import re

_re_asmdef = re.compile(r'^\s*(.+?)\s*=\s*(.+?)\s*$')
_re_sh4 = re.compile(r"^([A-Z][A-Z0-9_]*?)\s+([^,]+?)\s*,\s*('.*?'|[^,]+?)\s*,\s*('.*?'|[^,]+?)$")
_re_sh3 = re.compile(r"^([A-Z][A-Z0-9_]*?)\s+('.*?'|[^,]+?)\s*,\s*('.*?'|[^,]+?)$")
_re_sh2 = re.compile(r"^([A-Z][A-Z0-9_]*?)\s+('.*?'|[^,]+?)$")

def _load_asm_config(path: str) -> dict[str, int]:
    s2code = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        m = _re_asmdef.match(line)
        if not m:
            continue
        ins = m.group(1)
        code = int(m.group(2), 0)
        s2code[ins] = code
    return s2code

class ASM:
    def __init__(self, asm_config: str):
        self._machine = Machine()
        self._s2code = _load_asm_config(asm_config)

    def reset(self):
        self._machine.reboot()

    def __str__(self) -> str:
        return str(self._machine)
    
    # region proerty
    @property
    def pc(self) -> int:
        return self._machine.pc
    @property
    def ri(self) -> int | None:
        return self.machine.ri
    @ri.setter
    def ri(self, value):
        self.machine.ri = value
    @property
    def fi(self) -> bool:
        return self._machine.fi
    @property
    def ro(self) -> int | None:
        return self.machine.ro
    @property
    def machine(self) -> Machine:
        return self._machine
    # endregion

    @staticmethod
    def macro(sh: str) -> list[str]:
        def try_eval(s: str) -> str:
            if any(c in s for c in "+-*/%()"):
                try:
                    if s.startswith('#'):
                        return f'#{eval(s[1:])}'
                    return eval(s)
                except:
                    pass
            return s
        m = _re_sh4.match(sh)
        if m:
            ins = m.group(1)
            z = m.group(2)
            x = try_eval(m.group(3))
            y = try_eval(m.group(4))
            if ins == 'NAND':
                return [
                    f'AND {z}, {x}, {y}',
                    f'NOT {z}'
                ]
            if ins == 'NOR':
                return [
                    f'OR {z}, {x}, {y}',
                    f'NOT {z}'
                ]
            if ins == 'XNOR':
                return [
                    f'XOR {z}, {x}, {y}',
                    f'NOT {z}'
                ]
        m = _re_sh3.match(sh)
        if m:
            ins = m.group(1)
            z = m.group(2)
            x = try_eval(m.group(3))
            if ins in ['ADD', 'AND', 'OR', 'XOR']:
                return [f'{ins} {z}, {z}, {x}']
            if ins == 'NEG':
                return [f'SUB {z}, #0, {x}']
            if ins == 'MOV':
                return [f'ADD {z}, {x}, #0']
            if ins == 'NOT':
                return [f'NOT {z}, {x}, 0']
            if ins == 'XCH':
                return [
                    f'XOR {z}, {x}, {z}',
                    f'XOR {x}, {z}, {x}',
                    f'XOR {z}, {x}, {z}',
                ]
            if ins in ['JE', 'JNE']:
                return [f'{ins} {z}, {x}, #0']
        m = _re_sh2.match(sh)
        if m:
            ins = m.group(1)
            z = try_eval(m.group(2))
            if ins == 'NEG':
                return [f'SUB {z}, #0, {z}']
            if ins == 'INC':
                return [f'ADD {z}, {z}, #1']
            if ins == 'DEC':
                return [f'SUB {z}, {z}, #1']
            if ins == 'NOT':
                return [f'NOT {z}, {z}, 0']
            if ins == 'JMP':
                return [f'JE {z}, #0, #0']
        return [sh]

    def encode(self, sh: str) -> tuple[int, int, int, int]:
        def get_code(s: str):
            if s in self._s2code:
                return self._s2code[s]
            if s.startswith('#'):
                s = s[1:]
            if s.startswith("'"):
                return ord(s[1:-1])
            return int(s, 0)
        def is_imm(s: str):
            return s.startswith('#') or s.startswith("'")

        m = _re_sh4.match(sh)
        if not m:
            raise ValueError(f"ASM.compile(): bad sh '{sh}'")
        ins = get_code(m.group(1))
        z = get_code(m.group(2))
        raw_x = m.group(3)
        x = get_code(raw_x)
        if is_imm(raw_x):
            ins |= 0x80
        raw_y = m.group(4)
        y = get_code(raw_y)
        if is_imm(raw_y):
            ins |= 0x40
        return ins, x, y, z

    def step(self, sh: str):
        shs = self.macro(sh)
        for sh in shs:
            ins, addr0, addr1, addr2 = self.encode(sh)
            self._machine.step(ins, addr0, addr1, addr2)

def run_terminal(asm: ASM):
    re_in = re.compile(r'^in\s+(.+?)$')

    print('ASM terminal. Type exit to quit.')
    print(asm)
    while True:
        try:
            line = input('> ').strip()
        except (KeyboardInterrupt):
            print('^C')
            break
        if not line:
            continue
        if line.lower() == "exit":
            break
        try:
            m = re_in.match(line)
            if m:
                value = int(m.group(1), 0)
                asm.ri = value
                continue
            asm.step(line)
        except Exception as e:
            print(e)
        print(asm)

if __name__ == '__main__':
    run_terminal(ASM('leg/asm_config'))
