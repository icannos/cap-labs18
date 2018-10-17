from APICode18 import Instru3A

"""
This is only done to rewrite
- conditional jumps
into the target machine instructions.
This file should not be modified. TARGET18 Version, Aug 2018
"""


def replace_meta_i(old_i):
    """Replace Meta Instructions with real Machine Instructions"""
    ins, args = old_i.unfold()
    if ins == 'cond_jump':
        target_label, op1, c, op2 = args
        return [
            Instru3A('cmp', op1, op2),
            Instru3A('jumpif ', c,  target_label),
        ]
    else:
        return


def replace_all_meta(src_prog):
    #    print('coucou')
    src_prog.iter_instructions(replace_meta_i)
