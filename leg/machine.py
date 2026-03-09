class ALU:
    def __init__(self):
        self._i2f = {
            0b000: lambda a, b: (a + b) & 0xff,
            0b001: lambda a, b: (a - b) & 0xff,
            0b010: lambda a, b: a & b,
            0b011: lambda a, b: a | b,
            0b100: lambda a, _: ~a & 0xff,
            0b101: lambda a, b: a ^ b,
        }

    def __call__(self, ins: int, a: int, b: int) -> int:
        return self._i2f[ins & 0b111](a, b)

class BU:
    def __init__(self):
        self._i2f = {
            0b000: lambda a, b: a == b,
            0b001: lambda a, b: a != b,
            0b010: lambda a, b: a < b,
            0b011: lambda a, b: a <= b,
            0b100: lambda a, b: a > b,
            0b101: lambda a, b: a >= b,
        }

    def __call__(self, ins: int, a: int, b: int) -> bool:
        return self._i2f[ins & 0b111](a, b)

class RAM:
    def __init__(self):
        self._ram = [0 for _ in range(256)]

    def __call__(self, ins: int, addr: int, value = None) -> int | None:
        addr &= 0xff
        if ins & 1 == 0:
            return self._ram[addr]
        else:
            self._ram[addr] = value & 0xff

class STK:
    def __init__(self):
        self._stk = []

    def reboot(self):
        self._stk.clear()

    def __call__(self, ins: int, value: int = None) -> int | None:
        if ins & 1 == 0: # POP
            if len(self._stk) == 0:
                raise RuntimeError('STK.__call__(): pop empty stack')
            return self._stk.pop()
        else: # PUSH
            self._stk.append(value & 0xff)

class Machine:
    def __init__(self):
        self._r = [0 for _ in range(6)]
        self._pc = 0
        self._fi = True
        self._ri = None
        self._ro = None

        self._alu = ALU()
        self._bu = BU()
        self._ram = RAM()
        self._stk = STK()

    def reboot(self):
        for i in range(6):
            self._r[i] = 0
        self._pc = 0
        self._fi = True
        self._ri = None
        self._ro = None

        self._stk.reboot()

    def __str__(self) -> str:
        return " ".join([
            *[f'R{i}={self._r[i]}' for i in range(6)],
            f'PC={self._pc}',
            f"RO={'Z' if self._ro is None else self._ro}",
        ])

    # region property
    @property
    def r0(self):
        return self._r[0]
    @property
    def r1(self):
        return self._r[1]
    @property
    def r2(self):
        return self._r[2]
    @property
    def r3(self):
        return self._r[3]
    @property
    def r4(self):
        return self._r[4]
    @property
    def r5(self):
        return self._r[5]
    @property
    def pc(self):
        return self._pc
    @property
    def ri(self):
        return self._ri
    @ri.setter
    def ri(self, value: int | None):
        self._ri = value & 0xff if isinstance(value, int) else None
        self._fi = False
    @property
    def fi(self) -> bool:
        return self._fi
    @property
    def ro(self):
        return self._ro
    # endregion

    def _getv(self, addr: int):
        if addr < 6:
            return self._r[addr]
        if addr == 6:
            return self.pc
        if addr == 7:
            self._fi = True
            return self.ri
        raise ValueError(f'Machine._getv(): bad addr {addr}')

    def _setv(self, addr: int, value):
        if addr < 6:
            self._r[addr] = value
        elif addr == 6:
            self._pc = value
        elif addr == 7:
            self._ro = value
        else:
            raise ValueError(f'Machine._setv(): bad addr {addr}')

    def step(self, ins: int, addr0: int, addr1: int, addr2: int):
        self._pc += 4
        self._ro = None
        a = addr0 if ins & 0x80 else self._getv(addr0)
        b = addr1 if ins & 0x40 else self._getv(addr1)
        if ((ins >> 3) & 0b111) == 0b000:
            c = self._alu(ins, a, b)
            self._setv(addr2, c)
        elif ((ins >> 3) & 0b111) == 0b100:
            if self._bu(ins, a, b):
                self._pc = addr2
        elif ((ins >> 2) & 0b1111) == 0b0100: # RAM
            if ins & 0b10 == 0: # RAM
                if ins & 1 == 0: # LDR
                    v = self._ram(ins, a)
                    self._setv(addr2, v)
                else: # STR
                    self._ram(ins, a, b)
            else: # STK
                if ins & 1 == 0: # POP
                    v = self._stk(ins)
                    self._setv(addr2, v)
                else: # PUSH
                    self._stk(ins, a)
        else:
            raise ValueError(f'Machine.step(): bad instruction {ins}')
