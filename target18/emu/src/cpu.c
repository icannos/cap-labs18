#include <stdlib.h>
#include <errors.h>
#include <disasm.h>
#include <cpu.h>
#include <util.h>
#include <unistd.h>

/* Bit of a hack to gt dbglog() */
#define _DEBUGGER_SOURCE
#include <debugger.h>

/* cpu_new() -- create a CPU and give it a memory */
cpu_t *cpu_new(memory_t *mem)
{
	if(!mem) ifatal("cpu_new(): NULL memory argument");

	cpu_t *cpu = malloc(sizeof *cpu);
	if(!cpu) ifatal("# cpu_new(): cannot allocate memory");

	cpu->mem = mem;

	/* Initialize registers and flags */
	for(int i = 0; i < 8; i++) cpu->r[i] = 0x0000000000000000l;
	cpu->z = 0;
	cpu->n = 0;
	cpu->c = 0;
	cpu->v = 0;

	cpu->h = 0;
	cpu->m = 0;
	cpu->t = 0;
	cpu->s = 0;
	cpu->dbg = 0;

	/* Initialize pointers according to the memory geometry */
	cpu->ptr[PC] = 0x0000000000000000l;
	cpu->ptr[SP] = mem->stack;
	cpu->ptr[A0] = mem->data;
	cpu->ptr[A1] = mem->vram;

	/* Program Counter at beginning of instruction (this is an
	   implementation facility, not a real register) */
	cpu->IPC = cpu->ptr[PC];

	return cpu;
}

/* cpu_destroy() -- destroy a cpu_t object (not its memory) */
void cpu_destroy(cpu_t *cpu)
{
	free(cpu);
}



//---
//	Emulation layer
//
//	Please refer to the ISA and the documentation (/doc) for more detailed
//	information about the behavior of these instructions, although it can
//	mostly be inferred from their name and implementation.
//---

/* The number of times each instructions has been executed */
static size_t counts[DISASM_INS_COUNT] = { 0 };

/*
   Stores the number of bits exchanged between the memory and the processor
   when reading an instruction.
*/
static uint instruction_bits_count = 0;

/* Number of bits exchanged via read instructions. */
static uint read_bits_count = 0;

/* Number of bits exchanged via write instructions. */
static uint write_bits_count = 0;

/* Number of bits sent to the memory when calling jump/jumpif/call/return */
static uint jump_bits_count = 0;

/* Number of bits sent the the memory when calling `setctr` */
static uint ctr_access_bits_count = 0;

static uint counting_method = 4;

/*
	set_flags()
	A quick routine to set the flags of the processor.

	@arg	cpu		The CPU you're working with
	@arg	result		Calculation result, for flags Z and N
	@arg	carry		Carry flag (or -1 for no change)
	@arg	overflow	Overflow flag (or -1 for no change)
*/
static void set_flags(cpu_t *cpu, int64_t result, int carry, int overflow)
{
	cpu->z = (result == 0);
	cpu->n = (result < 0);
	if(carry >= 0) cpu->c = carry;
	if(overflow >= 0) cpu->v = overflow;
}

/*
	carry_add()
	Quick calculate and return carry of x + y.
*/
static int carry_add(uint64_t x, uint64_t y)
{
	/* Carry happens when x >= 2^64 - y, which is pretty much the same as
	   -y, except for y = 0 where the carry happens when calculating -y */
	return y && (x >= -y);
}

/*
	vflow_add()
	Quick calculate and return overflow of x + y.
*/
static int vflow_add(int64_t x, int64_t y)
{
	/* Overflow happens when both operands have the same sign, but the
	   result changes sign due to overflow */
	return ((x ^ y) >= 0) && ((x ^ (x + y)) < 0);
}

/*
	When a counter is set the a new value, only the least significant bits
	are sent. Return the number of bits that need to be sent to change
	a counter in this way.
*/
uint sent_ctr_bits(uint64_t prev_val, uint64_t new_val)
{
	// If the counting method is 1, 2 or 3, 64 bits are sent at each
	// change.
	if (counting_method < 4)
		return 64;

	// If the counting method is 4, only the useful bits are sent.
	uint64_t diff = prev_val ^ new_val;
	uint changes = 0;

	for ( ; diff != 0; diff >>= 1)
		changes++;

	return changes;
}

