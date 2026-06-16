"""
Ternary Computing Emulator — CLI

Interactive command-line interface for the ternary computing emulator.
Supports:
- Interactive REPL
- Running assembly programs
- Converting numbers
- Running demos
- Cross-platform standalone execution
"""

from __future__ import annotations

import argparse
import os
import sys
import readline  # enables arrow keys / history in REPL

from . import __version__
from .core import (
    NEG, ZERO, POS,
    int_to_balanced_ternary, balanced_ternary_to_int,
    str_to_trits, trits_to_str,
    ternary_add, ternary_sub, ternary_multiply, ternary_div, ternary_negate,
    ternary_and, ternary_or, ternary_xor, ternary_not,
    TernaryNumber,
)
from .vm import TernaryCPU, INSTRUCTIONS
from .asm import assemble, disassemble


# ── Demo programs ───────────────────────────────────────────────────

DEMO_HELLO = """
; Hello World — output numbers 1 through 5
    MOV   R0, R0          ; clear R0 (NOP-like)
    MOV   R1, R1          ; clear R1
    ; We'll use OUT to print values
    ; R0 = counter, R1 = limit
    ; Since we can't encode immediates easily, we pre-load values
"""

DEMO_FIBONACCI = """
; Fibonacci sequence — compute and output first 10 terms
; R0 = current, R1 = next, R2 = temp, R3 = counter
; Pre-loaded: R0=0, R1=1, R3=10
; Loop:
;   OUT 0, R0
;   MOV R2, R1
;   ADD R1, R0, R1
;   MOV R0, R2
;   SUB R3, R3, 1
;   JNZ loop
; HALT
"""

DEMO_ARITHMETIC = """
; Arithmetic demo: compute 7 + 5, 7 - 5, 7 * 5
; Results in R3, R4, R5
"""


def run_demo(demo_name: str) -> None:
    """Run a built-in demo program."""
    print(f"\n{'═' * 50}")
    print(f"  Ternary Computing Emulator v{__version__}")
    print(f"  Demo: {demo_name}")
    print(f"{'═' * 50}\n")

    if demo_name == "cpu":
        _demo_cpu()
    elif demo_name == "arithmetic":
        _demo_arithmetic()
    elif demo_name == "logic":
        _demo_logic()
    elif demo_name == "convert":
        _demo_convert()
    elif demo_name == "fibonacci":
        _demo_fibonacci()
    else:
        print(f"Unknown demo: {demo_name}")
        print("Available demos: cpu, arithmetic, logic, convert, fibonacci")


def _demo_cpu() -> None:
    """Demonstrate the CPU with a simple program."""
    cpu = TernaryCPU()

    # Program: compute 5 + 3, store result, output it
    # We'll use the assembler
    source = """
    ; Simple CPU demo: compute and output values
    OUT 0, R0    ; output R0 (should be 0)
    OUT 0, R1    ; output R1 (should be 0)
    HALT
    """
    program = assemble(source)
    print("Assembly:")
    print(source)
    print("Machine code:", program)
    print("Disassembly:")
    print(disassemble(program))
    print()

    cpu.load_program(program)
    output = cpu.run()
    print("Output:")
    for line in output:
        print(f"  {line}")
    print()
    print(cpu.dump_state())


def _demo_arithmetic(self=None) -> None:
    """Demonstrate ternary arithmetic."""
    print("Balanced Ternary Arithmetic")
    print("─" * 40)

    pairs = [(5, 3), (-7, 4), (0, 0), (13, -8), (100, 27)]
    for a, b in pairs:
        ta = int_to_balanced_ternary(a)
        tb = int_to_balanced_ternary(b)
        tsum = ternary_add(ta, tb)
        tdiff = ternary_sub(ta, tb)
        tprod = ternary_multiply(ta, tb)

        print(f"  {a:>4d} ({trits_to_str(ta):>5s}) + {b:>4d} ({trits_to_str(tb):>5s}) = "
              f"{a + b:>4d} ({trits_to_str(tsum):>5s})")
        print(f"  {a:>4d} ({trits_to_str(ta):>5s}) - {b:>4d} ({trits_to_str(tb):>5s}) = "
              f"{a - b:>4d} ({trits_to_str(tdiff):>5s})")
        print(f"  {a:>4d} ({trits_to_str(ta):>5s}) * {b:>4d} ({trits_to_str(tb):>5s}) = "
              f"{a * b:>4d} ({trits_to_str(tprod):>5s})")

        if b != 0:
            tq, tr = ternary_div(ta, tb)
            print(f"  {a:>4d} ({trits_to_str(ta):>5s}) / {b:>4d} ({trits_to_str(tb):>5s}) = "
                  f"{a // b:>4d} ({trits_to_str(tq):>5s}) rem {a - (a // b) * b} ({trits_to_str(tr):>5s})")
        print()


