`define associativity = 4

module 4_8_LRU(

    input [`associativity-1:0] set_bits [`associativity-1:0]
    input [`associativity-1:0] active_reg_index

    output [`associativity] output_set [`associativity-1:0]
)

always @(set_bits[active_reg_index]) begin
    for(i = 0; i < `associativity; i = i+1)
        if (set_bits[active_reg_index] == set_bits[i]) begin
            output_set[active_reg_index] <= `associativty -1;
        end
        if (set_bits[active_reg_index] > set_bits[i]) begin
            output_set[active_reg_index] <= set_bits[active_reg_index] - 1;
        end
end

endmodule

//results:
//
//-----4-way-----
//2 input equivalents: 156
//gate delays: 13
//
//----8-way------
//2 input equivalents: 416
//gate delays: 16