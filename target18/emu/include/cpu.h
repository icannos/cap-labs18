//---
//	emu:cpu - emulate the CPU architecture
//
//	This module provides an interface for running binary code assembled for
//	the fictional architecture.
//---

#ifndef	CPU_H
#define	CPU_H

#include <stdio.h>
#include <defs.h>
#include <memory.h>
#include <disasm.h>

/* Some names for the memory pointers */
#define	PC	0
#define	SP	1
#define	A0	2
#define	A1	3

/*
	cpu_t structure
	Holds the values of all the registers and pointers of the CPU. The
	memory object associated with the CPU is used for code and data
	accesses. All pointer values as passed by the CPU to the memory, which
	does not have a copy of them.
*/
typedef struct
{
	memory_t *mem;		/* This one may be shared between CPUs */
	uint64_t r[8];		/* Remember to cast when required! */

	uint z	:1;		/* Zero		ie. x == y */
	uint n	:1;		/* Negative	ie.  (int) x <  (int) y */
	uint c	:1;		/* Carry	ie. (uint) x < (uint) y */
	uint v	:1;		/* Overflow	ie. integer overflow */

	/* Flags for the debugger */
	uint h	:1;		/* Halt, detects loops of one instruction */
	uint m	:1;		/* Memory, indicates changes to memory */
	uint t	:1;		/* Counter, signals counter changes */
	uint s	:1;		/* Stop, indicates stop orders from user */
	uint dbg :1;		/* Is the CPU being debugged? */
	volatile uint sleep :1;	/* Current sleeping */

	uint64_t ptr[4];	/* There are no pointers among r0..r7 */

	uint64_t IPC;		/* PC at beginning of instruction (not a real
				   register) */
} cpu_t;

/*
	cpu_new() -- create a CPU and give it a memory
	The CPU does not retain ownership of the memory object. The memory
	object must be freed by the caller after the CPU is destroyed.

	@arg	mem	Memory to associate the CPU with
	@returns	New CPU object. Throws a fatal error on alloc failure.
*/
cpu_t *cpu_new(memory_t *mem);

/*
	cpu_destroy() -- destroy a cpu_t object (not its memory)

	@arg	cpu	CPU object allocated with cpu_new() to destroy
*/
void cpu_destroy(cpu_t *cpu);

/*
	cpu_dump() -- print CPU state to a stream

	@arg	cpu	Which CPU to inspect
	@arg	stream	Stream to output to
*/
void cpu_dump(cpu_t *cpu, FILE *stream);

/*
	cpu_execute() -- read an execute an instruction
	This function changes the CPU state according to the instruction
	located in the associated memory at address PC. It also updates the
	debugger flags to signal interesting events.

	@arg	cpu	CPU which executes the instruction
*/
void cpu_execute(cpu_t *cpu);

/*
	cpu_counts() -- statistics about executed instructions
	Returns an array of DISASM_INS_COUNT integers indicating the number of
	times each instructions has been executed so far. This value is a
	global count for all cpu_t instances working with the module.

	@returns	Count of executed instructions for each instruction
*/
size_t *cpu_counts(void);

/*
	cpu_instruction_bits_count() -- statistics about the number of bits
	exchanged between the processor and the memory when reading instructions.
 */
uint cpu_instruction_bits_count(void);

/*
	cpu_read_bits_count() -- statistics about the number of bits
	exchanged between the processor and the memory when reading the
	memory.
*/
uint cpu_read_bits_count(void);

/*
	cpu_write_bits_count() -- statistics about the number of bits
	exchanged between the processor and the memory when writing the
	memory.
*/
uint cpu_write_bits_count(void);

/*
	cpu_setctr_count() -- statistics about the number of bit
	sent to the memory when calling `setctr`.
*/
uint cpu_ctr_access_bits_count(void);

/*
	cpu_jump_count() -- statistics about the number of bit
	sent to give the value of the new PC when calling jump, jumpif, call
	or return.
*/
uint cpu_jump_bits_count(void);

/*
	cpu_set_counting_method() -- Set the counting method to `cm`.
	`cm` must be an integer between 1 and 4.
*/
void cpu_set_counting_method(uint cm);

#endif	/* CPU_H */