def _demo_logic() -> None:
    """Demonstrate three-valued logic."""
    print("Three-Valued Logic Gates")
    print("─" * 40)
    print(f"  {'A':>4s}  {'B':>4s}  {'AND':>4s}  {'OR':>4s}  {'XOR':>4s}  {'NOT A':>5s}")
    print(f"  {'─' * 4}  {'─' * 4}  {'─' * 4}  {'─' * 4}  {'─' * 4}  {'─' * 5}")

    values = [NEG, ZERO, POS]
    labels = {NEG: " T", ZERO: " 0", POS: " 1"}

    for a in values:
        for b in values:
            result_and = ternary_and(a, b)
            result_or = ternary_or(a, b)
            result_xor = ternary_xor(a, b)
            result_not = ternary_not(a)
            print(f"  {labels[a]:>4s}  {labels[b]:>4s}  {labels[result_and]:>4s}  "
                  f"{labels[result_or]:>4s}  {labels[result_xor]:>4s}  {labels[result_not]:>5s}")
        print()


def _demo_convert() -> None:
    """Demonstrate number conversion."""
    print("Number Conversion")
    print("─" * 40)
    print(f"  {'Decimal':>10s}  {'Balanced Ternary':>16s}  {'Back':>10s}")
    print(f"  {'─' * 10}  {'─' * 16}  {'─' * 10}")

    for n in range(-20, 21):
        bt = int_to_balanced_ternary(n)
        s = trits_to_str(bt)
        back = balanced_ternary_to_int(bt)
        print(f"  {n:>10d}  {s:>16s}  {back:>10d}")


def _demo_fibonacci() -> None:
    """Compute Fibonacci using the ternary CPU."""
    print("Fibonacci on the Ternary CPU")
    print("─" * 40)

    cpu = TernaryCPU()

    # We'll compute fibonacci by directly setting registers and running
    # a simple program that adds and loops
    # For simplicity, we'll do it step by step

    cpu._set_reg("R0", int_to_balanced_ternary(0))   # fib(0)
    cpu._set_reg("R1", int_to_balanced_ternary(1))   # fib(1)
    cpu._set_reg("R3", int_to_balanced_ternary(10))  # counter

    print("  n  |  fib(n)  |  balanced ternary")
    print(f"  {'─' * 2}  |  {'─' * 7}  |  {'─' * 16}")

    fibs = []
    for i in range(10):
        val = cpu._reg_value_to_int("R0")
        bt = cpu._get_reg("R0")
        fibs.append(val)
        print(f"  {i:>2d}  |  {val:>7d}  |  {trits_to_str(bt):>16s}")

        # Compute next: R2 = R0 + R1, R0 = R1, R1 = R2
        program = assemble("""
            MOV R2, R1
            ADD R1, R0, R1
            MOV R0, R2
        """)
        cpu.load_program(program)
        cpu.run()

    print(f"\n  Sequence: {fibs}")


# ── REPL ────────────────────────────────────────────────────────────

