# Ternary Computing Emulator

A full **balanced ternary computing emulator** — a simulated CPU that operates on
base-3 digits (trits: **-1, 0, 1**) instead of binary bits.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## What It Is

This emulator models a complete ternary computer:

- **Balanced ternary ALU** — arithmetic directly on trit representations
- **Virtual CPU** — 27 registers, memory, ALU, and flag registers
- **Instruction set** — 20+ instructions (arithmetic, logic, control flow, I/O)
- **Assembler / Disassembler** — human-readable assembly ↔ machine code
- **Interactive REPL** — step through programs, inspect state
- **Cross-platform binaries** — standalone executables for Windows, macOS, Linux

## Quick Start

### Install from source

```bash
git clone https://github.com/theeteeshrimp/ternary-computing-emulator.git
cd ternary-computing-emulator
pip install -e .
```

### Or download a standalone binary

Download the latest release for your platform from the
[Releases](https://github.com/theeteeshrimp/ternary-computing-emulator/releases) page.

### Try it

```bash
# Interactive REPL
ternary-emulator

# Convert a number
ternary-emulator convert 42

# Arithmetic
ternary-emulator calc 7 + 5
ternary-emulator calc -3 * 4

# Show logic table
ternary-emulator logic

# Run a demo
ternary-emulator demo fibonacci

# Assemble and run a program
ternary-emulator asm "ADD R0, R1, R2; HALT"

# Run an assembly file
ternary-emulator run program.asm
```

## The REPL

The interactive REPL is the best way to explore:

```text
$ ternary-emulator

═══════════════════════════════════════════════════════
  ⢕⣿⢀⣏⣿⢢⡕⣆⢺⣋⢟  Ternary Computing Emulator v1.0.0
  Type 'help' for commands, 'quit' to exit
═══════════════════════════════════════════════════════

ternary> convert 42
  42 → 111T (balanced ternary)

ternary> add 5 3
  1T + 1T1 = 11T (8)

ternary> logic
  Three-Valued Logic Gates
  ...
```

### REPL Commands

| Command | Description |
|---------|-------------|
| `convert <n>` | Convert decimal ↔ balanced ternary |
| `add/sub/mul/div <a> <b>` | Ternary arithmetic |
| `logic` | Show three-valued logic table |
| `asm <source>` | Assemble instructions |
| `disasm <codes>` | Disassemble machine code |
| `load <file>` | Load assembly file |
| `run [file]` | Execute program |
| `step` | Execute one instruction |
| `state` | Dump CPU registers & flags |
| `mem <addr> [count]` | Inspect memory |
| `reg <name> [value]` | Get/set register |
| `demo <name>` | Run built-in demos |

## Assembly Language

```asm
; Hello Fibonacci — compute first 10 Fibonacci numbers
    ; R0 = fib(n), R1 = fib(n+1), R2 = temp, R3 = counter
    ADD  R0, R1, R2    ; R2 = R0 + R1
    MOV  R0, R1         ; R0 = R1
    MOV  R1, R2         ; R1 = R2
    SUB  R3, R3, 1      ; decrement counter
    JNZ  R3, loop       ; if R3 != 0, goto loop
    HALT
```

Supported instructions:

| Instruction | Operands | Description |
|-------------|----------|-------------|
| `NOP` | — | No operation |
| `HALT` | — | Stop execution |
| `MOV` | src, dst | Copy register |
| `LOAD` | reg, [addr_reg] | Load from memory |
| `STORE` | reg, [addr_reg] | Store to memory |
| `ADD` | a, b, dst | Ternary add |
| `SUB` | a, b, dst | Ternary subtract |
| `MUL` | a, b, dst | Ternary multiply |
| `DIV` | a, b, dst | Ternary divide |
| `NEG` | src, dst | Negate |
| `AND/OR/XOR` | a, b, dst | Three-valued logic |
| `NOT` | src, dst | Bitwise negate |
| `SHL/SHR` | reg, amt, dst | Shift left/right |
| `CMP` | a, b | Compare, set flags |
| `JMP` | addr | Unconditional jump |
| `JZ/JN/JP` | reg, addr | Conditional jump |
| `CALL/RET` | addr | Subroutine call/return |
| `PUSH/POP` | reg | Stack operations |
| `IN/OUT` | port, reg | I/O |

## Architecture

```
┌──────────────────────────────────────────────┐
│              Ternary CPU                      │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ R0  -R26 │  │ PC  SR   │  │ SP  FLAGS │  │
│  │ (27 regs)│  │          │  │           │  │
│  └──────────┘  └──────────┘  └───────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │         Balanced Ternary ALU           │  │
│  │  ADD SUB MUL DIV NEG AND OR XOR NOT   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │       Ternary Memory (trit-addressed)  │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

## Building Standalone Binaries

Build for the current platform:

```bash
pip install pyinstaller
python scripts/build_binary.py
```

This produces a standalone executable in `dist/` for:
- **Windows**: `ternary-emulator.exe`
- **macOS**: `ternary-emulator` (universal2)
- **Linux**: `ternary-emulator`

## Cross-Platform Releases

Binaries can be built on each target platform or cross-compiled via GitHub Actions.

See `.github/workflows/release.yml` for the CI/CD pipeline.

## Why Balanced Ternary?

Balanced ternary uses three digits **{-1, 0, 1}** — naturally representing
negative, neutral, and positive states. This gives it interesting properties:

- **No sign bit needed** — negative numbers are first-class citizens
- **Symmetric rounding** — truncation = rounding to nearest
- **Natural sparsity** — `0` means "no computation needed"
- **Higher information density** — 1 trit ≈ 1.585 bits

The [Setun](https://en.wikipedia.org/wiki/Setun) computer (1958, Moscow State University)
was a real ternary computer that proved the concept in hardware.

## License

MIT License — see [LICENSE](LICENSE).
