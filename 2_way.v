module 2_LRU(

    input [1:0] access_bits;
    input access_index;
)

always @(access_index) begin
    casex(access_index)
        1b'0: access_bits = 2'b10;
        1b'1: access_bits = 2'b01;
    endcase


end

endmodule

//results:
//2-input equivalents: 8
//gate delays: 3
