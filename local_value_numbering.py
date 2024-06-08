import re
import pdb
"""
Splits a list of instructions into basic blocks.
Args:
program (list of str): List of three-address code instructions.
Returns:
list of list of str: A list of basic blocks, where each basic block is a list of instructions.
"""
def split_into_basic_blocks(program):
    blocks = []
    current_block = []
    for instr in program:
        if instr.startswith("label") or instr.startswith("branch"):
            if current_block:
                blocks.append(current_block)
                current_block = []
            blocks.append([instr])
        else:
            current_block.append(instr)
    if current_block:
        blocks.append(current_block)
    return blocks
"""
Gets or creates a new name for a variable using a variable table and a global counter.
Args:
var (str): The original variable name.
var_table (dict): A dictionary mapping original variable names to new names.
global_counter (int): A counter used to generate new variable names.
Returns:
tuple: A tuple containing the new variable name and the updated global counter.
"""
def get_new_name(var, var_table, global_counter):
    if var not in var_table:
        var_table[var] = f"{var}_{global_counter}"
        global_counter += 1
    return var_table[var], global_counter

"""
Generates a three-address code instruction.
Args:
lhs (str): The left-hand side variable.
op (str, optional): The operation.
rhs1 (str, optional): The first right-hand side variable.
rhs2 (str, optional): The second right-hand side variable.
Returns:
str: The generated instruction.
"""
def generate_instruction(lhs, op=None, rhs1=None ,rhs2=None):
    if rhs2 is not None:
        return f"{lhs} = {op}({rhs1}, {rhs2});"
    elif rhs1 is not None:
       return f"{lhs} = {op}({rhs1});"
    else:
       return f"{lhs} = {op};"
    
"""
Patches a basic block to update variable names using a variable table.
Args:
block (list of str): A list of instructions in a basic block.
var_table (dict): A dictionary mapping original variable names to new names.
Returns:
list of str: The patched basic block.
"""
def patch_basic_block(block, var_table):
    if not block:
        return block
    patched_block = []
    start_instr = block[0]
    if start_instr.startswith("label"):
        patched_block.append(start_instr)
        block = block[1:]
    for instr in block:
        newmatch = re.search(r'beq\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\);', instr)
        if newmatch:
            arg1 = newmatch.group(1)
            arg2 = newmatch.group(2)
            label = newmatch.group(3).strip()
            newarg1 = var_table[arg1]
            newarg2 = var_table[arg2]
            instr = f"beq({newarg1}, {newarg2}, {label});"
        patched_block.append(instr)
    for original_var, new_var in var_table.items():
               if original_var != new_var:
                  patched_block.append(f"{original_var} = {new_var};")
    return patched_block

"""
Performs Local Value Numbering (LVN) optimization on a program.
Args:
program (list of str): List of three-address code instructions.
Returns:
tuple: A tuple containing the optimized program, a list of new variable names, and the replacement count.
"""
def LVN(program):
    global_counter = 0
    value_table = {}  # This will store the RHS -> LHS mappings
    var_table = {}  # This will map original variable names to new names
    replacement_count = 0
    basic_blocks = split_into_basic_blocks(program)
    optimized_program = []
    three_addr_pattern = re.compile(r"(\S+)\s*=\s*(\S+)\((\S+),(\S+)\);")
    two_addr_pattern = re.compile(r"(\S+)\s*=\s*(\S+)\((\S+)\);") 
    newnamepattern = re.compile(r"(\S+)\s*=\s*((\S+));")
    for block in basic_blocks:
        new_block = []
        for instr in block:
            three_addr_match = three_addr_pattern.match(instr)
            two_addr_match = two_addr_pattern.match(instr)
            name_match = newnamepattern.match(instr)
            if three_addr_match:
                #three_addr_match is for capturing instr such as vr= addi(_new_name0, _new_name1) and similiar patterns with 1 op and 2 rhs arg
                lhs = three_addr_match.group(1)
                op = three_addr_match.group(2)
                rhs1 = three_addr_match.group(3)
                rhs2 = three_addr_match.group(4)
                if rhs1.startswith("vr") or rhs1.startswith("_new_name"):
                    rhs1, global_counter = get_new_name(rhs1, var_table, global_counter)
                if rhs2.startswith("vr") or rhs2.startswith("_new_name"):
                    rhs2, global_counter = get_new_name(rhs2, var_table, global_counter)
                rhs = f"{op}({rhs1},{rhs2})"
                #value table allows for storing past addi operations and replacing new duplicate addi instr with stored values, allowing the implemention of the optimization
                if rhs in value_table:
                    rhs_new = value_table[rhs]
                    lhs_new, global_counter = get_new_name(lhs, var_table, global_counter)
                    replacement_count += 1
                    new_block.append(f"{lhs_new} = {rhs_new};")
                else:
                    lhs_new, global_counter = get_new_name(lhs, var_table, global_counter)
                    value_table[rhs] = lhs_new
                    new_block.append(generate_instruction(lhs_new, op, rhs1, rhs2))
            #two_addr_match is for capturing instr such as x0 = vr2int(vr0) and similiar patterns with 1 op and 1 rhs arg
            elif two_addr_match:
                lhs = two_addr_match.group(1)
                op = two_addr_match.group(2)
                rhs = two_addr_match.group(3)
                if rhs.startswith("vr") or rhs.startswith("_new_name"):
                    rhs, global_counter = get_new_name(rhs, var_table, global_counter)
                if lhs.startswith("vr") or lhs.startswith("_new_name"):
                    lhs, global_counter = get_new_name(lhs, var_table, global_counter)
                new_block.append(generate_instruction(lhs, op, rhs))
            #name_match is for capturing instr such as _new_name2_7 = vr8_14; and similiar patterns with no op and 1 rhs arg
            elif name_match:
                lhs = name_match.group(1)
                rhs = name_match.group(2)
                if rhs.startswith("vr") or rhs.startswith("_new_name"):
                    rhs, global_counter = get_new_name(rhs, var_table, global_counter)
                if lhs.startswith("vr") or lhs.startswith("_new_name"):
                    lhs, global_counter = get_new_name(lhs, var_table, global_counter)
                new_block.append(generate_instruction(lhs, rhs))
            else:
                new_block.append(instr)
        new_block = patch_basic_block(new_block, var_table)
        optimized_program.extend(new_block)
    return optimized_program, list(var_table.values()), replacement_count