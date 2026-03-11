import re

_re_in = re.compile(r'^in\s+(.+)$')
_re_asmdef = re.compile(r'^([A-Za-z_]\w*)\s*=\s*(\w+)$')
_re_ins = r'[A-Za-z_]\w*?'
_re_xyz = r'[^,]+?'
_re_sh2 = re.compile(rf"^({_re_ins})\s+({_re_xyz})$")
_re_sh3 = re.compile(rf"^({_re_ins})\s+({_re_xyz})\s*,\s*({_re_xyz})$")

from .machine import Machine

def _load_asm_config(path: str) -> dict[str, int]:
    s2code = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _re_asmdef.match(line)
        if m:
            ins = m.group(1)
            code = int(m.group(2), 0)
            s2code[ins] = code
    return s2code

class ASM:
    def __init__(self, asm_config: str):
        self._machine = Machine()
        self._s2code = _load_asm_config(asm_config)
        self._retx = 0

    def reset(self):
        self._machine.reset()
        self._retx = 0

    def __str__(self) -> str:
        return str(self._machine)

    # region property
    @property
    def pc(self) -> int:
        return self._machine.pc
    @property
    def fi(self) -> bool:
        return self._machine.fi
    @property
    def ri(self) -> int | None:
        return self._machine.ri
    @ri.setter
    def ri(self, value):
        self._machine.ri = value
    @property
    def ro(self) -> int | None:
        return self._machine.ro
    @property
    def machine(self) -> Machine:
        return self._machine
    # endregion

    def _macro(self, sh: str) -> str | list[str]:
        if sh == 'DEC':
            return [
                'MOV R2, #1',
                'SUB',
            ]
        if sh == 'INC':
            return [
                'MOV R2, #1',
                'ADD',
            ]
        if sh == 'NEG':
            return [
                'MOV R2, R1',
                'MOV R1, #0',
                'SUB',
            ]
        if sh == 'NOT':
            return [
                'MOV R2, R1',
                'NAND',
            ]
        if sh == 'RET':
            return [
                'POP R0',
                'JMP',
            ]
        if sh == 'XNOR':
            return [
                'AND',
                'MOV R0, R3',
                'NOR',
                'MOV R1, R0',
                'MOV R2, R3',
                'OR'
            ]
        if sh == 'XOR':
            return [
                'AND',
                'MOV R0, R3',
                'NOR',
                'MOV R1, R0',
                'MOV R2, R3',
                'NOR'
            ]
        m = _re_sh2.match(sh)
        if m:
            ins = m.group(1)
            z = m.group(2)
            if ins == 'CALL':
                label = f'__ret{self._retx}'
                self._retx += 1
                return [
                    f'PUSH #{label}',
                    f'JMP {z}',
                    f'label {label}:',
                ]
            if ins == 'PUSH' and z.startswith('#'):
                return [
                    f'MOV R0, {z}',
                    'PUSH R0',
                ]
            if ins.startswith('J'):
                return [z, ins]
        m = _re_sh3.match(sh)
        if m:
            ins = m.group(1)
            z = m.group(2)
            x = m.group(3)
            if ins == 'MOV' and x.startswith('#'):
                if z == 'R0':
                    return f'IMM {x[1:]}'
                return [
                    f'IMM {x[1:]}',
                    f'MOV {z}, R0'
                ]
        return sh
    def macro(self, sh: str) -> list[str]:
        stk = [sh]
        shs = []
        while stk:
            sh = stk.pop()
            shx = self._macro(sh)
            if isinstance(shx, str):
                shs.append(shx)
                continue
            for i in range(len(shx) - 1, -1, -1):
                stk.append(shx[i])
        return shs

    def encode(self, sh: str) -> int:
        def eval_xyz(x: str) -> int:
            if x.startswith('R'):
                if x[1] == 'I' or x[1] == 'O':
                    return 7
                return int(x[1:])
            if x == 'PC':
                return 6
            return int(eval(x))

        if sh in self._s2code:
            return self._s2code[sh]
        m = _re_sh2.match(sh)
        if m:
            ins = m.group(1)
            z = eval_xyz(m.group(2))
            if ins == 'IMM':
                if z > 0x7f:
                    raise ValueError(f"bad imm in '{sh}'")
                return z
            if ins == 'POP':
                if z > 0b111:
                    raise ValueError(f"bad pop in '{sh}'")
                return 0xd0 | z
            if ins == 'PUSH':
                if z > 0b111:
                    raise ValueError(f"bad push in '{sh}'")
                return 0xd8 | z
        m = _re_sh3.match(sh)
        if m:
            ins = m.group(1)
            z = eval_xyz(m.group(2))
            x = eval_xyz(m.group(3))
            if ins == 'MOV':
                if z > 0b111 or x > 0b111:
                    raise ValueError(f"bad mov in '{sh}'")
                return 0x80 | (x << 3) | z
        return int(sh, 0)

    def step(self, sh: str):
        shs = self.macro(sh)
        for sh in shs:
            sh = self.encode(sh)
            self._machine.step(sh)

def run_terminal(asm: ASM):
    print(asm)
    while True:
        try:
            sh = input('> ').strip()
        except (KeyboardInterrupt):
            print('^C')
            break
        if not sh:
            continue
        if sh.lower() == "exit":
            break
        try:
            m = _re_in.match(sh)
            if m:
                ri = int(eval(m.group(1)))
                asm.ri = ri
                continue
            asm.step(sh)
        except Exception as e:
            print(e)
        print(asm)

if __name__ == '__main__':
    run_terminal(ASM('overtrue/asm.config'))