/* A useful shorthand that calls disasm_*() functions */
#define	get(type, ...) disasm_ ## type (cpu->mem, &cpu->ptr[PC], ##__VA_ARGS__)

/* TODO - Document this in a satisfactory way */

static void add2(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);

	int carry	= carry_add(cpu->r[rd], cpu->r[rs]);
	int overflow	= vflow_add(cpu->r[rd], cpu->r[rs]);

	cpu->r[rd] += cpu->r[rs];
	set_flags(cpu, cpu->r[rd], carry, overflow);
}

static void add2i(cpu_t *cpu)
{
	uint rd = get(reg);
	uint64_t cst = get(lconst, NULL);

	int carry	= carry_add(cpu->r[rd], cst);
	int overflow	= vflow_add(cpu->r[rd], cst);

	cpu->r[rd] += cst;
	set_flags(cpu, cpu->r[rd], carry, overflow);
}

static void sub2(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);

	int borrow	= cpu->r[rd] < cpu->r[rs];
	int overflow	= vflow_add(cpu->r[rd], -cpu->r[rs]);

	cpu->r[rd] -= cpu->r[rs];
	set_flags(cpu, cpu->r[rd], borrow, overflow);
}

static void sub2i(cpu_t *cpu)
{
	uint rd = get(reg);
	uint64_t cst = get(lconst, NULL);

	int borrow	= cpu->r[rd] < cst;
	int overflow	= vflow_add(cpu->r[rd], -cst);

	cpu->r[rd] -= cst;
	set_flags(cpu, cpu->r[rd], borrow, overflow);
}

static void cmp(cpu_t *cpu)
{
	uint rm = get(reg), rn = get(reg);

	int borrow	= cpu->r[rm] < cpu->r[rn];
	int overflow	= vflow_add(cpu->r[rm], -cpu->r[rn]);

	set_flags(cpu, cpu->r[rm] - cpu->r[rn], borrow, overflow);
}

static void cmpi(cpu_t *cpu)
{
	uint rm = get(reg);
	int64_t cst = get(aconst, NULL);

	int carry	= cpu->r[rm] < (uint64_t)cst;
	int overflow	= vflow_add(cpu->r[rm], -cst);

	set_flags(cpu, cpu->r[rm] - cst, carry, overflow);
}

static void let(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	cpu->r[rd] = cpu->r[rs];
}

static void leti(cpu_t *cpu)
{
	uint rd = get(reg);
	int64_t cst = get(aconst, NULL);
	cpu->r[rd] = (uint64_t)cst;
}

static void shift(cpu_t *cpu)
{
	uint dir = get(dir), rd = get(reg), shift = get(shift);

	if(dir)
	{
		cpu->c = (cpu->r[rd] >> (shift - 1)) & 1;
		cpu->r[rd] >>= shift;
	}
	else
	{
		cpu->c = (int64_t)(cpu->r[rd] << (shift - 1)) < 0;
		cpu->r[rd] <<= shift;
	}

	set_flags(cpu, cpu->r[rd], -1, -1);
}

static void readze(cpu_t *cpu)
{
	uint ptr = get(pointer), size = get(size), rd = get(reg);
	cpu->r[rd] = memory_read(cpu->mem, cpu->ptr[ptr], size);
	cpu->ptr[ptr] += size;

	/* Balance the automatic instruction bit count of cpu_execute() */
	if(ptr == PC) instruction_bits_count -= size;
	read_bits_count += size;
}

static void readse(cpu_t *cpu)
{
	uint ptr = get(pointer), size = get(size), rd = get(reg);
	uint64_t data = memory_read(cpu->mem, cpu->ptr[ptr], size);
	cpu->r[rd] = sign_extend(data, size);
	cpu->ptr[ptr] += size;

	/* Balance the automatic instruction bit count of cpu_execute() */
	if(ptr == PC) instruction_bits_count -= size;
	read_bits_count += size;
}

