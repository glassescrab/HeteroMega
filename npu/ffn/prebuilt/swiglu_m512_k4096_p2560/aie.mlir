module {
  aie.device(npu2) {
    %logical_core = aie.logical_tile<CoreTile>(0, 2)
    %logical_core_0 = aie.logical_tile<CoreTile>(0, 3)
    %logical_core_1 = aie.logical_tile<CoreTile>(0, 4)
    %logical_core_2 = aie.logical_tile<CoreTile>(0, 5)
    %logical_core_3 = aie.logical_tile<CoreTile>(1, 2)
    %logical_core_4 = aie.logical_tile<CoreTile>(1, 3)
    %logical_core_5 = aie.logical_tile<CoreTile>(1, 4)
    %logical_core_6 = aie.logical_tile<CoreTile>(1, 5)
    %logical_core_7 = aie.logical_tile<CoreTile>(2, 2)
    %logical_core_8 = aie.logical_tile<CoreTile>(2, 3)
    %logical_core_9 = aie.logical_tile<CoreTile>(2, 4)
    %logical_core_10 = aie.logical_tile<CoreTile>(2, 5)
    %logical_core_11 = aie.logical_tile<CoreTile>(3, 2)
    %logical_core_12 = aie.logical_tile<CoreTile>(3, 3)
    %logical_core_13 = aie.logical_tile<CoreTile>(3, 4)
    %logical_core_14 = aie.logical_tile<CoreTile>(3, 5)
    %logical_core_15 = aie.logical_tile<CoreTile>(4, 2)
    %logical_core_16 = aie.logical_tile<CoreTile>(4, 3)
    %logical_core_17 = aie.logical_tile<CoreTile>(4, 4)
    %logical_core_18 = aie.logical_tile<CoreTile>(4, 5)
    %logical_core_19 = aie.logical_tile<CoreTile>(5, 2)
    %logical_core_20 = aie.logical_tile<CoreTile>(5, 3)
    %logical_core_21 = aie.logical_tile<CoreTile>(5, 4)
    %logical_core_22 = aie.logical_tile<CoreTile>(5, 5)
    %logical_core_23 = aie.logical_tile<CoreTile>(6, 2)
    %logical_core_24 = aie.logical_tile<CoreTile>(6, 3)
    %logical_core_25 = aie.logical_tile<CoreTile>(6, 4)
    %logical_core_26 = aie.logical_tile<CoreTile>(6, 5)
    %logical_core_27 = aie.logical_tile<CoreTile>(7, 2)
    %logical_core_28 = aie.logical_tile<CoreTile>(7, 3)
    %logical_core_29 = aie.logical_tile<CoreTile>(7, 4)
    %logical_core_30 = aie.logical_tile<CoreTile>(7, 5)
    %logical_mem = aie.logical_tile<MemTile>(0, 1)
    %logical_mem_31 = aie.logical_tile<MemTile>(1, 1)
    %logical_mem_32 = aie.logical_tile<MemTile>(2, 1)
    %logical_mem_33 = aie.logical_tile<MemTile>(3, 1)
    %logical_shim_noc = aie.logical_tile<ShimNOCTile>(0, 0)
    %logical_shim_noc_34 = aie.logical_tile<ShimNOCTile>(1, 0)
    %logical_shim_noc_35 = aie.logical_tile<ShimNOCTile>(2, 0)
    %logical_shim_noc_36 = aie.logical_tile<ShimNOCTile>(3, 0)
    %logical_mem_37 = aie.logical_tile<MemTile>(0, 1)
    %logical_mem_38 = aie.logical_tile<MemTile>(1, 1)
    %logical_mem_39 = aie.logical_tile<MemTile>(2, 1)
    %logical_mem_40 = aie.logical_tile<MemTile>(3, 1)
    %logical_mem_41 = aie.logical_tile<MemTile>(4, 1)
    %logical_mem_42 = aie.logical_tile<MemTile>(5, 1)
    %logical_mem_43 = aie.logical_tile<MemTile>(6, 1)
    %logical_mem_44 = aie.logical_tile<MemTile>(7, 1)
    %logical_shim_noc_45 = aie.logical_tile<ShimNOCTile>(0, 0)
    %logical_shim_noc_46 = aie.logical_tile<ShimNOCTile>(1, 0)
    %logical_shim_noc_47 = aie.logical_tile<ShimNOCTile>(2, 0)
    %logical_shim_noc_48 = aie.logical_tile<ShimNOCTile>(3, 0)
    %logical_shim_noc_49 = aie.logical_tile<ShimNOCTile>(4, 0)
    %logical_shim_noc_50 = aie.logical_tile<ShimNOCTile>(5, 0)
    %logical_shim_noc_51 = aie.logical_tile<ShimNOCTile>(6, 0)
    %logical_shim_noc_52 = aie.logical_tile<ShimNOCTile>(7, 0)
    %logical_mem_53 = aie.logical_tile<MemTile>(1, 1)
    %logical_shim_noc_54 = aie.logical_tile<ShimNOCTile>(1, 0)
    %logical_mem_55 = aie.logical_tile<MemTile>(3, 1)
    %logical_shim_noc_56 = aie.logical_tile<ShimNOCTile>(3, 0)
    %logical_mem_57 = aie.logical_tile<MemTile>(5, 1)
    %logical_shim_noc_58 = aie.logical_tile<ShimNOCTile>(5, 0)
    %logical_mem_59 = aie.logical_tile<MemTile>(7, 1)
    %logical_shim_noc_60 = aie.logical_tile<ShimNOCTile>(7, 0)
    aie.objectfifo @swiglu_a_broadcast_0(%logical_mem dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core, %logical_core_3, %logical_core_7, %logical_core_11, %logical_core_15, %logical_core_19, %logical_core_23, %logical_core_27}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_a_host_0(%logical_shim_noc, {%logical_mem}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo.link [@swiglu_a_host_0] -> [@swiglu_a_broadcast_0]([] [0])
    aie.objectfifo @swiglu_a_broadcast_1(%logical_mem_31 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_0, %logical_core_4, %logical_core_8, %logical_core_12, %logical_core_16, %logical_core_20, %logical_core_24, %logical_core_28}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_a_host_1(%logical_shim_noc_34, {%logical_mem_31}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo.link [@swiglu_a_host_1] -> [@swiglu_a_broadcast_1]([] [0])
    aie.objectfifo @swiglu_a_broadcast_2(%logical_mem_32 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_1, %logical_core_5, %logical_core_9, %logical_core_13, %logical_core_17, %logical_core_21, %logical_core_25, %logical_core_29}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_a_host_2(%logical_shim_noc_35, {%logical_mem_32}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo.link [@swiglu_a_host_2] -> [@swiglu_a_broadcast_2]([] [0])
    aie.objectfifo @swiglu_a_broadcast_3(%logical_mem_33 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_2, %logical_core_6, %logical_core_10, %logical_core_14, %logical_core_18, %logical_core_22, %logical_core_26, %logical_core_30}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_a_host_3(%logical_shim_noc_36, {%logical_mem_33}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo.link [@swiglu_a_host_3] -> [@swiglu_a_broadcast_3]([] [0])
    aie.objectfifo @swiglu_gate_0_0(%logical_core, {%logical_core_3}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_0_1(%logical_core_0, {%logical_core_4}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_0_2(%logical_core_1, {%logical_core_5}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_0_3(%logical_core_2, {%logical_core_6}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_1_0(%logical_core_7, {%logical_core_11}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_1_1(%logical_core_8, {%logical_core_12}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_1_2(%logical_core_9, {%logical_core_13}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_1_3(%logical_core_10, {%logical_core_14}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_2_0(%logical_core_15, {%logical_core_19}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_2_1(%logical_core_16, {%logical_core_20}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_2_2(%logical_core_17, {%logical_core_21}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_2_3(%logical_core_18, {%logical_core_22}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_3_0(%logical_core_23, {%logical_core_27}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_3_1(%logical_core_24, {%logical_core_28}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_3_2(%logical_core_25, {%logical_core_29}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_gate_3_3(%logical_core_26, {%logical_core_30}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_w_broadcast_0(%logical_mem_37, {%logical_core, %logical_core_0, %logical_core_1, %logical_core_2}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_0(%logical_shim_noc_45, {%logical_mem_37}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_0] -> [@swiglu_w_broadcast_0]([] [0])
    aie.objectfifo @swiglu_w_broadcast_1(%logical_mem_38, {%logical_core_3, %logical_core_4, %logical_core_5, %logical_core_6}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_1(%logical_shim_noc_46, {%logical_mem_38}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_1] -> [@swiglu_w_broadcast_1]([] [0])
    aie.objectfifo @swiglu_w_broadcast_2(%logical_mem_39, {%logical_core_7, %logical_core_8, %logical_core_9, %logical_core_10}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_2(%logical_shim_noc_47, {%logical_mem_39}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_2] -> [@swiglu_w_broadcast_2]([] [0])
    aie.objectfifo @swiglu_w_broadcast_3(%logical_mem_40, {%logical_core_11, %logical_core_12, %logical_core_13, %logical_core_14}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_3(%logical_shim_noc_48, {%logical_mem_40}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_3] -> [@swiglu_w_broadcast_3]([] [0])
    aie.objectfifo @swiglu_w_broadcast_4(%logical_mem_41, {%logical_core_15, %logical_core_16, %logical_core_17, %logical_core_18}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_4(%logical_shim_noc_49, {%logical_mem_41}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_4] -> [@swiglu_w_broadcast_4]([] [0])
    aie.objectfifo @swiglu_w_broadcast_5(%logical_mem_42, {%logical_core_19, %logical_core_20, %logical_core_21, %logical_core_22}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_5(%logical_shim_noc_50, {%logical_mem_42}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_5] -> [@swiglu_w_broadcast_5]([] [0])
    aie.objectfifo @swiglu_w_broadcast_6(%logical_mem_43, {%logical_core_23, %logical_core_24, %logical_core_25, %logical_core_26}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_6(%logical_shim_noc_51, {%logical_mem_43}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_6] -> [@swiglu_w_broadcast_6]([] [0])
    aie.objectfifo @swiglu_w_broadcast_7(%logical_mem_44, {%logical_core_27, %logical_core_28, %logical_core_29, %logical_core_30}, 2 : i32) : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo @swiglu_w_host_7(%logical_shim_noc_52, {%logical_mem_44}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<2144xui8>>  
    aie.objectfifo.link [@swiglu_w_host_7] -> [@swiglu_w_broadcast_7]([] [0])
    aie.objectfifo @swiglu_z_host_1(%logical_mem_53, {%logical_shim_noc_54}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_z_worker_1_0(%logical_core_3, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_1_1(%logical_core_4, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_1_2(%logical_core_5, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_1_3(%logical_core_6, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo.link [@swiglu_z_worker_1_0, @swiglu_z_worker_1_1, @swiglu_z_worker_1_2, @swiglu_z_worker_1_3] -> [@swiglu_z_host_1]([0, 1024, 2048, 3072] [])
    aie.objectfifo @swiglu_z_host_3(%logical_mem_55, {%logical_shim_noc_56}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_z_worker_3_0(%logical_core_11, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_3_1(%logical_core_12, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_3_2(%logical_core_13, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_3_3(%logical_core_14, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo.link [@swiglu_z_worker_3_0, @swiglu_z_worker_3_1, @swiglu_z_worker_3_2, @swiglu_z_worker_3_3] -> [@swiglu_z_host_3]([0, 1024, 2048, 3072] [])
    aie.objectfifo @swiglu_z_host_5(%logical_mem_57, {%logical_shim_noc_58}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_z_worker_5_0(%logical_core_19, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_5_1(%logical_core_20, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_5_2(%logical_core_21, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_5_3(%logical_core_22, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo.link [@swiglu_z_worker_5_0, @swiglu_z_worker_5_1, @swiglu_z_worker_5_2, @swiglu_z_worker_5_3] -> [@swiglu_z_host_5]([0, 1024, 2048, 3072] [])
    aie.objectfifo @swiglu_z_host_7(%logical_mem_59, {%logical_shim_noc_60}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>  
    aie.objectfifo @swiglu_z_worker_7_0(%logical_core_27, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_7_1(%logical_core_28, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_7_2(%logical_core_29, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo @swiglu_z_worker_7_3(%logical_core_30, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>  
    aie.objectfifo.link [@swiglu_z_worker_7_0, @swiglu_z_worker_7_1, @swiglu_z_worker_7_2, @swiglu_z_worker_7_3] -> [@swiglu_z_host_7]([0, 1024, 2048, 3072] [])
    %swiglu_acc_0_0 = aie.buffer(%logical_core) {sym_name = "swiglu_acc_0_0"} : memref<1024xf32> 
    %swiglu_dequant_0_0 = aie.buffer(%logical_core) {sym_name = "swiglu_dequant_0_0"} : memref<4096xbf16> 
    func.func private @w4a16_prefill_reuse_init(memref<1024xf32>) attributes {link_with = "w4a16_prefill_reuse_bfp16_9419624b5979e53c6e1378890dc63daba9d8e6980e8ca78750946f240e6dfee1_098924e50ecac8ea14ae20a6e2553417ef21b23bc0dd4bc0c933d5192e14e3d1_r2.o"}
    func.func private @w4a16_prefill_reuse_accumulate(memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) attributes {link_with = "w4a16_prefill_reuse_bfp16_9419624b5979e53c6e1378890dc63daba9d8e6980e8ca78750946f240e6dfee1_098924e50ecac8ea14ae20a6e2553417ef21b23bc0dd4bc0c933d5192e14e3d1_r2.o"}
    func.func private @w4a16_prefill_reuse_finish(memref<1024xf32>, memref<1024xbf16>) attributes {link_with = "w4a16_prefill_reuse_bfp16_9419624b5979e53c6e1378890dc63daba9d8e6980e8ca78750946f240e6dfee1_098924e50ecac8ea14ae20a6e2553417ef21b23bc0dd4bc0c933d5192e14e3d1_r2.o"}
    %swiglu_acc_0_1 = aie.buffer(%logical_core_0) {sym_name = "swiglu_acc_0_1"} : memref<1024xf32> 
    %swiglu_dequant_0_1 = aie.buffer(%logical_core_0) {sym_name = "swiglu_dequant_0_1"} : memref<4096xbf16> 
    %swiglu_acc_0_2 = aie.buffer(%logical_core_1) {sym_name = "swiglu_acc_0_2"} : memref<1024xf32> 
    %swiglu_dequant_0_2 = aie.buffer(%logical_core_1) {sym_name = "swiglu_dequant_0_2"} : memref<4096xbf16> 
    %swiglu_acc_0_3 = aie.buffer(%logical_core_2) {sym_name = "swiglu_acc_0_3"} : memref<1024xf32> 
    %swiglu_dequant_0_3 = aie.buffer(%logical_core_2) {sym_name = "swiglu_dequant_0_3"} : memref<4096xbf16> 
    %swiglu_acc_1_0 = aie.buffer(%logical_core_3) {sym_name = "swiglu_acc_1_0"} : memref<1024xf32> 
    %swiglu_dequant_1_0 = aie.buffer(%logical_core_3) {sym_name = "swiglu_dequant_1_0"} : memref<4096xbf16> 
    %swiglu_up_bf16_1_0 = aie.buffer(%logical_core_3) {sym_name = "swiglu_up_bf16_1_0"} : memref<1024xbf16> 
    func.func private @silu_mul_bf16(memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) attributes {link_with = "silu_mul_1863c3ab0cb4be00c0ced57223d172da2706969d1329d7785e9a78c4dea167fc_t1024.o"}
    %swiglu_acc_1_1 = aie.buffer(%logical_core_4) {sym_name = "swiglu_acc_1_1"} : memref<1024xf32> 
    %swiglu_dequant_1_1 = aie.buffer(%logical_core_4) {sym_name = "swiglu_dequant_1_1"} : memref<4096xbf16> 
    %swiglu_up_bf16_1_1 = aie.buffer(%logical_core_4) {sym_name = "swiglu_up_bf16_1_1"} : memref<1024xbf16> 
    %swiglu_acc_1_2 = aie.buffer(%logical_core_5) {sym_name = "swiglu_acc_1_2"} : memref<1024xf32> 
    %swiglu_dequant_1_2 = aie.buffer(%logical_core_5) {sym_name = "swiglu_dequant_1_2"} : memref<4096xbf16> 
    %swiglu_up_bf16_1_2 = aie.buffer(%logical_core_5) {sym_name = "swiglu_up_bf16_1_2"} : memref<1024xbf16> 
    %swiglu_acc_1_3 = aie.buffer(%logical_core_6) {sym_name = "swiglu_acc_1_3"} : memref<1024xf32> 
    %swiglu_dequant_1_3 = aie.buffer(%logical_core_6) {sym_name = "swiglu_dequant_1_3"} : memref<4096xbf16> 
    %swiglu_up_bf16_1_3 = aie.buffer(%logical_core_6) {sym_name = "swiglu_up_bf16_1_3"} : memref<1024xbf16> 
    %swiglu_acc_2_0 = aie.buffer(%logical_core_7) {sym_name = "swiglu_acc_2_0"} : memref<1024xf32> 
    %swiglu_dequant_2_0 = aie.buffer(%logical_core_7) {sym_name = "swiglu_dequant_2_0"} : memref<4096xbf16> 
    %swiglu_acc_2_1 = aie.buffer(%logical_core_8) {sym_name = "swiglu_acc_2_1"} : memref<1024xf32> 
    %swiglu_dequant_2_1 = aie.buffer(%logical_core_8) {sym_name = "swiglu_dequant_2_1"} : memref<4096xbf16> 
    %swiglu_acc_2_2 = aie.buffer(%logical_core_9) {sym_name = "swiglu_acc_2_2"} : memref<1024xf32> 
    %swiglu_dequant_2_2 = aie.buffer(%logical_core_9) {sym_name = "swiglu_dequant_2_2"} : memref<4096xbf16> 
    %swiglu_acc_2_3 = aie.buffer(%logical_core_10) {sym_name = "swiglu_acc_2_3"} : memref<1024xf32> 
    %swiglu_dequant_2_3 = aie.buffer(%logical_core_10) {sym_name = "swiglu_dequant_2_3"} : memref<4096xbf16> 
    %swiglu_acc_3_0 = aie.buffer(%logical_core_11) {sym_name = "swiglu_acc_3_0"} : memref<1024xf32> 
    %swiglu_dequant_3_0 = aie.buffer(%logical_core_11) {sym_name = "swiglu_dequant_3_0"} : memref<4096xbf16> 
    %swiglu_up_bf16_3_0 = aie.buffer(%logical_core_11) {sym_name = "swiglu_up_bf16_3_0"} : memref<1024xbf16> 
    %swiglu_acc_3_1 = aie.buffer(%logical_core_12) {sym_name = "swiglu_acc_3_1"} : memref<1024xf32> 
    %swiglu_dequant_3_1 = aie.buffer(%logical_core_12) {sym_name = "swiglu_dequant_3_1"} : memref<4096xbf16> 
    %swiglu_up_bf16_3_1 = aie.buffer(%logical_core_12) {sym_name = "swiglu_up_bf16_3_1"} : memref<1024xbf16> 
    %swiglu_acc_3_2 = aie.buffer(%logical_core_13) {sym_name = "swiglu_acc_3_2"} : memref<1024xf32> 
    %swiglu_dequant_3_2 = aie.buffer(%logical_core_13) {sym_name = "swiglu_dequant_3_2"} : memref<4096xbf16> 
    %swiglu_up_bf16_3_2 = aie.buffer(%logical_core_13) {sym_name = "swiglu_up_bf16_3_2"} : memref<1024xbf16> 
    %swiglu_acc_3_3 = aie.buffer(%logical_core_14) {sym_name = "swiglu_acc_3_3"} : memref<1024xf32> 
    %swiglu_dequant_3_3 = aie.buffer(%logical_core_14) {sym_name = "swiglu_dequant_3_3"} : memref<4096xbf16> 
    %swiglu_up_bf16_3_3 = aie.buffer(%logical_core_14) {sym_name = "swiglu_up_bf16_3_3"} : memref<1024xbf16> 
    %swiglu_acc_4_0 = aie.buffer(%logical_core_15) {sym_name = "swiglu_acc_4_0"} : memref<1024xf32> 
    %swiglu_dequant_4_0 = aie.buffer(%logical_core_15) {sym_name = "swiglu_dequant_4_0"} : memref<4096xbf16> 
    %swiglu_acc_4_1 = aie.buffer(%logical_core_16) {sym_name = "swiglu_acc_4_1"} : memref<1024xf32> 
    %swiglu_dequant_4_1 = aie.buffer(%logical_core_16) {sym_name = "swiglu_dequant_4_1"} : memref<4096xbf16> 
    %swiglu_acc_4_2 = aie.buffer(%logical_core_17) {sym_name = "swiglu_acc_4_2"} : memref<1024xf32> 
    %swiglu_dequant_4_2 = aie.buffer(%logical_core_17) {sym_name = "swiglu_dequant_4_2"} : memref<4096xbf16> 
    %swiglu_acc_4_3 = aie.buffer(%logical_core_18) {sym_name = "swiglu_acc_4_3"} : memref<1024xf32> 
    %swiglu_dequant_4_3 = aie.buffer(%logical_core_18) {sym_name = "swiglu_dequant_4_3"} : memref<4096xbf16> 
    %swiglu_acc_5_0 = aie.buffer(%logical_core_19) {sym_name = "swiglu_acc_5_0"} : memref<1024xf32> 
    %swiglu_dequant_5_0 = aie.buffer(%logical_core_19) {sym_name = "swiglu_dequant_5_0"} : memref<4096xbf16> 
    %swiglu_up_bf16_5_0 = aie.buffer(%logical_core_19) {sym_name = "swiglu_up_bf16_5_0"} : memref<1024xbf16> 
    %swiglu_acc_5_1 = aie.buffer(%logical_core_20) {sym_name = "swiglu_acc_5_1"} : memref<1024xf32> 
    %swiglu_dequant_5_1 = aie.buffer(%logical_core_20) {sym_name = "swiglu_dequant_5_1"} : memref<4096xbf16> 
    %swiglu_up_bf16_5_1 = aie.buffer(%logical_core_20) {sym_name = "swiglu_up_bf16_5_1"} : memref<1024xbf16> 
    %swiglu_acc_5_2 = aie.buffer(%logical_core_21) {sym_name = "swiglu_acc_5_2"} : memref<1024xf32> 
    %swiglu_dequant_5_2 = aie.buffer(%logical_core_21) {sym_name = "swiglu_dequant_5_2"} : memref<4096xbf16> 
    %swiglu_up_bf16_5_2 = aie.buffer(%logical_core_21) {sym_name = "swiglu_up_bf16_5_2"} : memref<1024xbf16> 
    %swiglu_acc_5_3 = aie.buffer(%logical_core_22) {sym_name = "swiglu_acc_5_3"} : memref<1024xf32> 
    %swiglu_dequant_5_3 = aie.buffer(%logical_core_22) {sym_name = "swiglu_dequant_5_3"} : memref<4096xbf16> 
    %swiglu_up_bf16_5_3 = aie.buffer(%logical_core_22) {sym_name = "swiglu_up_bf16_5_3"} : memref<1024xbf16> 
    %swiglu_acc_6_0 = aie.buffer(%logical_core_23) {sym_name = "swiglu_acc_6_0"} : memref<1024xf32> 
    %swiglu_dequant_6_0 = aie.buffer(%logical_core_23) {sym_name = "swiglu_dequant_6_0"} : memref<4096xbf16> 
    %swiglu_acc_6_1 = aie.buffer(%logical_core_24) {sym_name = "swiglu_acc_6_1"} : memref<1024xf32> 
    %swiglu_dequant_6_1 = aie.buffer(%logical_core_24) {sym_name = "swiglu_dequant_6_1"} : memref<4096xbf16> 
    %swiglu_acc_6_2 = aie.buffer(%logical_core_25) {sym_name = "swiglu_acc_6_2"} : memref<1024xf32> 
    %swiglu_dequant_6_2 = aie.buffer(%logical_core_25) {sym_name = "swiglu_dequant_6_2"} : memref<4096xbf16> 
    %swiglu_acc_6_3 = aie.buffer(%logical_core_26) {sym_name = "swiglu_acc_6_3"} : memref<1024xf32> 
    %swiglu_dequant_6_3 = aie.buffer(%logical_core_26) {sym_name = "swiglu_dequant_6_3"} : memref<4096xbf16> 
    %swiglu_acc_7_0 = aie.buffer(%logical_core_27) {sym_name = "swiglu_acc_7_0"} : memref<1024xf32> 
    %swiglu_dequant_7_0 = aie.buffer(%logical_core_27) {sym_name = "swiglu_dequant_7_0"} : memref<4096xbf16> 
    %swiglu_up_bf16_7_0 = aie.buffer(%logical_core_27) {sym_name = "swiglu_up_bf16_7_0"} : memref<1024xbf16> 
    %swiglu_acc_7_1 = aie.buffer(%logical_core_28) {sym_name = "swiglu_acc_7_1"} : memref<1024xf32> 
    %swiglu_dequant_7_1 = aie.buffer(%logical_core_28) {sym_name = "swiglu_dequant_7_1"} : memref<4096xbf16> 
    %swiglu_up_bf16_7_1 = aie.buffer(%logical_core_28) {sym_name = "swiglu_up_bf16_7_1"} : memref<1024xbf16> 
    %swiglu_acc_7_2 = aie.buffer(%logical_core_29) {sym_name = "swiglu_acc_7_2"} : memref<1024xf32> 
    %swiglu_dequant_7_2 = aie.buffer(%logical_core_29) {sym_name = "swiglu_dequant_7_2"} : memref<4096xbf16> 
    %swiglu_up_bf16_7_2 = aie.buffer(%logical_core_29) {sym_name = "swiglu_up_bf16_7_2"} : memref<1024xbf16> 
    %swiglu_acc_7_3 = aie.buffer(%logical_core_30) {sym_name = "swiglu_acc_7_3"} : memref<1024xf32> 
    %swiglu_dequant_7_3 = aie.buffer(%logical_core_30) {sym_name = "swiglu_dequant_7_3"} : memref<4096xbf16> 
    %swiglu_up_bf16_7_3 = aie.buffer(%logical_core_30) {sym_name = "swiglu_up_bf16_7_3"} : memref<1024xbf16> 
    %core_0_2 = aie.core(%logical_core) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_0_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_0_0, %swiglu_dequant_0_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_0_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_0_3 = aie.core(%logical_core_0) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_0_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_0_1, %swiglu_dequant_0_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_0_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_0_4 = aie.core(%logical_core_1) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_0_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_0_2, %swiglu_dequant_0_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_0_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_0_5 = aie.core(%logical_core_2) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_0_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_0_3, %swiglu_dequant_0_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_0_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_1_2 = aie.core(%logical_core_3) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_1_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_1_0, %swiglu_dequant_1_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_1(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_1_0, %swiglu_up_bf16_1_0) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_0_0(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_1_0, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_0(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_1_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_1_3 = aie.core(%logical_core_4) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_1_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_1_1, %swiglu_dequant_1_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_1(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_1_1, %swiglu_up_bf16_1_1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_0_1(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_1_1, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_1(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_1_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_1_4 = aie.core(%logical_core_5) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_1_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_1_2, %swiglu_dequant_1_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_1(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_1_2, %swiglu_up_bf16_1_2) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_0_2(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_1_2, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_2(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_1_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_1_5 = aie.core(%logical_core_6) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_1_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_1_3, %swiglu_dequant_1_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_1(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_1_3, %swiglu_up_bf16_1_3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_0_3(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_1_3, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_0_3(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_1_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_2_2 = aie.core(%logical_core_7) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_2_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_2_0, %swiglu_dequant_2_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_2_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_2_3 = aie.core(%logical_core_8) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_2_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_2_1, %swiglu_dequant_2_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_2_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_2_4 = aie.core(%logical_core_9) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_2_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_2_2, %swiglu_dequant_2_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_2_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_2_5 = aie.core(%logical_core_10) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_2_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_2_3, %swiglu_dequant_2_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_2_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_3_2 = aie.core(%logical_core_11) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_3_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_3_0, %swiglu_dequant_3_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_3(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_3_0, %swiglu_up_bf16_3_0) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_1_0(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_3_0, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_0(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_3_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_3_3 = aie.core(%logical_core_12) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_3_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_3_1, %swiglu_dequant_3_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_3(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_3_1, %swiglu_up_bf16_3_1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_1_1(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_3_1, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_1(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_3_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_3_4 = aie.core(%logical_core_13) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_3_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_3_2, %swiglu_dequant_3_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_3(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_3_2, %swiglu_up_bf16_3_2) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_1_2(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_3_2, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_2(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_3_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_3_5 = aie.core(%logical_core_14) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_3_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_3_3, %swiglu_dequant_3_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_3(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_3_3, %swiglu_up_bf16_3_3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_1_3(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_3_3, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_1_3(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_3_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_4_2 = aie.core(%logical_core_15) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_4_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_4_0, %swiglu_dequant_4_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_4_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_4_3 = aie.core(%logical_core_16) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_4_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_4_1, %swiglu_dequant_4_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_4_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_4_4 = aie.core(%logical_core_17) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_4_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_4_2, %swiglu_dequant_4_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_4_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_4_5 = aie.core(%logical_core_18) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_4_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_4_3, %swiglu_dequant_4_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_4_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_5_2 = aie.core(%logical_core_19) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_5_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_5_0, %swiglu_dequant_5_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_5(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_5_0, %swiglu_up_bf16_5_0) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_2_0(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_5_0, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_0(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_5_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_5_3 = aie.core(%logical_core_20) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_5_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_5_1, %swiglu_dequant_5_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_5(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_5_1, %swiglu_up_bf16_5_1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_2_1(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_5_1, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_1(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_5_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_5_4 = aie.core(%logical_core_21) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_5_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_5_2, %swiglu_dequant_5_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_5(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_5_2, %swiglu_up_bf16_5_2) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_2_2(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_5_2, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_2(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_5_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_5_5 = aie.core(%logical_core_22) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_5_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_5_3, %swiglu_dequant_5_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_5(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_5_3, %swiglu_up_bf16_5_3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_2_3(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_5_3, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_2_3(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_5_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_6_2 = aie.core(%logical_core_23) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_6_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_6_0, %swiglu_dequant_6_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_6_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_6_3 = aie.core(%logical_core_24) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_6_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_6_1, %swiglu_dequant_6_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_6_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_6_4 = aie.core(%logical_core_25) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_6_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_6_2, %swiglu_dequant_6_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_6_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_6_5 = aie.core(%logical_core_26) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_6_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %2 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %4 = aie.objectfifo.acquire @swiglu_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%3, %5, %swiglu_acc_6_3, %swiglu_dequant_6_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @swiglu_gate_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_6_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_7_2 = aie.core(%logical_core_27) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_7_0) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_7_0, %swiglu_dequant_7_0) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_7(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_7_0, %swiglu_up_bf16_7_0) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_3_0(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_7_0, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_0(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_7_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_7_3 = aie.core(%logical_core_28) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_7_1) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_7_1, %swiglu_dequant_7_1) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_7(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_7_1, %swiglu_up_bf16_7_1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_3_1(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_7_1, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_1(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_7_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_7_4 = aie.core(%logical_core_29) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_7_2) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_7_2, %swiglu_dequant_7_2) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_7(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_7_2, %swiglu_up_bf16_7_2) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_3_2(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_7_2, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_2(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_7_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    %core_7_5 = aie.core(%logical_core_30) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_61 = arith.constant 0 : index
        %c80 = arith.constant 80 : index
        %c1_62 = arith.constant 1 : index
        scf.for %arg1 = %c0_61 to %c80 step %c1_62 {
          func.call @w4a16_prefill_reuse_init(%swiglu_acc_7_3) : (memref<1024xf32>) -> ()
          %c0_63 = arith.constant 0 : index
          %c32 = arith.constant 32 : index
          %c1_64 = arith.constant 1 : index
          scf.for %arg2 = %c0_63 to %c32 step %c1_64 {
            %4 = aie.objectfifo.acquire @swiglu_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %6 = aie.objectfifo.acquire @swiglu_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<2144xui8>>
            %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<2144xui8>> -> memref<2144xui8>
            func.call @w4a16_prefill_reuse_accumulate(%5, %7, %swiglu_acc_7_3, %swiglu_dequant_7_3) : (memref<4096xbf16>, memref<2144xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @swiglu_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @swiglu_w_broadcast_7(Consume, 1)
          }
          func.call @w4a16_prefill_reuse_finish(%swiglu_acc_7_3, %swiglu_up_bf16_7_3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          %0 = aie.objectfifo.acquire @swiglu_gate_3_3(Consume, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          %2 = aie.objectfifo.acquire @swiglu_z_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @silu_mul_bf16(%1, %swiglu_up_bf16_7_3, %3) : (memref<1024xbf16>, memref<1024xbf16>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @swiglu_gate_3_3(Consume, 1)
          aie.objectfifo.release @swiglu_z_worker_7_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 4096 : i32}
    aie.runtime_sequence(%arg0: memref<2097152xbf16>, %arg1: memref<10977280xui8>, %arg2: memref<1310720xbf16>) {
      %0 = aiex.dma_configure_task_for @swiglu_z_host_1 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%0)
      %1 = aiex.dma_configure_task_for @swiglu_z_host_3 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 10240 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%1)
      %2 = aiex.dma_configure_task_for @swiglu_z_host_5 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 20480 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%2)
      %3 = aiex.dma_configure_task_for @swiglu_z_host_7 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 30720 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%3)
      %4 = aiex.dma_configure_task_for @swiglu_a_host_0 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 0 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%4)
      %5 = aiex.dma_configure_task_for @swiglu_a_host_1 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 131072 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%5)
      %6 = aiex.dma_configure_task_for @swiglu_a_host_2 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 262144 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%6)
      %7 = aiex.dma_configure_task_for @swiglu_a_host_3 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 393216 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%7)
      %8 = aiex.dma_configure_task_for @swiglu_w_host_0 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 0 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%8)
      %9 = aiex.dma_configure_task_for @swiglu_w_host_1 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 5488640 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%9)
      %10 = aiex.dma_configure_task_for @swiglu_w_host_2 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 1372160 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%10)
      %11 = aiex.dma_configure_task_for @swiglu_w_host_3 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 6860800 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%11)
      %12 = aiex.dma_configure_task_for @swiglu_w_host_4 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 2744320 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%12)
      %13 = aiex.dma_configure_task_for @swiglu_w_host_5 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 8232960 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%13)
      %14 = aiex.dma_configure_task_for @swiglu_w_host_6 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 4116480 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%14)
      %15 = aiex.dma_configure_task_for @swiglu_w_host_7 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 9605120 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%15)
      aiex.dma_await_task(%0)
      aiex.dma_await_task(%1)
      aiex.dma_await_task(%2)
      aiex.dma_await_task(%3)
      aiex.dma_free_task(%0)
      aiex.dma_free_task(%1)
      aiex.dma_free_task(%2)
      aiex.dma_free_task(%3)
      aiex.dma_free_task(%4)
      aiex.dma_free_task(%5)
      aiex.dma_free_task(%6)
      aiex.dma_free_task(%7)
      aiex.dma_free_task(%8)
      aiex.dma_free_task(%9)
      aiex.dma_free_task(%10)
      aiex.dma_free_task(%11)
      aiex.dma_free_task(%12)
      aiex.dma_free_task(%13)
      aiex.dma_free_task(%14)
      aiex.dma_free_task(%15)
      %16 = aiex.dma_configure_task_for @swiglu_z_host_1 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%16)
      %17 = aiex.dma_configure_task_for @swiglu_z_host_3 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 337920 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%17)
      %18 = aiex.dma_configure_task_for @swiglu_z_host_5 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 348160 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%18)
      %19 = aiex.dma_configure_task_for @swiglu_z_host_7 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 358400 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%19)
      %20 = aiex.dma_configure_task_for @swiglu_a_host_0 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 524288 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%20)
      %21 = aiex.dma_configure_task_for @swiglu_a_host_1 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 655360 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%21)
      %22 = aiex.dma_configure_task_for @swiglu_a_host_2 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 786432 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%22)
      %23 = aiex.dma_configure_task_for @swiglu_a_host_3 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 917504 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%23)
      %24 = aiex.dma_configure_task_for @swiglu_w_host_0 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 0 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%24)
      %25 = aiex.dma_configure_task_for @swiglu_w_host_1 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 5488640 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%25)
      %26 = aiex.dma_configure_task_for @swiglu_w_host_2 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 1372160 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%26)
      %27 = aiex.dma_configure_task_for @swiglu_w_host_3 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 6860800 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%27)
      %28 = aiex.dma_configure_task_for @swiglu_w_host_4 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 2744320 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%28)
      %29 = aiex.dma_configure_task_for @swiglu_w_host_5 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 8232960 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%29)
      %30 = aiex.dma_configure_task_for @swiglu_w_host_6 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 4116480 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%30)
      %31 = aiex.dma_configure_task_for @swiglu_w_host_7 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 9605120 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%31)
      aiex.dma_await_task(%16)
      aiex.dma_await_task(%17)
      aiex.dma_await_task(%18)
      aiex.dma_await_task(%19)
      aiex.dma_free_task(%16)
      aiex.dma_free_task(%17)
      aiex.dma_free_task(%18)
      aiex.dma_free_task(%19)
      aiex.dma_free_task(%20)
      aiex.dma_free_task(%21)
      aiex.dma_free_task(%22)
      aiex.dma_free_task(%23)
      aiex.dma_free_task(%24)
      aiex.dma_free_task(%25)
      aiex.dma_free_task(%26)
      aiex.dma_free_task(%27)
      aiex.dma_free_task(%28)
      aiex.dma_free_task(%29)
      aiex.dma_free_task(%30)
      aiex.dma_free_task(%31)
      %32 = aiex.dma_configure_task_for @swiglu_z_host_1 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%32)
      %33 = aiex.dma_configure_task_for @swiglu_z_host_3 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 665600 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%33)
      %34 = aiex.dma_configure_task_for @swiglu_z_host_5 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 675840 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%34)
      %35 = aiex.dma_configure_task_for @swiglu_z_host_7 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 686080 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%35)
      %36 = aiex.dma_configure_task_for @swiglu_a_host_0 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1048576 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%36)
      %37 = aiex.dma_configure_task_for @swiglu_a_host_1 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1179648 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%37)
      %38 = aiex.dma_configure_task_for @swiglu_a_host_2 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1310720 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%38)
      %39 = aiex.dma_configure_task_for @swiglu_a_host_3 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1441792 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%39)
      %40 = aiex.dma_configure_task_for @swiglu_w_host_0 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 0 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%40)
      %41 = aiex.dma_configure_task_for @swiglu_w_host_1 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 5488640 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%41)
      %42 = aiex.dma_configure_task_for @swiglu_w_host_2 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 1372160 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%42)
      %43 = aiex.dma_configure_task_for @swiglu_w_host_3 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 6860800 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%43)
      %44 = aiex.dma_configure_task_for @swiglu_w_host_4 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 2744320 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%44)
      %45 = aiex.dma_configure_task_for @swiglu_w_host_5 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 8232960 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%45)
      %46 = aiex.dma_configure_task_for @swiglu_w_host_6 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 4116480 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%46)
      %47 = aiex.dma_configure_task_for @swiglu_w_host_7 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 9605120 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%47)
      aiex.dma_await_task(%32)
      aiex.dma_await_task(%33)
      aiex.dma_await_task(%34)
      aiex.dma_await_task(%35)
      aiex.dma_free_task(%32)
      aiex.dma_free_task(%33)
      aiex.dma_free_task(%34)
      aiex.dma_free_task(%35)
      aiex.dma_free_task(%36)
      aiex.dma_free_task(%37)
      aiex.dma_free_task(%38)
      aiex.dma_free_task(%39)
      aiex.dma_free_task(%40)
      aiex.dma_free_task(%41)
      aiex.dma_free_task(%42)
      aiex.dma_free_task(%43)
      aiex.dma_free_task(%44)
      aiex.dma_free_task(%45)
      aiex.dma_free_task(%46)
      aiex.dma_free_task(%47)
      %48 = aiex.dma_configure_task_for @swiglu_z_host_1 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%48)
      %49 = aiex.dma_configure_task_for @swiglu_z_host_3 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 993280 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%49)
      %50 = aiex.dma_configure_task_for @swiglu_z_host_5 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 1003520 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%50)
      %51 = aiex.dma_configure_task_for @swiglu_z_host_7 {
        aie.dma_bd(%arg2 : memref<1310720xbf16> offset = 1013760 len = 81920 sizes = [1, 20, 8, 512] strides = [0, 512, 40960, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%51)
      %52 = aiex.dma_configure_task_for @swiglu_a_host_0 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1572864 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%52)
      %53 = aiex.dma_configure_task_for @swiglu_a_host_1 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1703936 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%53)
      %54 = aiex.dma_configure_task_for @swiglu_a_host_2 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1835008 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%54)
      %55 = aiex.dma_configure_task_for @swiglu_a_host_3 {
        aie.dma_bd(%arg0 : memref<2097152xbf16> offset = 1966080 len = 131072 sizes = [20, 128, 2, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {repeat_count = 19 : i32}
      aiex.dma_start_task(%55)
      %56 = aiex.dma_configure_task_for @swiglu_w_host_0 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 0 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%56)
      %57 = aiex.dma_configure_task_for @swiglu_w_host_1 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 5488640 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%57)
      %58 = aiex.dma_configure_task_for @swiglu_w_host_2 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 1372160 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%58)
      %59 = aiex.dma_configure_task_for @swiglu_w_host_3 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 6860800 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%59)
      %60 = aiex.dma_configure_task_for @swiglu_w_host_4 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 2744320 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%60)
      %61 = aiex.dma_configure_task_for @swiglu_w_host_5 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 8232960 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%61)
      %62 = aiex.dma_configure_task_for @swiglu_w_host_6 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 4116480 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%62)
      %63 = aiex.dma_configure_task_for @swiglu_w_host_7 {
        aie.dma_bd(%arg1 : memref<10977280xui8> offset = 9605120 len = 1372160 sizes = [1, 1, 1, 1372160] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%63)
      aiex.dma_await_task(%48)
      aiex.dma_await_task(%49)
      aiex.dma_await_task(%50)
      aiex.dma_await_task(%51)
      aiex.dma_free_task(%48)
      aiex.dma_free_task(%49)
      aiex.dma_free_task(%50)
      aiex.dma_free_task(%51)
      aiex.dma_free_task(%52)
      aiex.dma_free_task(%53)
      aiex.dma_free_task(%54)
      aiex.dma_free_task(%55)
      aiex.dma_free_task(%56)
      aiex.dma_free_task(%57)
      aiex.dma_free_task(%58)
      aiex.dma_free_task(%59)
      aiex.dma_free_task(%60)
      aiex.dma_free_task(%61)
      aiex.dma_free_task(%62)
      aiex.dma_free_task(%63)
    }
  }
}
