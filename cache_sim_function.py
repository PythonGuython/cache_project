import gzip
import math
import matplotlib.pyplot as plt
import pandas as pd

def simulate(trace_name, cachesize_kb, associativity, blocksize_bytes, miss_penalty, clock_period):

    print(f"Starting sim with parameters: cachesize_kb = {cachesize_kb}, associativity = {associativity}, blocksize_bytes = {blocksize_bytes}, miss_penalty = {miss_penalty}, clock_period = {clock_period} ")

    def get_tag(address, n_upper):
        '''
        input address as int
        '''
        num = address
        binary = bin(num)[2:]
        diff = 32 - len(binary)

        if diff != 0:
            binary = '0'*diff + binary
        
        return int(binary[:n_upper],2)

    def LRU(index, valid_bits, dirty_bits, cache_tags):

        valid_bits.append(valid_bits.pop(index))
        dirty_bits.append(dirty_bits.pop(index))
        cache_tags.append(cache_tags.pop(index))
        return valid_bits, dirty_bits, cache_tags

    extra_miss_pen = 0

    if blocksize_bytes == 32:
        extra_miss_pen = 2
    elif blocksize_bytes == 64:
        extra_miss_pen = 6
    elif blocksize_bytes == 128:
        extra_miss_pen = 14

    store_hits = 0
    store_misses = 0
    load_hits = 0
    load_misses = 0
    dirty_evictions = 0
    total_cycles = 0
    instr_count = 0
    memory_accesses = 0
    miss_penalties = 0

    with gzip.open(trace_name, 'rb') as file:
        file_content = file.read().splitlines()

    memory_accesses = len(file_content)

    if associativity == 1:

        #direct replacement

        n_blocks = (cachesize_kb*1024)/blocksize_bytes
        cache_tags = [0 for i in range(int(n_blocks))]
        valid_bit = [False for i in range(int(n_blocks))]
        dirty_bit = [False for i in range(int(n_blocks))]

        offset_bits = round(math.log2(blocksize_bytes))

        index_bits = round(math.log2(n_blocks))

        tag_index = offset_bits + index_bits

        tag_bits = 32 - tag_index

        for i in file_content:
            str_data = i.decode().split(" ")
            ldstr = int(str_data[1])
            address = int(str_data[2], 16)
            instr_num = int(str_data[3])

            instr_count += instr_num

            block_address = math.floor(address/blocksize_bytes)
            block_index = int(block_address%n_blocks)

            tag_index = offset_bits + index_bits
            tag = get_tag(address, tag_bits)

            iter_miss_penalty = 0

            if ldstr == 1: #store
                if ((tag == cache_tags[block_index]) & valid_bit[block_index]):
                    store_hits += 1
                    dirty_bit[block_index] = True
                elif ((tag != cache_tags[block_index]) | ~valid_bit[block_index]):
                    store_misses += 1
                    cache_tags[block_index] = tag
                    valid_bit[block_index]= True
                    iter_miss_penalty += miss_penalty          
                    if dirty_bit[block_index]:
                        dirty_evictions +=1
                        iter_miss_penalty += 2 
                    dirty_bit[block_index] = True

                else:
                    print("STORE ERROR: neither hit nor miss")

            elif ldstr == 0: #load
                if ((tag == cache_tags[block_index]) & valid_bit[block_index]):
                    load_hits += 1
                    
                elif ((tag != cache_tags[block_index]) | ~valid_bit[block_index]):
                    load_misses +=1
                    cache_tags[block_index] = tag
                    valid_bit[block_index]= True
                    iter_miss_penalty += miss_penalty
                    if dirty_bit[block_index]:
                        dirty_evictions += 1
                        dirty_bit[block_index] = False
                        iter_miss_penalty += 2
                else:
                    print("LOAD ERROR: neither hit nor miss")

            else:
                print("ERROR: not load or store")

            total_cycles += instr_num + iter_miss_penalty
            miss_penalties += iter_miss_penalty

    else:
        #set associative
        #split into two blocks for my own understanding

        n_blocks = (cachesize_kb*1024)/blocksize_bytes
        n_sets = n_blocks/associativity

        #instantiate cache_tags (list comprehensions were creating shallow copies)
        cache_tags = []
        for i in range(int(n_sets)):
            subset = []
            for i in range(associativity):
                subset.append(0)
            cache_tags.append(subset)

        #instantiate valid_bit_lists
        valid_bit_lists = []
        for i in range(int(n_sets)):
            subset = []
            for i in range(associativity):
                subset.append(False)
            valid_bit_lists.append(subset)

        dirty_bit_lists = []
        for i in range(int(n_sets)):
            subset = []
            for i in range(associativity):
                subset.append(False)
            dirty_bit_lists.append(subset)

        offset_bits = round(math.log2(blocksize_bytes))

        index_bits = round(math.log2(n_sets))

        tag_index = offset_bits + index_bits

        tag_bits = 32 - tag_index

        print(extra_miss_pen, miss_penalty)

        for i in file_content:
            str_data = i.decode().split(" ")
            ldstr = int(str_data[1])
            address = int(str_data[2], 16)
            instr_num = int(str_data[3])

            instr_count += instr_num

            set_address = math.floor(address/blocksize_bytes)
            set_index = int(set_address%n_sets)

            tag = get_tag(address, tag_bits)

            iter_miss_penalty = 0
            cycles = 0
            
            cache_set = cache_tags[set_index]
            valid_bits = valid_bit_lists[set_index]
            dirty_bits = dirty_bit_lists[set_index]

            index = None
            match = False
            valid = False

            for j, stored_tag in enumerate(cache_set):

                if tag == stored_tag:
                    match = True
                    index = j
                    valid = valid_bits[j]
                    break

            if not match:
                index = 0

            #LRU paradigm, move whatever was most recently used to end of the list. So the first index will be the most least recently used
            #must move tags, valid bits, and dirty bits

            if ldstr == 1:
                #store
                
                if (match & valid):
                    store_hits += 1
                    dirty_bits[index] = True

                    valid_bits, dirty_bits, cache_set = LRU(index, valid_bits, dirty_bits, cache_set)

                    valid_bit_lists[set_index] = valid_bits
                    dirty_bit_lists[set_index] = dirty_bits
                    cache_tags[set_index] = cache_set

                elif (~match | ~valid):

                    store_misses += 1

                    cache_set[index] = tag
                    valid_bits[index] = True

                    iter_miss_penalty += miss_penalty          
                    if dirty_bits[index]:
                        dirty_evictions +=1
                        iter_miss_penalty += extra_miss_pen 

                    dirty_bits[index] = True

                    valid_bits, dirty_bits, cache_set = LRU(index, valid_bits, dirty_bits, cache_set)

                    valid_bit_lists[set_index] = valid_bits
                    dirty_bit_lists[set_index] = dirty_bits
                    cache_tags[set_index] = cache_set

                else:
                    print("STORE ERROR: neither hit nor miss")

            elif ldstr == 0: #load
                if (match & valid):
                    load_hits += 1

                    valid_bits, dirty_bits, cache_set = LRU(index, valid_bits, dirty_bits, cache_set)

                    valid_bit_lists[set_index] = valid_bits
                    dirty_bit_lists[set_index] = dirty_bits
                    cache_tags[set_index] = cache_set
                    
                elif (~match | ~valid):

                    load_misses +=1
                    cache_set[index] = tag
                    valid_bits[index]= True
                    iter_miss_penalty += miss_penalty
                    if dirty_bits[index]:
                        dirty_evictions += 1
                        dirty_bits[index] = False
                        iter_miss_penalty += extra_miss_pen

                    valid_bits, dirty_bits, cache_set = LRU(index, valid_bits, dirty_bits, cache_set)

                    valid_bit_lists[set_index] = valid_bits
                    dirty_bit_lists[set_index] = dirty_bits
                    cache_tags[set_index] = cache_set
                    
                else:
                    print("LOAD ERROR: neither hit nor miss")

            else:
                print("ERROR: not load or store")

            total_cycles += instr_num + iter_miss_penalty
            miss_penalties += iter_miss_penalty

    miss_rate = (load_misses + store_misses)/memory_accesses
    read_miss_rate = load_misses/(load_misses + load_hits)
    average_memory_access_time = (miss_penalties)/memory_accesses
    total_CPI = total_cycles/instr_count
    memory_CPI = total_CPI - 1

    #cycle time slow downs
    assoc_penalty = 0
    cache_size_penalty = 0

    if associativity == 2:
        assoc_penalty += .05
    elif associativity == 4:
        assoc_penalty += .075
    elif associativity == 8:
        assoc_penalty += .1

    if cachesize_kb == 32:
        cache_size_penalty += .05
    elif cachesize_kb == 64:
        cache_size_penalty += .1
    elif cachesize_kb == 128:
        cache_size_penalty += .15

    clock_period_adj = clock_period*(1 + assoc_penalty+ cache_size_penalty)
    total_time = clock_period_adj*total_cycles/(10**9)

    print(f"Completed sim with parameters: cachesize_kb = {cachesize_kb}, associativity = {associativity}, blocksize_bytes = {blocksize_bytes}, miss_penalty = {miss_penalty}, clock_period = {clock_period} ")


    return total_cycles, instr_count, memory_accesses, miss_rate, read_miss_rate, memory_CPI, total_CPI, average_memory_access_time, dirty_evictions, load_misses, store_misses, load_hits, store_hits, total_time

total_cycles, instr_count, memory_accesses, miss_rate, read_miss_rate, memory_CPI, \
total_CPI, average_memory_access_time, dirty_evictions, load_misses, store_misses, \
load_hits, store_hits, total_time = simulate('mcf.trace.gz', 64, 8, 32, 42, .5)


print("total cycles:", total_cycles)
print("instruction count:", instr_count)
print("memory accesses: ", memory_accesses)
print("overall miss rate: {:.2f}".format(miss_rate))
print("read miss rate: {:.2f}".format(read_miss_rate))
print("memory CPI:", memory_CPI)
print("total CPI:", total_CPI)
print("Average memory access time in cycles: ", average_memory_access_time)
print("dirty evictions: ", dirty_evictions)
print("load misses: ", load_misses)
print("store misses: ", store_misses)
print("load hits: ", load_hits)
print("store hits: ", store_hits)   
print("total time: ", total_time)