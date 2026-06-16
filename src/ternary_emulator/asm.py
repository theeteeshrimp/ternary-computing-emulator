"""
Ternary Assembler & Disassembler

Human-readable assembly language for the ternary CPU, with
two-way translation between assembly text and machine code.

Assembly syntax (one instruction per line):
    OPCODE  operands           ; comment

Registers: R0-R26
Numbers: decimal integers or balanced ternary strings (e.g., 1T0T)
Memory:  [Rn] for register-indirect addressing
Labels:  defined with LABEL:, referenced by name
"""

from __future__ import annotations

import re

from .core import (
    NEG, ZERO, POS,
    int_to_balanced_ternary, balanced_ternary_to_int,
    str_to_trits, trits_to_str,
)
from .vm import INSTRUCTIONS, OPCODE_BY_NUM


def _parse_value(text: str) -> int:
    """Parse a value: decimal integer, balanced ternary string, or register."""
    text = text.strip()
    if not text:
        raise ValueError("empty operand")

    # Register
    if re.match(r"^R\d+$", text, re.IGNORECASE):
        idx = int(text[1:])
        if 0 <= idx <= 26:
            return idx
        raise ValueError(f"register index out of range: {text}")

    # Balanced ternary string (contains T, -, or only 0/1)
    if re.match(r"^[T\-01]+$", text.upper()) and not re.match(r"^\d+$", text):
        trits = str_to_trits(text)
        return balanced_ternary_to_int(tuple(trits))

    # Decimal integer
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"cannot parse value: {text!r}")


def _is_register(text: str) -> bool:
    return bool(re.match(r"^R\d+$", text, re.IGNORECASE))


def assemble(source: str) -> list[int]:
    """
    Assemble source text into a flat list of integer opcodes and operands.

    Supports:
    - Instructions: NOP, MOV, MOVI, LOAD, STORE, PUSH, POP, ADD, SUB, MUL,
      DIV, NEG, AND, OR, XOR, NOT, SHL, SHR, CMP, JMP, JZ, JN, JP, CALL,
      RET, IN, OUT, HALT
    - Registers: R0-R26
    - Immediate values: decimal or balanced ternary (e.g., 1T0T)
    - Labels: LABEL_NAME: (definition) and LABEL_NAME (reference)
    - Comments: ; comment
    - Memory addressing: [Rn]
    """
    lines = source.strip().splitlines()
    program: list[int] = []
    labels: dict[str, int] = {}
    pending_labels: list[tuple[int, str]] = []  # (program_index, label_name)

    for line_num, raw_line in enumerate(lines, 1):
        # Strip comments
        line = raw_line.split(";")[0].strip()
        if not line:
            continue

        # Label definition
        label_match = re.match(r"^([A-Za-z_]\w*):\s*(.*)", line)
        if label_match:
            label_name = label_match.group(1)
            labels[label_name] = len(program)
            line = label_match.group(2).strip()
            if not line:
                continue

        # Split instruction and operands
        parts = re.split(r"[\s,]+", line.strip())
        mnemonic = parts[0].upper()
        operand_strs = [p.strip() for p in parts[1:] if p.strip()]

        if mnemonic not in INSTRUCTIONS:
            raise ValueError(f"line {line_num}: unknown instruction: {mnemonic}")

        expected_ops = INSTRUCTIONS[mnemonic][1]
        opcode = INSTRUCTIONS[mnemonic][0]

        # Handle special syntax
        if mnemonic == "MOV" and len(operand_strs) == 2:
            # MOV dest, src — if src is immediate, use MOVI
            if not _is_register(operand_strs[1]):
                # MOVI reg, immediate
                reg_idx = _parse_value(operand_strs[0])
                imm_val = _parse_value(operand_strs[1])
                program.append(INSTRUCTIONS["MOVI"][0])
                program.append(reg_idx)
                program.append(imm_val)
                continue

        if mnemonic in ("LOAD", "STORE") and len(operand_strs) == 2:
            # LOAD dest, [addr_reg] or STORE src, [addr_reg]
            addr_str = operand_strs[1].strip("[]")
            operand_strs = [operand_strs[0], addr_str]

        if mnemonic in ("JMP", "JZ", "JN", "JP", "CALL") and len(operand_strs) == 1:
            # Can be a label or a register
            target = operand_strs[0]
            if re.match(r"^R\d+$", target, re.IGNORECASE):
                reg_idx = _parse_value(target)
                program.append(opcode)
                program.append(reg_idx)
            elif re.match(r"^[A-Za-z_]\w*$", target):
                # Label reference — resolve now if known, else patch later
                program.append(opcode)
                if target in labels:
                    program.append(labels[target])
                else:
                    pending_labels.append((len(program), target))
                    program.append(0)  # placeholder
            else:
                raise ValueError(f"line {line_num}: invalid jump target: {target}")
            continue

        # Standard encoding
        if len(operand_strs) != expected_ops:
            raise ValueError(
                f"line {line_num}: {mnemonic} expects {expected_ops} operands, got {len(operand_strs)}"
            )

        program.append(opcode)
        for op_str in operand_strs:
            # Handle memory addressing syntax [Rn]
            op_str = op_str.strip("[]")
            program.append(_parse_value(op_str))

    # Patch label references
    for idx, label_name in pending_labels:
        if label_name not in labels:
            raise ValueError(f"undefined label: {label_name}")
        program[idx] = labels[label_name]

    return program


def disassemble(program: list[int]) -> str:
    """Disassemble a flat program into human-readable assembly text."""
    lines: list[str] = []
    pc = 0

    while pc < len(program):
        opcode = program[pc]
        if opcode not in OPCODE_BY_NUM:
            lines.append(f"??? ({opcode})")
            pc += 1
            continue

        mnemonic = OPCODE_BY_NUM[opcode]
        operand_count = INSTRUCTIONS[mnemonic][1]
        pc += 1

        operands: list[str] = []
        for _ in range(operand_count):
            if pc < len(program):
                val = program[pc]
                pc += 1
            else:
                val = 0

            # For jump/call instructions, show as label-like
            if mnemonic in ("JMP", "JZ", "JN", "JP", "CALL") and _ == 0:
                operands.append(f"R{val}")
            elif mnemonic in ("MOV", "MOVI", "LOAD", "STORE", "PUSH", "POP", "NEG", "NOT", "IN", "OUT") and _ == 0:
                operands.append(f"R{val}")
            elif mnemonic in ("ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR") and _ < 3:
                operands.append(f"R{val}")
            elif mnemonic == "CMP":
                operands.append(f"R{val}")
            elif mnemonic == "SHL" or mnemonic == "SHR":
                if _ < 2:
                    operands.append(f"R{val}")
                else:
                    operands.append(str(val))
            else:
                operands.append(str(val))

        lines.append(f"{mnemonic} {', '.join(operands)}")

    return "\n".join(lines)


def assemble_to_program(source: str) -> list[int]:
    """Assemble source to a program (alias for assemble)."""
    return assemble(source)
