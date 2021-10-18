//------------------------------------------------------------------------------
//
// Copyright 2006 - 2019 Synopsys, INC.
//
// This Synopsys IP and all associated documentation are proprietary to
// Synopsys, Inc. and may only be used pursuant to the terms and conditions of a
// written license agreement with Synopsys, Inc. All other use, reproduction,
// modification, or distribution of the Synopsys IP or the associated
// documentation is strictly prohibited.
//
// Component Name   : DWC_xpcs
// Component Version: 3.41a
// Release Type     : GA
//------------------------------------------------------------------------------

//---------------------------------------------------------------------------//
// $Id: //dwh/ethernet_iip/main/XPCS_SSP/src/common/DWC_xpcs_pseq_e12.v#13 $
// Release version :  3.41a
// Date             :        $Date: 2019/12/02 $
// File Version     :        $Revision: #13 $
//--                                                                        
//--------------------------------------------------------------------------
// MODULE:
// DWC_xpcs_pseq_e12 (DWC_xpcs_pseq_e12.v)
//
//                                                                               //
// DESCRIPTION:                                                                  //
//                This block implements the Power Up Sequence for Synopsys E12 PHY//
//                                                                                //
//-------------------------------------------------------------------------------//

module DWC_xpcs_pseq_e12 (
    clk_csr_i
                          ,rst_clk_csr_n
                          ,actv_rst_clk_csr_pseq
                          ,scc_tx_ack
                          ,scc_rx_ack
                          ,scc_byp_pseq
                          ,scc_pdown
                          ,scc_psave
                          ,power_down
                          ,csr_e12_tx_lpd
                          ,csr_e12_rx_lpd
                          ,csr_e12_tx_reset
                          ,csr_e12_rx_reset
                          ,csr_e12_ref_clk_en
                          ,csr_e12_tx_clk_rdy
                          ,pseq_tx_reset
                          ,pseq_rx_reset
                          ,pseq_tx_lpd
                          ,pseq_rx_lpd
                          ,pseq_pwr_up
                          ,pseq_state
                          ,pseq_ref_clk_en
                          ,pseq_tx_clk_rdy
                          ,pseq_tx_req
                          ,pseq_rx_req
                          );

input      clk_csr_i;        // CSR clock
input      rst_clk_csr_n;    // Reset sync'ed to clk_csr_i

input      actv_rst_clk_csr_pseq;      // Indicates rst_clk_csr_pseq_n active, assert 1 clock cycle early of rst_clk_csr_pseq_n assert and deasserts with it

input [`NUM_OF_LANES-1:0]   scc_tx_ack; // ack for tx control event frm phy
input [`NUM_OF_LANES-1:0]   scc_rx_ack; // ack for tx control event frm phy
input                       scc_pdown;  // power down sync'ed to csr clk
input                       scc_psave;  // power save sync'ed to csr clk
input                       scc_byp_pseq; // Bypass power-up seq control
input                       csr_e12_ref_clk_en; // Ref clock power down control from CSR
input                       power_down; // Power down control from MCI/MDIO -unsychronized
input [`NUM_OF_LANES-1:0]   csr_e12_tx_lpd; // Tx power down control from CSR
input [`NUM_OF_LANES-1:0]   csr_e12_rx_lpd; // Rx power down control from CSR
input [`NUM_OF_LANES-1:0]   csr_e12_tx_reset; // Tx Reset control from CSR
input [`NUM_OF_LANES-1:0]   csr_e12_rx_reset; // Rx Reset control from CSR
input  [`NUM_OF_LANES-1:0]  csr_e12_tx_clk_rdy;  // Tx Clock Ready

output [`NUM_OF_LANES-1:0]  pseq_tx_lpd; // Tx power down control to phy - Puts PHY in P1 power state
output [`NUM_OF_LANES-1:0]  pseq_rx_lpd; // Tx power down control to phy - Puts PHY in P1 power state
output [`NUM_OF_LANES-1:0]  pseq_tx_reset; // Tx Reset to phy - Puts PHY in P2 state
output [`NUM_OF_LANES-1:0]  pseq_rx_reset; // Rx Reset to phy - Puts PHY in P2 state
output                      pseq_pwr_up;       // Signal indicating power good
output [6:0]                pseq_state;  // power-up sequence state
output                      pseq_ref_clk_en; // Ref clock power down cntrol output
output [`NUM_OF_LANES-1:0]  pseq_tx_clk_rdy; // Tx clock ready output

output [`NUM_OF_LANES-1:0]  pseq_tx_req;  // Tx req for tx_lpd 
output [`NUM_OF_LANES-1:0]  pseq_rx_req;  // Rx Req for rx_lpd


// Parameters
parameter WF_ACK_H0    = 0,
          WF_ACK_L0    = 1,
          WF_ACK_H1    = 2,
          WF_ACK_L1    = 3,
          POWER_GOOD   = 4,
          POWER_SAVE   = 5,
          POWER_DOWN   = 6;