static void jump(cpu_t *cpu)
{
	int64_t diff = get(addr, NULL);

	/* Deduce "diff" bits from the statistics to balance the increment
	   performed by cpu_execute() */
	instruction_bits_count -= diff;

	jump_bits_count += sent_ctr_bits(cpu->ptr[PC], cpu->ptr[PC] + diff);
	cpu->ptr[PC] += diff;
	/* Detect "halt" loops */
	if(cpu->ptr[PC] == cpu->IPC) cpu->h = 1;
}

static void jumpif(cpu_t *cpu)
{
	int z = cpu->z, n = cpu->n, v = cpu->v, c = cpu->c;
	int conds[] = {
		z, !z, !z && (n == v), n ^ v, n == v, !c, c, z || (n ^ v),
	};
	uint cnd = get(cond);
	int64_t diff = get(addr, NULL);

	if(!conds[cnd]) return;

	/* Deduce "diff" bits from the statistics to balance the increment
	   performed by cpu_execute() */
	instruction_bits_count -= diff;

	jump_bits_count += sent_ctr_bits(cpu->ptr[PC], cpu->ptr[PC] + diff);
	cpu->ptr[PC] += diff;
	/* Detect "halt" loops */
	if(cpu->ptr[PC] == cpu->IPC) cpu->h = 1;
}

