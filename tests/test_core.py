"""Tests for the ternary computing emulator."""

import pytest

from ternary_emulator.core import (
    NEG, ZERO, POS,
    int_to_balanced_ternary, balanced_ternary_to_int,
    str_to_trits, trits_to_str, normalize_trits,
    ternary_add, ternary_sub, ternary_multiply, ternary_div, ternary_negate,
    ternary_and, ternary_or, ternary_xor, ternary_not,
    TernaryNumber,
    ternary_eq, quantize, quantize_array,
)
from ternary_emulator.vm import TernaryCPU, INSTRUCTIONS
from ternary_emulator.asm import assemble, disassemble


# ── Balanced Ternary Arithmetic ──────────────────────────────────────

class TestBalancedTernary:
    def test_zero(self):
        assert int_to_balanced_ternary(0) == (ZERO,)

    def test_positive(self):
        assert int_to_balanced_ternary(1) == (POS,)
        assert int_to_balanced_ternary(3) == (POS, ZERO)
        assert int_to_balanced_ternary(4) == (POS, POS)
        assert int_to_balanced_ternary(5) == (POS, NEG, NEG)
        assert int_to_balanced_ternary(42) == (POS, NEG, NEG, NEG, ZERO)

    def test_negative(self):
        assert int_to_balanced_ternary(-1) == (NEG,)
        assert int_to_balanced_ternary(-3) == (NEG, ZERO)
        assert int_to_balanced_ternary(-5) == (NEG, POS, POS)

    def test_round_trip(self):
        for n in range(-200, 201):
            assert balanced_ternary_to_int(int_to_balanced_ternary(n)) == n

    def test_parse_string(self):
        assert str_to_trits("1T0") == [POS, NEG, ZERO]
        assert str_to_trits("T") == [NEG]
        assert str_to_trits("0") == [ZERO]

    def test_string_round_trip(self):
        assert trits_to_str(int_to_balanced_ternary(42)) == "1TTT0"
        assert trits_to_str(int_to_balanced_ternary(-42)) == "T1110"
        assert trits_to_str(int_to_balanced_ternary(0)) == "0"

    def test_normalize(self):
        assert normalize_trits((ZERO, ZERO, POS)) == [POS]
        assert normalize_trits((ZERO,)) == [ZERO]
        assert normalize_trits((NEG, ZERO)) == [NEG, ZERO]


# ── ALU Operations ──────────────────────────────────────────────────

class TestALU:
    def test_add(self):
        a = int_to_balanced_ternary(5)
        b = int_to_balanced_ternary(3)
        assert balanced_ternary_to_int(ternary_add(a, b)) == 8

    def test_add_negative(self):
        a = int_to_balanced_ternary(5)
        b = int_to_balanced_ternary(-3)
        assert balanced_ternary_to_int(ternary_add(a, b)) == 2

    def test_sub(self):
        a = int_to_balanced_ternary(8)
        b = int_to_balanced_ternary(3)
        assert balanced_ternary_to_int(ternary_sub(a, b)) == 5

    def test_negate(self):
        assert balanced_ternary_to_int(ternary_negate(int_to_balanced_ternary(5))) == -5
        assert balanced_ternary_to_int(ternary_negate(int_to_balanced_ternary(-3))) == 3
        assert ternary_negate(int_to_balanced_ternary(0)) == [0]

    def test_multiply(self):
        a = int_to_balanced_ternary(4)
        b = int_to_balanced_ternary(3)
        assert balanced_ternary_to_int(ternary_multiply(a, b)) == 12

    def test_divide(self):
        a = int_to_balanced_ternary(12)
        b = int_to_balanced_ternary(3)
        q, r = ternary_div(a, b)
        assert balanced_ternary_to_int(q) == 4
        assert balanced_ternary_to_int(r) == 0

    def test_divide_with_remainder(self):
        a = int_to_balanced_ternary(10)
        b = int_to_balanced_ternary(3)
        q, r = ternary_div(a, b)
        assert balanced_ternary_to_int(q) == 3
        assert balanced_ternary_to_int(r) == 1

    def test_divide_by_zero(self):
        a = int_to_balanced_ternary(5)
        b = int_to_balanced_ternary(0)
        with pytest.raises(ZeroDivisionError):
            ternary_div(a, b)


# ── Three-Valued Logic ──────────────────────────────────────────────

