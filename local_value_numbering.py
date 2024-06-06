import re
import pdb
def split_into_basic_blocks(program):
    blocks = []
    current_block = []
    for instr in program:
        if instr.startswith("label") or instr.startswith("branch") or instr == "return;":
            if current_block:
                blocks.append(current_block)
                current_block = []
            blocks.append([instr])
        else:
            current_block.append(instr)
    if current_block:
        blocks.append(current_block)
    return blocks

def get_new_name(var, var_table, global_counter):
    if var not in var_table:
        var_table[var] = f"{var}_{global_counter}"
        global_counter += 1
    return var_table[var], global_counter

def generate_instruction(lhs, op, rhs1, rhs2=None):
    if rhs2 is not None:
        return f"{lhs} = {op}({rhs1}, {rhs2});"
    else:
       return f"{lhs} = {op}({rhs1});"


def patch_basic_block(block, var_table):
    if not block:
        return block
    patched_block = []
    start_instr = block[0]
    if start_instr.startswith("label"):
        patched_block.append(start_instr)
        block = block[1:]
    # Add assignments at the beginning of the block
    #for original_var, new_var in var_table.items():
        #if original_var != new_var:
            #patched_block.append(f"{new_var} = {original_var};")
    #add 
    for instr in block:
        if "int2vr" or "float2vr" in instr:
            #patched_block.append(instr)
            newinstr =  instr.split("=")
            var = newinstr[0].strip()
            #pdb.set_trace()
            for original_var, new_var in var_table.items():
               if original_var != new_var:
                  instr[0]
                  patched_block.append(f"{new_var} = {original_var};")
                  #pdb.set_trace()
        else:
            patched_block.append(instr)
    patched_block.extend(block)
    # Add assignments at the end of the block
    for original_var, new_var in var_table.items():
        if original_var != new_var:
            patched_block.append(f"{original_var} = {new_var};")
    #pdb.set_trace()
    return patched_block

def LVN(program):

    global_counter = 0
    value_table = {}  # This will store the RHS -> LHS mappings
    var_table = {}  # This will map original variable names to new names
    replacement_count = 0
    basic_blocks = split_into_basic_blocks(program)
    optimized_program = []
    three_addr_pattern = re.compile(r"(\S+)\s*=\s*(\S+)\((\S+),(\S+)\);")
    two_addr_pattern = re.compile(r"(\S+)\s*=\s*(\S+)\((\S+)\);")
    for block in basic_blocks:
        new_block = []
        for instr in block:
            three_addr_match = three_addr_pattern.match(instr)
            if three_addr_match:
                lhs = three_addr_match.group(1)
                op = three_addr_match.group(2)
                rhs1 = three_addr_match.group(3)
                rhs2 = three_addr_match.group(4)
                if rhs1.startswith("vr") or rhs1.startswith("_new_name"):
                    rhs1, global_counter = get_new_name(rhs1, var_table, global_counter)
                if rhs2.startswith("vr") or rhs2.startswith("_new_name"):
                    rhs2, global_counter = get_new_name(rhs2, var_table, global_counter)
                rhs = f"{op}({rhs1},{rhs2})"
                if rhs in value_table:
                    lhs_new = value_table[rhs]
                    replacement_count += 1
                    new_block.append(f"{lhs} = {lhs_new};")
                else:
                    lhs_new, global_counter = get_new_name(lhs, var_table, global_counter)
                    value_table[rhs] = lhs_new
                    new_block.append(generate_instruction(lhs_new, op, rhs1, rhs2))
            else:
                two_addr_match = two_addr_pattern.match(instr)
                if two_addr_match:
                    lhs = two_addr_match.group(1)
                    op = two_addr_match.group(2)
                    rhs = two_addr_match.group(3)
                    if rhs.startswith("vr") or rhs.startswith("_new_name"):
                        rhs, global_counter = get_new_name(rhs, var_table, global_counter)
                    if lhs.startswith("vr") or lhs.startswith("_new_name"):
                        lhs, global_counter = get_new_name(lhs, var_table, global_counter)
                    #pdb.set_trace()

                   # rhs_combined = f"{op}({rhs})"
                   ## if rhs_combined in value_table:
                    #    lhs_new = value_table[rhs_combined]
                    #    replacement_count += 1
                   #     new_block.append(f"{lhs} = {lhs_new};")
                   # else:
                   #     lhs_new, global_counter = get_new_name(lhs, var_table, global_counter)
                   #     value_table[rhs_combined] = lhs_new
                    new_block.append(generate_instruction(lhs, op, rhs))
                else:
                    new_block.append(instr)
        new_block = patch_basic_block(new_block, var_table)
        optimized_program.extend(new_block)
    #pdb.set_trace()
    return optimized_program, list(var_table.values()), replacement_count