reg                      pseq_pwr_up;  // DUT is in POWER GOOD state
reg [6:0]                pseq_state, pseq_next_state; // State machine variables
reg [`NUM_OF_LANES-1:0]  pseq_tx_lpd; // Tx Lane Power Down- Asserted in PSAVE
reg [`NUM_OF_LANES-1:0]  pseq_rx_lpd; // Tx Lane Power Down- Asserted in PSAVE
reg [`NUM_OF_LANES-1:0]  pseq_tx_reset; // Tx Reset- Asserted in PDOWN
reg [`NUM_OF_LANES-1:0]  pseq_rx_reset; // Rx Reset- Asserted in PDOWN
reg [`NUM_OF_LANES-1:0]  pseq_tx_req;  // Tx Req - needed for tx_lpd change
reg [`NUM_OF_LANES-1:0]  pseq_rx_req;  // Rx Req - needed for rx_lpd change
reg [`NUM_OF_LANES-1:0]  pseq_tx_clk_rdy_prg; // Tx Clk Ready (Required for PHY Tx lane alignment)
reg                      lpd_hi;      // High when tx/rx LPD are asserted

wire   pseq_ref_clk_en;




  DWC_xpcs_and
   #(`NUM_OF_LANES) DWC_xpcs_and_pseq_tx_clk_rdy_inst ( .and_out(pseq_tx_clk_rdy), .and_in0(pseq_tx_clk_rdy_prg), .and_in1({(`NUM_OF_LANES){!actv_rst_clk_csr_pseq}}) );


//////////////////////////////////////    
always @(`RST_CSR_MODE) begin
  if (!rst_clk_csr_n) // This reset gets asserted on both standard and vendor soft reset. Done to ensure that this module also gets reset whenver phy is reset.
    pseq_state <= 7'h1;
  else
    pseq_state <= pseq_next_state;
end

always @(*) begin

   pseq_next_state = 7'h0;
// leda C_4C_R_B C_5C_R DFT_022 FM_2_12 W225 W226 W455 VER_2_8_1_5 VER_2_8_5_1 off
// LMD: Mutliple rules like use of snps parallel case etc. are turned off
// LJ: Standard way of FSM encoding throughout this IP. All cases are covered
// spyglass disable_block STARC05-2.8.1.5 STARC05-2.8.5.1
// SMD: Use of snps parallel case and full-case are turned off
// SJ: Standard way of FSM encoding throughout this IP since first release. All cases are covered
   case (`H) // synopsys full_case parallel_case
// leda C_4C_R_B C_5C_R DFT_022 FM_2_12 W226 W455 VER_2_8_1_5 VER_2_8_5_1 on
// spyglass enable_block STARC05-2.8.1.5 STARC05-2.8.5.1
    pseq_state[WF_ACK_H0]    : begin
                                 if (((&scc_rx_ack) && (&scc_tx_ack)) | scc_byp_pseq)
                                   pseq_next_state[WF_ACK_L0] = `H;
                                 else
                                   pseq_next_state[WF_ACK_H0] = `H;
                               end
    pseq_state[WF_ACK_L0]    : begin
                                 if (!((|scc_tx_ack)|(|scc_rx_ack)) | scc_byp_pseq)
                                   pseq_next_state[POWER_GOOD] = `H;
                                 else
                                   pseq_next_state[WF_ACK_L0] = `H; 
                               end    
   pseq_state[POWER_GOOD]    : begin
                                 if (scc_pdown)
                                   pseq_next_state[POWER_DOWN] = `H;
                                 else if (scc_psave) 
                                   pseq_next_state[WF_ACK_H1] = `H;
                                 else
                                   pseq_next_state[POWER_GOOD] = `H;
                               end
   pseq_state[WF_ACK_H1]      : begin  
                                 if ((&scc_rx_ack) && (&scc_tx_ack))    
                                   pseq_next_state[WF_ACK_L1] = `H; 
                                 else 
                                   pseq_next_state [WF_ACK_H1] = `H;
                               end
   pseq_state[WF_ACK_L1]     : begin
                                 if (!(|scc_tx_ack)) begin
                                   if (lpd_hi)
                                     pseq_next_state[POWER_SAVE] = `H;
                                   else
                                     pseq_next_state[POWER_GOOD] = `H;
                                 end else
                                   pseq_next_state[WF_ACK_L1] = `H;
                               end
    pseq_state [POWER_SAVE]  : begin
                                 if (!scc_psave) 
                                   pseq_next_state [WF_ACK_H1] = `H;
                                 else
                                   pseq_next_state [POWER_SAVE] = `H;
                               end
   pseq_state [POWER_DOWN]   : begin
                                 if (!scc_pdown) 
                                   pseq_next_state [WF_ACK_L0] = `H;
                                 else
                                   pseq_next_state [POWER_DOWN] = `H;
                               end
    endcase
// leda W225 on    
end

////////////////////////////////////////////////////////////////////////////////////////////////////
// Powerup Indication
always @(`RST_CSR_MODE) begin
   if (!rst_clk_csr_n)
     pseq_pwr_up <= `L;
   else  
     pseq_pwr_up <= (scc_byp_pseq) ? `H : (pseq_next_state[POWER_GOOD] & !(scc_pdown | scc_psave));
end
///////////////////////////////////////////////////////////////////////////////////////////////////








table
  0   0 0   : 0
  0 1 0 : 1
  1 0    0 : 0
  1 1 1 : 0
  1 0 0            : 1
endtable




// config
//   design
//   lallala
// endconfig


// Power-Save Feature
always @(`RST_CSR_MODE) begin
  if (!rst_clk_csr_n) begin
    pseq_tx_lpd <= {`NUM_OF_LANES{`L}};
    pseq_rx_lpd <= {`NUM_OF_LANES{`L}};
    lpd_hi      <= `L;
  end
  else begin 
    if (pseq_state[POWER_GOOD] & scc_psave) begin 
      pseq_tx_lpd <= {`NUM_OF_LANES{`H}};
      pseq_rx_lpd <= {`NUM_OF_LANES{`H}};
      lpd_hi     <= `H;
    end else if (pseq_state[POWER_SAVE] & !scc_psave) begin
      pseq_tx_lpd  <= {`NUM_OF_LANES{`L}};
      pseq_rx_lpd  <= {`NUM_OF_LANES{`L}};
      lpd_hi       <= `L;
    end else if (pseq_state[POWER_GOOD] & !scc_psave) begin
      pseq_tx_lpd  <= csr_e12_tx_lpd;
      pseq_rx_lpd  <= csr_e12_rx_lpd;
    end
  end 
end

// Rx-Ack Handshake to force 'LPD' 
 always @(`RST_CSR_MODE) begin
  if (!rst_clk_csr_n) begin
    pseq_tx_req <= {`NUM_OF_LANES{`L}};
    pseq_rx_req <= {`NUM_OF_LANES{`L}};
  end
  else begin 
    if (pseq_state[WF_ACK_H1]) begin 
      pseq_tx_req <= {`NUM_OF_LANES{`H}};
      pseq_rx_req <= {`NUM_OF_LANES{`H}};
    end else if (pseq_state[WF_ACK_L1]) begin
      pseq_tx_req  <= {`NUM_OF_LANES{`L}};
      pseq_rx_req  <= {`NUM_OF_LANES{`L}};
    end
  end 
end

////////////////////////////////////////////////////////
// Tx-Rx Reset Implementation, similar to UP5
always @(`RST_CSR_MODE) begin
  if (!rst_clk_csr_n) begin
    pseq_tx_reset <= {`NUM_OF_LANES{`L}};
    pseq_rx_reset <= {`NUM_OF_LANES{`L}};
  end
  else begin 
    if (pseq_next_state[POWER_DOWN]) begin 
      pseq_tx_reset <= {`NUM_OF_LANES{`H}};
      pseq_rx_reset <= {`NUM_OF_LANES{`H}};
    end else if (pseq_next_state[WF_ACK_L0]) begin
      pseq_tx_reset  <= {`NUM_OF_LANES{`L}};
      pseq_rx_reset  <= {`NUM_OF_LANES{`L}};
    end else if (pseq_state[POWER_GOOD] & !scc_pdown) begin
      pseq_tx_reset  <= csr_e12_tx_reset; 
      pseq_rx_reset  <= csr_e12_rx_reset;
    end
  end 
end


///////////////////////////////////////////////
assign pseq_ref_clk_en = (power_down & pseq_state [POWER_DOWN]) ? csr_e12_ref_clk_en : `H;  
///////////////////////////////////////////////

// Clk Rdy -To be asserted on Tx clks are UP
  always @(`RST_CSR_MODE) begin
    if (!rst_clk_csr_n) 
      pseq_tx_clk_rdy_prg <= {`NUM_OF_LANES{`L}};
    else if (pseq_state[POWER_GOOD])
      pseq_tx_clk_rdy_prg <= csr_e12_tx_clk_rdy;
    else
      pseq_tx_clk_rdy_prg <= {`NUM_OF_LANES{`L}};
  end
////////////////////////////////////////////


//// CR/JTAG port select
// always @(`RST_CSR_MODE) begin
//   if (!rst_clk_csr_n) 
//     pseq_cr_para_sel <= 1'b1; // Select CR port
//   else if (pseq_state[POWER_DOWN])
//     pseq_cr_para_sel <= csr_e12_cr_para_sel;
// end



endmodule




 
