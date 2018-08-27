#include <disasm.h>
#include <util.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define	r4(n)	n, n, n, n
#define	r8(n)	r4(n), r4(n)
#define r16(n)	r8(n), r8(n)

/* Associate a unique instruction id to all sequences of 8 bits. This table
   avoids having to read 4 bits, test if it's a valid instruction (Huffman
   encoding), if not, read another bit, test again... until 8 bits.
   This is the default encoding; --load-huffman can change it */
static const uint8_t default_ids[256] = {
	r16(0), r16(1), r16(2), r16(3), r16(4), r16(5), r16(6), r16(7),
	r16(8), r8(9), r8(10), r16(11), r16(12),
	r4(13), r4(14), r4(15), r4(16), r4(17), r4(18), r4(19), r4(20),
	21, 21, 22, 22, 23, 23, 24, 24, 25, 25, 26, 26, 27, 27, 28, 28,
	29, 29, 30, 30, 31, 31, 32, 32, 33, 33, 34, 34, 35, 36, 37, 38,
};

/* Indicate the length of each unique instruction id. */
static uint8_t length[DISASM_INS_COUNT] = {
	r8(4), 4, 5, 5, 4, 4, r8(6), r8(7), r4(7), 7, 7, 8, 8, 8, 8,
};

static uint opcode_size = 8;
static uint8_t *ids;
/* Record if we have to manually free array pointed by ids */
static uint8_t instr_set_dynamic_alloc = 0;


/* Instruction set. The entry at each unique id represents the associated
   instruction, with a predefined format. The first three letters are elements
   of the arg_t enumeration and represent the instruction's arguments. The
   fifth letter is an element of the ctgy_t enumeration and classifies the
   instruction. The mnemonic is read starting at index 6. */
static const char instructions[DISASM_INS_COUNT][16] = {
	"rr- A add2",	"rl- A add2i",	"rr- A sub2",	"rl- A sub2i",
	"rr- T cmp",	"rc- T cmpi",	"rr- L let",	"rc- L leti",
	"drh A shift",	"psr M readze", "psr M readse",	"a-- J jump",
	"oa- J jumpif",	"rr- A or2",	"rl- A or2i",	"rr- A and2",
	"rl- A and2i",	"psr M write",	"a-- J call",	"pr- C setctr",
	"pr- C getctr",	"sr- M push",	"--- J return",	"rrr A add3",
	"rrl A add3i",	"rrr A sub3",	"rrl A sub3i",	"rrr A and3",
	"rrl A and3i",	"rrr A or3",	"rrl A or3i",	"rrr A xor3",
	"rrl A xor3i",	"rrh A asr3",	"l-- C sleep",	"r-- A rand",
	"ra- M lea",	"fr- C print",	"fl- C printi",
};

/* Number of metadata bytes in the array above. The instruction mnemonic starts
   at offset INTSR_INFORMATION_BITS. */
#define INSTR_INFORMATION_BITS 6

/* load_encoding() -- load a huffman encoding as instruction set
   Loads the default encoding if "filename" is NULL. Returns non-zero
   on failure */
uint load_encoding(const char *filename)
{
	/* Use the default instruction set when no filename is specified */
	if(!filename)
	{
		ids = (uint8_t *)default_ids;
		return 0;
	}

	FILE *huffman_f = fopen(filename, "r");
	if(!huffman_f) return 1;

	/* Read the size of the larger opcode */
	fscanf(huffman_f, "%u\n", &opcode_size);

	/* Allocate an array able to store any opcode */
	ids = malloc((1 << opcode_size) * sizeof *ids);
	instr_set_dynamic_alloc = 1;

	char mnemonic[64];
	uint iid;
	uint size;
	char opcode_str[128];
	uint64_t opcode;

	for (int i = 0; i < DISASM_INS_COUNT; i++)
	{
		fscanf(huffman_f, "%63[^ ] %u %u %127[01]\n", mnemonic, &iid,
			&size, opcode_str);

		fprintf(stderr, "%s %u %u %s\n", mnemonic, iid, size,
			opcode_str);

		/* Build up the integer representation of that opcode */
		opcode = 0;
		for(int j = 0; opcode_str[j]; j++) if(opcode_str[j] == '1')
		{
			opcode |= ((1ul << opcode_size) >> (j + 1));
		}

		/* Fill the corresponding part in the instruction id array */
		for (int j = 0; j < (1 << (opcode_size - size)); j++)
			ids[opcode + j] = iid;

		/* Set the size of that opcode */
		length[iid] = size;
	}

	fclose(huffman_f);
	return 0;

}
/* free_encoding() -- free if needed instruction set array */
void free_encoding()
{
	if(instr_set_dynamic_alloc) free(ids);
}

