"""
Ternary CPU Virtual Machine

Simulates a balanced ternary CPU with:
- 27 general-purpose registers (R0-R26), each holding a balanced ternary word
- Program counter (PC), status register (SR), stack pointer (SP)
- Ternary addressable memory
- ALU with balanced ternary arithmetic and three-valued logic
- 3-trit opcode instruction set (28 opcodes, 0-27)

Instruction format: each instruction is one integer opcode followed by
zero or more integer operand words. Operands are register indices (0-26)
or immediate values depending on the instruction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import (
    NEG, ZERO, POS,
    TRIT_TO_CHAR, CHAR_TO_TRIT,
    int_to_balanced_ternary, balanced_ternary_to_int,
    ternary_add, ternary_sub, ternary_multiply, ternary_div,
    ternary_negate, ternary_and, ternary_or, ternary_xor, ternary_not,
    str_to_trits, trits_to_str, normalize_trits,
)

# ── Instruction set ─────────────────────────────────────────────────

INSTRUCTIONS: dict[str, tuple[int, int, str]] = {
    # data movement
    "NOP":    (0,  0, "No operation"),
    "MOV":    (1,  2, "MOV dest, src          - copy register"),
    "MOVI":   (2,  2, "MOVI reg, immediate    - load immediate value"),
    "LOAD":   (3,  2, "LOAD dest, addr_reg    - load from memory[addr_reg]"),
    "STORE":  (4,  2, "STORE src, addr_reg    - store to memory[addr_reg]"),
    "PUSH":   (5,  1, "PUSH src               - push register to stack"),
    "POP":    (6,  1, "POP dest                - pop from stack to register"),

    # arithmetic
    "ADD":    (7,  3, "ADD dest, src1, src2   - ternary add"),
    "SUB":    (8,  3, "SUB dest, src1, src2   - ternary subtract"),
    "MUL":    (9,  3, "MUL dest, src1, src2   - ternary multiply"),
    "DIV":    (10, 3, "DIV dest, src1, src2   - ternary divide (quotient)"),
    "NEG":    (11, 2, "NEG dest, src          - ternary negate"),

    # logic (per-trit three-valued logic)
    "AND":    (12, 3, "AND dest, src1, src2   - three-valued AND"),
    "OR":     (13, 3, "OR dest, src1, src2    - three-valued OR"),
    "XOR":    (14, 3, "XOR dest, src1, src2   - three-valued XOR"),
    "NOT":    (15, 2, "NOT dest, src           - three-valued NOT"),

    # shift
    "SHL":    (16, 3, "SHL dest, src, amount  - shift left by amount trits"),
    "SHR":    (17, 3, "SHR dest, src, amount  - shift right by amount trits"),

    # compare
    "CMP":    (18, 2, "CMP src1, src2          - compare, set flags"),

    # control flow
    "JMP":    (19, 1, "JMP addr_reg            - unconditional jump"),
    "JZ":     (20, 1, "JZ addr_reg             - jump if zero flag set"),
    "JN":     (21, 1, "JN addr_reg             - jump if negative flag set"),
    "JP":     (22, 1, "JP addr_reg             - jump if positive flag set"),
    "CALL":   (23, 1, "CALL addr_reg            - call subroutine"),
    "RET":    (24, 0, "RET                      - return from subroutine"),

    # I/O
    "IN":     (25, 2, "IN dest, port           - read input to register"),
    "OUT":    (26, 2, "OUT port, src           - write register to output"),

    # control
    "HALT":   (27, 0, "HALT                     - stop execution"),
}

OPCODE_BY_NUM: dict[int, str] = {info[0]: mnemonic for mnemonic, info in INSTRUCTIONS.items()}


@dataclass
class CPUFlags:
    """CPU status flags."""
    zero: bool = False
    negative: bool = False
    positive: bool = False
    carry: bool = False
    halted: bool = False

    def update_from_result(self, result: list[int]) -> None:
        val = balanced_ternary_to_int(tuple(result))
        self.zero = (val == 0)
        self.negative = (val < 0)
        self.positive = (val > 0)

    def __str__(self) -> str:
        flags = []
        if self.zero: flags.append("Z")
        if self.negative: flags.append("N")
        if self.positive: flags.append("P")
        if self.carry: flags.append("C")
        if self.halted: flags.append("H")
        return "".join(flags) if flags else "-"


@dataclass
class TernaryCPU:
    """Balanced Ternary CPU emulator."""
    register_width: int = 9
    memory_size: int = 19683

    registers: dict[str, list[int]] = field(init=False)
    memory: dict[int, list[int]] = field(init=False)
    pc: int = 0
    sp: int = 0
    flags: CPUFlags = field(default_factory=CPUFlags)

    input_buffer: list[int] = field(default_factory=list)
    output_buffer: list[str] = field(default_factory=list)

    program: list[int] = field(default_factory=list)
    cycle_count: int = 0
    max_cycles: int = 100_000

    def __post_init__(self) -> None:
        self.registers = {}
        for i in range(27):
            self.registers[f"R{i}"] = [ZERO] * self.register_width
        self.memory = {}
        self.sp = self.memory_size - 1

    def _get_reg(self, name: str) -> list[int]:
        name = name.upper().strip()
        if name not in self.registers:
            raise ValueError(f"unknown register: {name}")
        return list(self.registers[name])

    def _set_reg(self, name: str, value: list[int]) -> None:
        name = name.upper().strip()
        if name not in self.registers:
            raise ValueError(f"unknown register: {name}")
        padded = list(value)
        while len(padded) < self.register_width:
            padded.insert(0, ZERO)
        if len(padded) > self.register_width:
            padded = padded[-self.register_width:]
        self.registers[name] = padded

    def _mem_read(self, addr: int) -> list[int]:
        if addr < 0 or addr >= self.memory_size:
            raise ValueError(f"memory address out of range: {addr}")
        return list(self.memory.get(addr, [ZERO] * self.register_width))

    def _mem_write(self, addr: int, value: list[int]) -> None:
        if addr < 0 or addr >= self.memory_size:
            raise ValueError(f"memory address out of range: {addr}")
        padded = list(value)
        while len(padded) < self.register_width:
            padded.insert(0, ZERO)
        if len(padded) > self.register_width:
            padded = padded[-self.register_width:]
        self.memory[addr] = padded

    def _resolve_address(self, reg_index: int) -> int:
        return balanced_ternary_to_int(tuple(self._get_reg(f"R{reg_index}")))

    def reg_value_to_int(self, name: str) -> int:
        """Get integer value of a register by name."""
        return balanced_ternary_to_int(tuple(self._get_reg(name)))

    def load_program(self, program: list[int]) -> None:
        self.program = list(program)
        self.pc = 0

    def step(self) -> bool:
        if self.flags.halted:
            return False
        if self.pc < 0 or self.pc >= len(self.program):
            self.flags.halted = True
            return False

        opcode = self.program[self.pc]
        self.pc += 1
        self.cycle_count += 1

        if self.cycle_count > self.max_cycles:
            self.output_buffer.append(f"[WARN] max cycles ({self.max_cycles}) reached")
            self.flags.halted = True
            return False

        if opcode not in OPCODE_BY_NUM:
            self.output_buffer.append(f"[WARN] invalid opcode {opcode} at PC={self.pc - 1}")
            return True

        mnemonic = OPCODE_BY_NUM[opcode]
        operand_count = INSTRUCTIONS[mnemonic][1]

        operands: list[int] = []
        for _ in range(operand_count):
            if self.pc < len(self.program):
                operands.append(self.program[self.pc])
                self.pc += 1
            else:
                operands.append(0)

        self._execute(mnemonic, operands)
        return not self.flags.halted

    def _execute(self, mnemonic: str, ops: list[int]) -> None:
        if mnemonic == "NOP":
            pass

        elif mnemonic == "MOV":
            src = self._get_reg(f"R{ops[1]}")
            self._set_reg(f"R{ops[0]}", src)
            self.flags.update_from_result(src)

        elif mnemonic == "MOVI":
            val = int_to_balanced_ternary(ops[1], self.register_width)
            self._set_reg(f"R{ops[0]}", list(val))
            self.flags.update_from_result(list(val))

        elif mnemonic == "LOAD":
            addr = self._resolve_address(ops[1])
            val = self._mem_read(addr)
            self._set_reg(f"R{ops[0]}", val)
            self.flags.update_from_result(val)

        elif mnemonic == "STORE":
            addr = self._resolve_address(ops[1])
            val = self._get_reg(f"R{ops[0]}")
            self._mem_write(addr, val)

        elif mnemonic == "ADD":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = list(ternary_add(tuple(a), tuple(b), self.register_width))
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "SUB":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = list(ternary_sub(tuple(a), tuple(b), self.register_width))
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "MUL":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = list(ternary_multiply(tuple(a), tuple(b), self.register_width))
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "DIV":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            try:
                result, remainder = ternary_div(tuple(a), tuple(b), self.register_width)
                self._set_reg(f"R{ops[0]}", list(result))
                self._set_reg("R26", list(remainder))
                self.flags.update_from_result(list(result))
            except ZeroDivisionError:
                self.output_buffer.append("[ERROR] division by zero")
                self.flags.halted = True

        elif mnemonic == "NEG":
            src = self._get_reg(f"R{ops[1]}")
            result = list(ternary_negate(tuple(src)))
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "AND":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = [ternary_and(x, y) for x, y in zip(a, b)]
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "OR":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = [ternary_or(x, y) for x, y in zip(a, b)]
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "XOR":
            a = self._get_reg(f"R{ops[1]}")
            b = self._get_reg(f"R{ops[2]}")
            result = [ternary_xor(x, y) for x, y in zip(a, b)]
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "NOT":
            src = self._get_reg(f"R{ops[1]}")
            result = [ternary_not(t) for t in src]
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "SHL":
            src = self._get_reg(f"R{ops[1]}")
            amount = max(0, ops[2])
            result = src[amount:] + [ZERO] * amount
            if len(result) > self.register_width:
                result = result[:self.register_width]
            while len(result) < self.register_width:
                result.insert(0, ZERO)
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "SHR":
            src = self._get_reg(f"R{ops[1]}")
            amount = max(0, ops[2])
            if amount > 0:
                result = [ZERO] * amount + src[:-amount]
            else:
                result = list(src)
            while len(result) < self.register_width:
                result.insert(0, ZERO)
            if len(result) > self.register_width:
                result = result[-self.register_width:]
            self._set_reg(f"R{ops[0]}", result)
            self.flags.update_from_result(result)

        elif mnemonic == "CMP":
            a = self._get_reg(f"R{ops[0]}")
            b = self._get_reg(f"R{ops[1]}")
            result = list(ternary_sub(tuple(a), tuple(b), self.register_width))
            self.flags.update_from_result(result)

        elif mnemonic == "JMP":
            self.pc = self._resolve_address(ops[0])

        elif mnemonic == "JZ":
            if self.flags.zero:
                self.pc = self._resolve_address(ops[0])

        elif mnemonic == "JN":
            if self.flags.negative:
                self.pc = self._resolve_address(ops[0])

        elif mnemonic == "JP":
            if self.flags.positive:
                self.pc = self._resolve_address(ops[0])

        elif mnemonic == "CALL":
            ret_addr = int_to_balanced_ternary(self.pc, self.register_width)
            self._mem_write(self.sp, list(ret_addr))
            self.sp -= 1
            self.pc = self._resolve_address(ops[0])

        elif mnemonic == "RET":
            self.sp += 1
            addr = self._mem_read(self.sp)
            self.pc = balanced_ternary_to_int(tuple(addr))

        elif mnemonic == "PUSH":
            val = self._get_reg(f"R{ops[0]}")
            self._mem_write(self.sp, val)
            self.sp -= 1

        elif mnemonic == "POP":
            self.sp += 1
            val = self._mem_read(self.sp)
            self._set_reg(f"R{ops[0]}", val)

        elif mnemonic == "IN":
            port = ops[1]
            if self.input_buffer:
                val = self.input_buffer.pop(0)
            else:
                val = ZERO
            self._set_reg(f"R{ops[0]}", list(int_to_balanced_ternary(val, self.register_width)))

        elif mnemonic == "OUT":
            port = ops[0]
            val = self._get_reg(f"R{ops[1]}")
            int_val = balanced_ternary_to_int(tuple(val))
            tri_str = trits_to_str(val)
            self.output_buffer.append(f"[OUT p{port}] {int_val} ({tri_str})")

        elif mnemonic == "HALT":
            self.flags.halted = True

    def run(self) -> list[str]:
        while self.step():
            pass
        return list(self.output_buffer)

    def reset(self) -> None:
        self.__init__(self.register_width, self.memory_size)

    def dump_state(self) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("  TERNARY CPU STATE")
        lines.append("=" * 50)
        lines.append(f"  PC={self.pc}  SP={self.sp}  Flags=[{self.flags}]  Cycles={self.cycle_count}")
        lines.append("-" * 50)
        lines.append("  REGISTERS:")
        for i in range(27):
            name = f"R{i}"
            val = self.registers[name]
            int_val = balanced_ternary_to_int(tuple(val))
            tri_str = trits_to_str(val)
            marker = " *" if int_val != 0 else "  "
            lines.append(f"    {name}: {tri_str:>9s}  ({int_val:>6d}){marker}")
        lines.append("-" * 50)
        lines.append("  MEMORY (non-zero):")
        nonzero = {k: v for k, v in sorted(self.memory.items()) if balanced_ternary_to_int(tuple(v)) != 0}
        if nonzero:
            for addr, val in list(nonzero.items())[:50]:
                int_val = balanced_ternary_to_int(tuple(val))
                tri_str = trits_to_str(val)
                lines.append(f"    [{addr:>5d}]: {tri_str:>9s}  ({int_val:>6d})")
            if len(nonzero) > 50:
                lines.append(f"    ... ({len(nonzero) - 50} more)")
        else:
            lines.append("    (all zero)")
        if self.output_buffer:
            lines.append("-" * 50)
            lines.append("  OUTPUT:")
            for line in self.output_buffer:
                lines.append(f"    {line}")
        lines.append("=" * 50)
        return "\n".join(lines)