static void or2(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	cpu->r[rd] |= cpu->r[rs];
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void or2i(cpu_t *cpu)
{
	uint rd = get(reg);
	uint64_t cst = get(lconst, NULL);
	cpu->r[rd] |= cst;
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void and2(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	cpu->r[rd] &= cpu->r[rs];
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void and2i(cpu_t *cpu)
{
	uint rd = get(reg);
	uint64_t cst = get(lconst, NULL);
	cpu->r[rd] &= cst;
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void _write(cpu_t *cpu)
{
	uint ptr = get(pointer), size = get(size), rs = get(reg);
	memory_write(cpu->mem, cpu->ptr[ptr], cpu->r[rs], size);
	cpu->ptr[ptr] += size;

	/* Balance the automatic instruction bit count of cpu_execute() */
	if(ptr == PC) instruction_bits_count -= size;
	write_bits_count += size;

	/* Let the debugger know about this memory change */
	cpu->m = 1;
}

static void call(cpu_t *cpu)
{
	int64_t target = get(addr, NULL);
	if (counting_method == 1)
		ctr_access_bits_count += 64;
	jump_bits_count += sent_ctr_bits(cpu->ptr[PC], cpu->r[7]);
	cpu->r[7] = cpu->ptr[PC];

	/* This is a jump, so we also need to correct the statistics */
	instruction_bits_count -= target - cpu->ptr[PC];
	cpu->ptr[PC] = target;
}

static void setctr(cpu_t *cpu)
{
	uint ptr = get(pointer), rs = get(reg);

	if(ptr == PC) instruction_bits_count -= cpu->r[rs] - cpu->ptr[PC];

	/* Changes to the counters must be passed on to the memory */
	ctr_access_bits_count += sent_ctr_bits(cpu->ptr[ptr], cpu->r[rs]);

	cpu->ptr[ptr] = cpu->r[rs];

	/* Let the debugger know about this counter change */
	cpu->t = 1;
}

static void getctr(cpu_t *cpu)
{
	uint ptr = get(pointer), rd = get(reg);
	cpu->r[rd] = cpu->ptr[ptr];
	if (counting_method == 0)
		// Sending 64 bits from the memory to get the counter value.
		ctr_access_bits_count += 64;

}

static void push(cpu_t *cpu)
{
	uint size = get(size), rs = get(reg);
	cpu->ptr[SP] -= size;

	/* TODO: Use a proper exception when raising stack overflow */
	if((int64_t)cpu->ptr < 0 || cpu->ptr[SP] < cpu->mem->text)
		fatal("Stack overflow (SP = %lu) at PC = %lu\n", cpu->ptr[SP],
		cpu->ptr[PC]);
	memory_write(cpu->mem, cpu->ptr[SP], cpu->r[rs], size);

	if (counting_method == 1)
		// Sending 64 bits from the memory to get the PC value.
		ctr_access_bits_count += 64;
	if (counting_method <= 2)
		// Sending 64 bits to the memory to set the new PC value.
		ctr_access_bits_count += 64;

	write_bits_count += size;

	/* Let the debugger know about this memory change */
	cpu->m = 1;
}

static void _return(cpu_t *cpu)
{
	/* Cancel out the yet-to-happen automatic increase */
	instruction_bits_count -= cpu->r[7] - cpu->ptr[PC];

	jump_bits_count += sent_ctr_bits(cpu->ptr[PC], cpu->r[7]);
	cpu->ptr[PC] = cpu->r[7];

	/* The 64 bits from r7 indicating the value of the new PC are sent */
	/* the memory. */
}

static void add3(cpu_t *cpu)
{
	uint rd = get(reg), rm = get(reg), rn = get(reg);

	int carry	= carry_add(cpu->r[rm], cpu->r[rn]);
	int overflow	= vflow_add(cpu->r[rm], cpu->r[rn]);

	cpu->r[rd] = cpu->r[rm] + cpu->r[rn];
	set_flags(cpu, cpu->r[rd], carry, overflow);
}

static void add3i(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	uint64_t cst = get(lconst, NULL);

	int carry	= carry_add(cpu->r[rs], cst);
	int overflow	= vflow_add(cpu->r[rs], cst);

	cpu->r[rd] = cpu->r[rs] + cst;
	set_flags(cpu, cpu->r[rd], carry, overflow);
}

static void sub3(cpu_t *cpu)
{
	uint rd = get(reg), rm = get(reg), rn = get(reg);

	int borrow	= cpu->r[rm] < cpu->r[rn];
	int overflow	= vflow_add(cpu->r[rm], -cpu->r[rn]);

	cpu->r[rd] = cpu->r[rm] - cpu->r[rn];
	set_flags(cpu, cpu->r[rd], borrow, overflow);
}

static void sub3i(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	uint64_t cst = get(lconst, NULL);

	int borrow	= cpu->r[rs] < cst;
	int overflow	= vflow_add(cpu->r[rs], -cst);

	cpu->r[rd] = cpu->r[rs] - cst;
	set_flags(cpu, cpu->r[rd], borrow, overflow);
}

static void or3(cpu_t *cpu)
{
	uint rd = get(reg), rm = get(reg), rn = get(reg);
	cpu->r[rd] = cpu->r[rm] | cpu->r[rn];
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void or3i(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	uint64_t cst = get(lconst, NULL);
	cpu->r[rd] = cpu->r[rs] | cst;
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void and3(cpu_t *cpu)
{
	uint rd = get(reg), rm = get(reg), rn = get(reg);
	cpu->r[rd] = cpu->r[rm] & cpu->r[rn];
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void and3i(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	uint64_t cst = get(lconst, NULL);
	cpu->r[rd] = cpu->r[rs] & cst;
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void xor3(cpu_t *cpu)
{
	uint rd = get(reg), rm = get(reg), rn = get(reg);
	cpu->r[rd] = cpu->r[rm] ^ cpu->r[rn];
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void xor3i(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg);
	uint64_t cst = get(lconst, NULL);
	cpu->r[rd] = cpu->r[rs] ^ cst;
	set_flags(cpu, cpu->r[rd], 0, -1);
}

static void asr3(cpu_t *cpu)
{
	uint rd = get(reg), rs = get(reg), shift = get(shift);
	int carry = ((int64_t)cpu->r[rs] >> (shift - 1)) & 1;

	int64_t result = (int64_t)cpu->r[rs] >> shift;
	cpu->r[rd] = (uint64_t)result;
	set_flags(cpu, result, carry, -1);
}

/* TODO - Use a proper debugger-related exception handling scheme for these */

static void _sleep(cpu_t *cpu)
{
	cpu->sleep = 1;
	__attribute__((unused))
	uint64_t cst = get(lconst, NULL);

	do pause();
	while(cpu->sleep);
}

static void _rand(cpu_t *cpu)
{
	uint rd = get(reg);
	cpu->r[rd] = ((uint64_t)rand() << 32) | rand();
}

static void lea(cpu_t *cpu)
{
	uint reg = get(reg);
	int64_t diff = get(addr, NULL);

	cpu->r[reg] = cpu->ptr[PC] + diff;
}

static void print_common(cpu_t *cpu, uint fmt, uint64_t val)
{
	int (*print)(const char *format, ...);
	int byte;

	print = (cpu->dbg) ? dbglog : printf;

	if(fmt == 0) print("%c", val & 0xff);
	if(fmt == 1) print("%ld", val);
	if(fmt == 2) print("%#lx", val);
	if(fmt == 3) while(1)
	{
		byte = memory_read(cpu->mem, val, 8);
		if(!byte) break;
		val += 8;
		print("%c", byte);
	}
}

static void print(cpu_t *cpu)
{
	uint fmt = get(pformat);
	uint reg = get(reg);
	print_common(cpu, fmt, cpu->r[reg]);
}

static void printi(cpu_t *cpu)
{
	uint fmt = get(pformat);
	uint64_t cst;

	/* Signed constants */
	if(fmt == 1) cst = get(aconst, NULL);
	else cst = get(lconst, NULL);

	print_common(cpu, fmt, cst);
}

/* Array of all instruction routines */
static void (*instructions[DISASM_INS_COUNT])(cpu_t *cpu) = {
	add2,		add2i,		sub2,		sub2i,
	cmp,		cmpi,		let,		leti,
	shift,		readze,		readse,		jump,
	jumpif,		or2,		or2i,		and2,
	and2i,		_write,		call,		setctr,
	getctr,		push,		_return,	add3,
	add3i,		sub3,		sub3i,		and3,
	and3i,		or3,		or3i,		xor3,
	xor3i,		asr3,		_sleep,		_rand,
	lea,		print,		printi,
};

/* cpu_dump() -- print CPU state to a stream */
void cpu_dump(cpu_t *cpu, FILE *stream)
{
	if(stream && !cpu) fputs("<null cpu>", stream);
	if(!stream || !cpu) return;

	fprintf(stream, "r0 = %016lx    PC = %08lx\n", cpu->r[0],cpu->ptr[PC]);
	fprintf(stream, "r1 = %016lx    SP = %08lx\n", cpu->r[1],cpu->ptr[SP]);
	fprintf(stream, "r2 = %016lx    A0 = %08lx\n", cpu->r[2],cpu->ptr[A0]);
	fprintf(stream, "r3 = %016lx    A1 = %08lx\n", cpu->r[3],cpu->ptr[A1]);
	fprintf(stream, "r4 = %016lx\n", cpu->r[4]);
	fprintf(stream, "r5 = %016lx    Z = %d\n", cpu->r[5], cpu->z);
	fprintf(stream, "r6 = %016lx    N = %d\n", cpu->r[6], cpu->z);
	fprintf(stream, "r7 = %016lx    C = %d\n", cpu->r[7], cpu->c);
}

/* cpu_execute() -- read an execute an instruction */
void cpu_execute(cpu_t *cpu)
{
	cpu->IPC = cpu->ptr[PC];
	uint opcode = disasm_opcode(cpu->mem, &cpu->ptr[PC], NULL);

	/* Provide statistics about the number of executed instructions */
	counts[opcode]++;

	instructions[opcode](cpu);

	/* Automatically increase the number of instruction bits by the
	   difference between the values of PC before and after executing the
	   instructions.
	   Instructions that affect PC (jumps...) balance this manually */
	instruction_bits_count += cpu->ptr[PC] - cpu->IPC;
}

/* cpu_counts() -- statistics about executed instructions */
size_t *cpu_counts(void)
{
	return counts;
}

uint cpu_instruction_bits_count(void)
{
	return instruction_bits_count;
}

uint cpu_read_bits_count(void)
{
	return read_bits_count;
}

uint cpu_write_bits_count(void)
{
	return write_bits_count;
}

uint cpu_jump_bits_count(void)
{
	return jump_bits_count;
}

uint cpu_ctr_access_bits_count(void)
{
	return ctr_access_bits_count;
}

void cpu_set_counting_method(uint cm)
{
	counting_method = cm;
}