def run_repl() -> None:
    """Run the interactive REPL."""
    print(f"\n{'═' * 55}")
    print(f"  ⢕⣿⢀⣏⣿⢳⡕⣆⢺⣋⢟  Ternary Computing Emulator v{__version__}")
    print(f"  Type 'help' for commands, 'quit' to exit")
    print(f"{'═' * 55}\n")

    cpu = TernaryCPU()

    while True:
        try:
            line = input("ternary> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not line:
            continue

        parts = line.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        try:
            if cmd in ("quit", "exit", "q"):
                print("Bye!")
                break

            elif cmd == "help":
                _print_help()

            elif cmd == "convert":
                _repl_convert(args)

            elif cmd == "add":
                _repl_op(args, "add")
            elif cmd == "sub":
                _repl_op(args, "sub")
            elif cmd == "mul":
                _repl_op(args, "mul")
            elif cmd == "div":
                _repl_op(args, "div")

            elif cmd == "logic":
                _repl_logic(args)

            elif cmd == "run":
                _repl_run(cpu, args)

            elif cmd == "step":
                _repl_step(cpu)

            elif cmd == "reset":
                cpu.reset()
                print("  CPU reset.")

            elif cmd == "state":
                print(cpu.dump_state())

            elif cmd == "load":
                _repl_load(cpu, args)

            elif cmd == "asm":
                _repl_asm(args)

            elif cmd == "disasm":
                _repl_disasm(args)

            elif cmd == "demo":
                run_demo(args if args else "arithmetic")

            elif cmd == "mem":
                _repl_mem(cpu, args)

            elif cmd == "reg":
                _repl_reg(cpu, args)

            else:
                print(f"  Unknown command: {cmd}. Type 'help' for commands.")

        except Exception as e:
            print(f"  Error: {e}")


def _print_help() -> None:
    """Print REPL help."""
    print("""
  Commands:
    convert <n>         — Convert decimal to balanced ternary
    add <a> <b>          — Ternary add
    sub <a> <b>          — Ternary subtract
    mul <a> <b>          — Ternary multiply
    div <a> <b>          — Ternary divide
    logic                — Show three-valued logic table
    asm <source>         — Assemble instructions (semicolon-separated)
    disasm <opcodes>     — Disassemble machine code (space-separated)
    load <file>          — Load assembly file and assemble
    run [file]           — Run loaded program or load and run file
    step                 — Execute one instruction
    reset                — Reset CPU state
    state                — Dump CPU state
    mem <addr> [count]   — Show memory contents
    reg <name> [value]   — Get/set register
    demo <name>          — Run demo (cpu, arithmetic, logic, convert, fibonacci)
    help                 — Show this help
    quit                 — Exit
  """)


def _parse_value(text: str) -> int:
    """Parse a value (decimal or balanced ternary string)."""
    text = text.strip()
    if any(c in text.upper() for c in "T") and not text[1:].isdigit():
        return balanced_ternary_to_int(str_to_trits(text))
    return int(text)


def _repl_convert(args: str) -> None:
    """Convert a number."""
    n = int(args)
    bt = int_to_balanced_ternary(n)
    s = trits_to_str(bt)
    print(f"  {n} → {s} (balanced ternary)")
    print(f"  {s} → {balanced_ternary_to_int(bt)} (decimal)")


def _repl_op(args: str, op: str) -> None:
    """Perform a binary operation."""
    parts = args.split()
    if len(parts) != 2:
        print(f"  Usage: {op} <a> <b>")
        return

    a = _parse_value(parts[0])
    b = _parse_value(parts[1])
    ta = int_to_balanced_ternary(a)
    tb = int_to_balanced_ternary(b)

    if op == "add":
        result = ternary_add(ta, tb)
    elif op == "sub":
        result = ternary_sub(ta, tb)
    elif op == "mul":
        result = ternary_multiply(ta, tb)
    elif op == "div":
        if b == 0:
            print("  Error: division by zero")
            return
        result, rem = ternary_div(ta, tb)
        rem_int = balanced_ternary_to_int(rem)
    else:
        return

    res_int = balanced_ternary_to_int(result)
    res_str = trits_to_str(result)
    print(f"  {trits_to_str(ta)} {op} {trits_to_str(tb)} = {res_str} ({res_int})")
    if op == "div" and rem_int != 0:
        print(f"  remainder: {trits_to_str(rem)} ({rem_int})")


def _repl_logic(args: str) -> None:
    """Show logic table."""
    _demo_logic()


def _repl_run(cpu: TernaryCPU, args: str) -> None:
    """Run a program."""
    if args:
        _repl_load(cpu, args)
    if not cpu.program:
        print("  No program loaded. Use 'load <file>' or 'asm <source>' first.")
        return
    output = cpu.run()
    for line in output:
        print(f"  {line}")
    print(f"  [{cpu.cycle_count} cycles, flags: {cpu.flags}]")


def _repl_step(cpu: TernaryCPU) -> None:
    """Execute one step."""
    if not cpu.program:
        print("  No program loaded.")
        return
    running = cpu.step()
    print(f"  PC={cpu.pc} Flags=[{cpu.flags}] Cycles={cpu.cycle_count}")
    if not running:
        print("  CPU halted.")


def _repl_load(cpu: TernaryCPU, args: str) -> None:
    """Load an assembly file."""
    path = args.strip()
    if not os.path.exists(path):
        print(f"  File not found: {path}")
        return
    with open(path) as f:
        source = f.read()
    program = assemble(source)
    cpu.load_program(program)
    print(f"  Loaded {len(program)} words from {path}")


def _repl_asm(args: str) -> None:
    """Assemble instructions."""
    source = args.replace(";", "\n")
    program = assemble(source)
    print(f"  Machine code: {program}")
    print(f"  Disassembly:")
    print(disassemble(program))


def _repl_disasm(args: str) -> None:
    """Disassemble machine code."""
    codes = [int(x) for x in args.split()]
    print(disassemble(codes))


def _repl_mem(cpu: TernaryCPU, args: str) -> None:
    """Show memory."""
    parts = args.split()
    if not parts:
        print("  Usage: mem <addr> [count]")
        return
    addr = int(parts[0])
    count = int(parts[1]) if len(parts) > 1 else 10
    for i in range(count):
        a = addr + i
        if 0 <= a < cpu.memory_size:
            val = cpu._mem_read(a)
            v = balanced_ternary_to_int(val)
            if v != 0:
                print(f"  [{a:>5d}]: {trits_to_str(val):>9s}  ({v})")


def _repl_reg(cpu: TernaryCPU, args: str) -> None:
    """Get/set register."""
    parts = args.split()
    if not parts:
        print("  Usage: reg <name> [value]")
        return
    name = parts[0].upper()
    if len(parts) == 1:
        val = cpu._get_reg(name)
        v = balanced_ternary_to_int(val)
        print(f"  {name}: {trits_to_str(val)} ({v})")
    else:
        value = _parse_value(parts[1])
        cpu._set_reg(name, int_to_balanced_ternary(value, cpu.register_width))
        val = cpu._get_reg(name)
        v = balanced_ternary_to_int(val)
        print(f"  {name} ← {trits_to_str(val)} ({v})")


# ── Main entry point ────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ternary-emulator",
        description="Ternary Computing Emulator — balanced ternary CPU, assembler, and REPL",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # REPL
    subparsers.add_parser("repl", help="start interactive REPL")

    # Convert
    conv = subparsers.add_parser("convert", help="convert a number")
    conv.add_argument("value", type=int)

    # Arithmetic
    arith = subparsers.add_parser("calc", help="ternary arithmetic")
    arith.add_argument("a", type=int)
    arith.add_argument("op", choices=["+", "-", "*", "/"])
    arith.add_argument("b", type=int)

    # Logic
    subparsers.add_parser("logic", help="show three-valued logic table")

    # Assemble
    asm_p = subparsers.add_parser("asm", help="assemble a program")
    asm_p.add_argument("source", help="assembly source string (semicolon-separated)")
    asm_p.add_argument("--run", action="store_true", help="run after assembling")

    # Run file
    run_p = subparsers.add_parser("run", help="run an assembly file")
    run_p.add_argument("file", help="path to assembly file")

    # Disassemble
    dis_p = subparsers.add_parser("disasm", help="disassemble machine code")
    dis_p.add_argument("codes", nargs="+", type=int, help="machine code words")

    # Demo
    demo = subparsers.add_parser("demo", help="run a demo")
    demo.add_argument("name", nargs="?", default="arithmetic",
                      choices=["cpu", "arithmetic", "logic", "convert", "fibonacci"])

    args = parser.parse_args(argv)

    if args.command is None:
        run_repl()
        return 0

    if args.command == "repl":
        run_repl()

    elif args.command == "convert":
        n = args.value
        bt = int_to_balanced_ternary(n)
        s = trits_to_str(bt)
        print(f"{n} → {s}")
        print(f"{s} → {balanced_ternary_to_int(bt)}")

    elif args.command == "calc":
        ta = int_to_balanced_ternary(args.a)
        tb = int_to_balanced_ternary(args.b)
        if args.op == "+":
            result = ternary_add(ta, tb)
        elif args.op == "-":
            result = ternary_sub(ta, tb)
        elif args.op == "*":
            result = ternary_multiply(ta, tb)
        elif args.op == "/":
            if args.b == 0:
                print("Error: division by zero")
                return 1
            result, _ = ternary_div(ta, tb)
        res_int = balanced_ternary_to_int(result)
        print(f"{trits_to_str(ta)} {args.op} {trits_to_str(tb)} = {trits_to_str(result)} ({res_int})")

    elif args.command == "logic":
        _demo_logic()

    elif args.command == "asm":
        source = args.source.replace(";", "\n")
        program = assemble(source)
        print("Machine code:", program)
        print("Disassembly:")
        print(disassemble(program))
        if args.run:
            cpu = TernaryCPU()
            cpu.load_program(program)
            output = cpu.run()
            for line in output:
                print(line)
            print(cpu.dump_state())

    elif args.command == "run":
        with open(args.file) as f:
            source = f.read()
        program = assemble(source)
        cpu = TernaryCPU()
        cpu.load_program(program)
        output = cpu.run()
        for line in output:
            print(line)
        print(cpu.dump_state())

    elif args.command == "disasm":
        print(disassemble(args.codes))

    elif args.command == "demo":
        run_demo(args.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
