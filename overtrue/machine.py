class ALU:
    def __init__(self):
        self._i2f = {
            0b000: lambda a, b: a | b, # OR
            0b001: lambda a, b: ~(a & b) & 0xff, # NAND
            0b010: lambda a, b: ~(a | b) & 0xff, # NOR
            0b011: lambda a, b: a & b, # AND
            0b100: lambda a, b: (a + b) & 0xff, # ADD
            0b101: lambda a, b: (a - b) & 0xff, # SUB
            0b110: lambda a, b: (a << b) & 0xff, # SHL
            0b111: lambda a, b: a >> b, # SHR
        }

    def __call__(self, ins: int, a: int, b: int) -> int:
        return self._i2f[ins & 0x3f](a, b)

class BU:
    def __init__(self):
        self._i2f = {
            0b000: lambda _: False,
            0b001: lambda a: a == 0,
            0b010: lambda a: a & 0x80, # <0
            0b011: lambda a: a & 0x80 or a == 0, # <=0
            0b100: lambda _: True,
            0b101: lambda a: a != 0,
            0b110: lambda a: not (a & 0x80), # >=0
            0b111: lambda a: not (a & 0x80) and a != 0, # >0
        }

    def __call__(self, ins: int, a: int) -> bool:
        return self._i2f[ins & 0b111](a)

class STK:
    def __init__(self):
        self._stk = []

    def reboot(self):
        self._stk.clear()

    def __call__(self, ins: int, value: int = None) -> int | None:
        if ins & 0b1000: # PUSH
            self._stk.append(value & 0xff)
        else: # POP
            if len(self._stk) == 0:
                raise RuntimeError('STK.__call__(): pop empty stack')
            return self._stk.pop()

class Machine:
    def __init__(self):
        self._r = [0 for _ in range(6)]
        self._pc = 0
        self._fi = True
        self._ri = None
        self._ro = None

        self._alu = ALU()
        self._bu = BU()
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
    def pc(self) -> int:
        return self._pc
    @property
    def ri(self) -> int | None:
        return self._ri
    @ri.setter
    def ri(self, value):
        self._ri = value
    @property
    def ro(self) -> int | None:
        return self._ro
    @property
    def fi(self) -> bool:
        return self._fi
    # endregion

    def _getv(self, addr: int):
        if addr < 6:
            return self._r[addr]
        if addr == 6:
            return self._pc
        if addr == 7:
            self._fi = True
            return self._ri
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

    def step(self, ins: int):
        self._pc += 1
        self._ro = None
        if (ins >> 6) & 0b11 == 0b00: # IMM
            self._setv(0, ins & 0x3f)
        elif (ins >> 6) & 0b11 == 0b01: # ALU
            r1 = self._r[1]
            r2 = self._r[2]
            self._r[3] = self._alu(ins, r1, r2)
        elif (ins >> 6) & 0b11 == 0b10: # MOV
            src = (ins >> 3) & 0b111
            dst = ins & 0b111
            v = self._getv(src)
            self._setv(dst, v)
        elif (ins >> 3) & 0b11111 == 0b11000: # JXX
            r0 = self._r[0]
            r3 = self._r[3]
            ok = self._bu(ins, r3)
            if ok:
                self._pc = r0
        elif (ins >> 4) & 0b1111 == 0b1101: # STK
            if ins & 0b1000: # PUSH
                src = ins & 0b111
                v = self._getv(src)
                self._stk(ins, v)
            else: # POP
                v = self._stk(ins)
                dst = ins & 0b111
                self._setv(dst, v)