class TestLogicProcessors:
    def test_tand(self):
        assert ternary_and(POS, POS) == POS
        assert ternary_and(ZERO, POS) == ZERO
        assert ternary_and(NEG, POS) == NEG
        assert ternary_and(NEG, NEG) == NEG

    def test_tor(self):
        assert ternary_or(POS, POS) == POS
        assert ternary_or(ZERO, POS) == POS
        assert ternary_or(NEG, POS) == POS
        assert ternary_or(NEG, ZERO) == ZERO

    def test_txor(self):
        assert ternary_xor(POS, NEG) == POS
        assert ternary_xor(POS, POS) == NEG
        assert ternary_xor(ZERO, POS) == ZERO

    def test_tnot(self):
        assert ternary_not(POS) == NEG
        assert ternary_not(NEG) == POS
        assert ternary_not(ZERO) == ZERO

    def test_teq(self):
        assert ternary_eq(POS, POS) == POS
        assert ternary_eq(NEG, NEG) == POS
        assert ternary_eq(POS, NEG) == NEG


# ── Quantization ────────────────────────────────────────────────────

class TestQuantization:
    def test_basic(self):
        assert quantize(0.8) == POS
        assert quantize(-0.8) == NEG
        assert quantize(0.1) == ZERO

    def test_array(self):
        assert quantize_array([0.8, -0.1, -0.9, 0.5]) == [POS, ZERO, NEG, POS]

    def test_threshold(self):
        assert quantize(0.5, threshold=0.6) == ZERO
        assert quantize(0.7, threshold=0.6) == POS


# ── TernaryNumber Class ─────────────────────────────────────────────

class TestTernaryNumber:
    def test_from_int(self):
        n = TernaryNumber.from_int(42)
        assert n.to_int() == 42
        assert str(n) == "1TTT0"

    def test_from_string(self):
        n = TernaryNumber.from_str("111T")
        assert n.to_int() == 38
        assert str(n) == "111T"

    def test_arithmetic(self):
        a = TernaryNumber.from_int(5)
        b = TernaryNumber.from_int(3)
        assert (a + b).to_int() == 8
        assert (a - b).to_int() == 2
        assert (a * b).to_int() == 15
        assert (-a).to_int() == -5

    def test_equality(self):
        a = TernaryNumber.from_int(42)
        b = TernaryNumber.from_str("1TTT0")
        assert a == b


# ── Ternary CPU ─────────────────────────────────────────────────────