/* disasm_opcode() -- read an instruction code */
uint disasm_opcode(memory_t *mem, uint64_t *ptr, const char **format)
{
	uint mask = (1ul << opcode_size) - 1;
	uint opcode = memory_read(mem, *ptr, opcode_size) & mask;
	uint id = ids[opcode];

	*ptr += length[id];
	if (format) *format = instructions[id];

	return id;
}

/* disasm_format() -- get the format for a given instruction */
const char *disasm_format(uint opcode)
{
	if (opcode >= DISASM_INS_COUNT) return NULL;
	return instructions[opcode];
}

/* disasm_reg() -- read a register number */
uint disasm_reg(memory_t *mem, uint64_t *ptr)
{
	*ptr += 3;
	return memory_read(mem, *ptr - 3, 3);
}

/* disasm_dir() -- read a shift direction bit */
uint disasm_dir(memory_t *mem, uint64_t *ptr)
{
	*ptr += 1;
	return memory_read(mem, *ptr - 1, 1);
}

/* disasm_cond() -- read a jump condition type */
uint disasm_cond(memory_t *mem, uint64_t *ptr)
{
	*ptr += 3;
	return memory_read(mem, *ptr - 3, 3);
}

/* disasm_addr() -- read a relative address */
int64_t disasm_addr(memory_t *mem, uint64_t *ptr, uint *size_arg)
{
	/* Length of header, size of address, 3 header bits of address */
	uint offset = 1, size = 8;
	uint head = memory_read(mem, *ptr, 3);

	/* Headers of size 2 start with 10, which allows 100 and 101 */
	if (head == 4 || head == 5) offset = 2, size = 16;
	/* Headers of size 3 only include 110 and 111 */
	else if (head >= 6) offset = 3, size = 1 << (head - 1);

	*ptr += offset + size;
	if (size_arg) *size_arg = size;
	uint64_t addr = memory_read(mem, *ptr - size, size);

	return sign_extend(addr, size);
}

/* disasm_lconst() -- read a zero-extended constant */
uint64_t disasm_lconst(memory_t *mem, uint64_t *ptr, uint *size_arg)
{
	/* Length of header, size of constant, 3 header bits of constant */
	uint offset = 1, size = 1;
	uint head = memory_read(mem, *ptr, 3);

	/* Headers of size 2 start with 10, which allows 100 and 101 */
	if (head == 4 || head == 5) offset = 2, size = 8;
	/* Headers of size 3 only include 110 and 111 */
	else if (head >= 6) offset = 3, size = 1 << (head - 1);

	*ptr += offset + size;
	if (size_arg) *size_arg = size;

	uint64_t t = memory_read(mem, *ptr - size, size);
	return t;
}

/* disasm_aconst() -- read a sign-extended constant */
int64_t disasm_aconst(memory_t *mem, uint64_t *ptr, uint *size_arg)
{
	uint size;

	/* Let disasm_lconst() do the bit retrieval job for us */
	uint64_t cst = disasm_lconst(mem, ptr, &size);
	if (size_arg) *size_arg = size;

	return sign_extend(cst, size);
}

/* disasm_shift() -- read a shift constant */
uint disasm_shift(memory_t *mem, uint64_t *ptr)
{
	uint shift = memory_read(mem, *ptr, 7);

	/* If the first bit is set, then the value was just 1 */
	if (shift & 0x40) shift = 1, (*ptr)++;
	/* Otherwise, we have 6 bits which represent the shift value */
	else *ptr += 7;

	return shift;
}

/* disasm_size() -- read a memory operation size */
uint disasm_size(memory_t *mem, uint64_t *ptr)
{
	uint size = memory_read(mem, *ptr, 3);
	/* Values lower than 4 mean 00x or 01x, thus sizes of length 2 */
	*ptr += 3 - (size < 4);

	/* Cheap formulas to get the size "efficiently" */
	if (size < 4) return 1 + 3 * (size >> 1);
	return 1 << (size - 1);
}

/* disasm_pointer() -- read a pointer id */
uint disasm_pointer(memory_t *mem, uint64_t *ptr)
{
	*ptr += 2;
	return memory_read(mem, *ptr - 2, 2);
}

/* disasm_pformat() -- read a print format */
uint disasm_pformat(memory_t *mem, uint64_t *ptr)
{
	*ptr += 4;
	return memory_read(mem, *ptr - 4, 4);
}

uint disasm_instr_length(uint id)
{
	return length[id];
}

const char *disasm_instruction_name(uint id)
{
	return instructions[id] + INSTR_INFORMATION_BITS;
}