class TestTernaryCPU:
    def test_reset(self):
        cpu = TernaryCPU()
        cpu.reset()
        assert cpu.pc == 0
        assert cpu.flags.halted is False
        assert cpu.registers["R0"] == [ZERO] * 9

    def test_nop(self):
        cpu = TernaryCPU()
        cpu.load_program([INSTRUCTIONS["NOP"][0]])
        cpu.step()
        assert cpu.pc == 1
        assert cpu.flags.halted is False

    def test_halt(self):
        cpu = TernaryCPU()
        cpu.load_program([INSTRUCTIONS["HALT"][0]])
        result = cpu.step()
        assert result is False
        assert cpu.flags.halted is True

    def test_mov_register(self):
        cpu = TernaryCPU()
        # MOV dest=R0, src=R1
        cpu.load_program([INSTRUCTIONS["MOV"][0], 0, 1])
        cpu.step()
        assert cpu.registers["R0"] == [ZERO] * 9

    def test_movi(self):
        cpu = TernaryCPU()
        # MOVI R0, 5
        cpu.load_program([INSTRUCTIONS["MOVI"][0], 0, 5])
        cpu.step()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 5

    def test_add(self):
        cpu = TernaryCPU()
        # MOVI R1, 3; MOVI R2, 5; ADD R0, R1, R2
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 3,
            INSTRUCTIONS["MOVI"][0], 2, 5,
            INSTRUCTIONS["ADD"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 8

    def test_sub(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 8,
            INSTRUCTIONS["MOVI"][0], 2, 3,
            INSTRUCTIONS["SUB"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 5

    def test_mul(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 4,
            INSTRUCTIONS["MOVI"][0], 2, 3,
            INSTRUCTIONS["MUL"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 12

    def test_div(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 12,
            INSTRUCTIONS["MOVI"][0], 2, 3,
            INSTRUCTIONS["DIV"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 4

    def test_neg(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 5,
            INSTRUCTIONS["NEG"][0], 0, 1,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == -5

    def test_and(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 1,
            INSTRUCTIONS["MOVI"][0], 2, 1,
            INSTRUCTIONS["AND"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 1

    def test_or(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 0,
            INSTRUCTIONS["MOVI"][0], 2, 1,
            INSTRUCTIONS["OR"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 1

    def test_xor(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 1,
            INSTRUCTIONS["MOVI"][0], 2, -1,
            INSTRUCTIONS["XOR"][0], 0, 1, 2,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == 1

    def test_not(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 1,
            INSTRUCTIONS["NOT"][0], 0, 1,
        ])
        cpu.run()
        assert balanced_ternary_to_int(tuple(cpu.registers["R0"])) == -1

    def test_cmp_zero(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 0,
            INSTRUCTIONS["MOVI"][0], 2, 0,
            INSTRUCTIONS["CMP"][0], 1, 2,
        ])
        cpu.run()
        assert cpu.flags.zero is True

    def test_cmp_negative(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, -5,
            INSTRUCTIONS["MOVI"][0], 2, 3,
            INSTRUCTIONS["CMP"][0], 1, 2,
        ])
        cpu.run()
        assert cpu.flags.negative is True

    def test_jmp(self):
        cpu = TernaryCPU()
        # MOVI R0, 5; JMP R0; NOP; NOP; NOP; NOP; HALT
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 0, 5,
            INSTRUCTIONS["JMP"][0], 0,
            INSTRUCTIONS["NOP"][0],
            INSTRUCTIONS["NOP"][0],
            INSTRUCTIONS["NOP"][0],
            INSTRUCTIONS["NOP"][0],
            INSTRUCTIONS["HALT"][0],
        ])
        cpu.run()
        assert cpu.pc == 10  # after HALT at index 9, pc advanced to 10

    def test_out(self):
        cpu = TernaryCPU()
        cpu.load_program([
            INSTRUCTIONS["MOVI"][0], 1, 42,
            INSTRUCTIONS["OUT"][0], 0, 1,
        ])
        output = cpu.run()
        assert any("42" in line for line in output)

    def test_dump_state(self):
        cpu = TernaryCPU()
        cpu.load_program([INSTRUCTIONS["HALT"][0]])
        cpu.run()
        dump = cpu.dump_state()
        assert "TERNARY CPU STATE" in dump
        assert "R0:" in dump


# ── Assembler ───────────────────────────────────────────────────────

class TestAssembler:
    def test_assemble_nop(self):
        program = assemble("NOP")
        assert program == [INSTRUCTIONS["NOP"][0]]

    def test_assemble_halt(self):
        program = assemble("HALT")
        assert program == [INSTRUCTIONS["HALT"][0]]

    def test_assemble_mov(self):
        program = assemble("MOV R0, R1")
        assert program[0] == INSTRUCTIONS["MOV"][0]

    def test_assemble_movi(self):
        program = assemble("MOV R0, 5")
        # Should auto-convert to MOVI
        assert program[0] == INSTRUCTIONS["MOVI"][0]
        assert program[1] == 0  # R0
        assert program[2] == 5  # immediate

    def test_assemble_add(self):
        program = assemble("ADD R0, R1, R2")
        assert program[0] == INSTRUCTIONS["ADD"][0]

    def test_assemble_with_numbers(self):
        program = assemble("MOVI R0, 5")
        assert program[0] == INSTRUCTIONS["MOVI"][0]

    def test_assemble_comments(self):
        program = assemble("NOP ; this is a comment")
        assert program == [INSTRUCTIONS["NOP"][0]]

    def test_assemble_blank_lines(self):
        program = assemble("\n\nNOP\n\n")
        assert program == [INSTRUCTIONS["NOP"][0]]

    def test_disassemble(self):
        program = [INSTRUCTIONS["NOP"][0], INSTRUCTIONS["HALT"][0]]
        text = disassemble(program)
        assert "NOP" in text
        assert "HALT" in text

    def test_round_trip(self):
        source = "NOP\nADD R0, R1, R2\nHALT"
        program = assemble(source)
        text = disassemble(program)
        program2 = assemble(text)
        assert program == program2

    def test_assemble_with_label(self):
        source = "START:\nNOP\nJMP START\n"
        program = assemble(source)
        assert len(program) > 0

    def test_movi_ternary_value(self):
        program = assemble("MOVI R0, 1T0T")
        assert program[0] == INSTRUCTIONS["MOVI"][0]
        assert program[1] == 0
        # 1T0T = 1*27 + (-1)*9 + 0*3 + (-1)*1 = 27-9-1 = 17
        assert program[2] == 17
