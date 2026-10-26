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
    %logical_mem_53 = aie.logical_tile<MemTile>(0, 1)
    %logical_shim_noc_54 = aie.logical_tile<ShimNOCTile>(0, 0)
    %logical_mem_55 = aie.logical_tile<MemTile>(1, 1)
    %logical_shim_noc_56 = aie.logical_tile<ShimNOCTile>(1, 0)
    %logical_mem_57 = aie.logical_tile<MemTile>(2, 1)
    %logical_shim_noc_58 = aie.logical_tile<ShimNOCTile>(2, 0)
    %logical_mem_59 = aie.logical_tile<MemTile>(3, 1)
    %logical_shim_noc_60 = aie.logical_tile<ShimNOCTile>(3, 0)
    %logical_mem_61 = aie.logical_tile<MemTile>(4, 1)
    %logical_shim_noc_62 = aie.logical_tile<ShimNOCTile>(4, 0)
    %logical_mem_63 = aie.logical_tile<MemTile>(5, 1)
    %logical_shim_noc_64 = aie.logical_tile<ShimNOCTile>(5, 0)
    %logical_mem_65 = aie.logical_tile<MemTile>(6, 1)
    %logical_shim_noc_66 = aie.logical_tile<ShimNOCTile>(6, 0)
    %logical_mem_67 = aie.logical_tile<MemTile>(7, 1)
    %logical_shim_noc_68 = aie.logical_tile<ShimNOCTile>(7, 0)
    aie.objectfifo @direct_a_broadcast_0(%logical_mem dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core, %logical_core_3, %logical_core_7, %logical_core_11, %logical_core_15, %logical_core_19, %logical_core_23, %logical_core_27}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_a_host_0(%logical_shim_noc, {%logical_mem}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo.link [@direct_a_host_0] -> [@direct_a_broadcast_0]([] [0])
    aie.objectfifo @direct_a_broadcast_1(%logical_mem_31 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_0, %logical_core_4, %logical_core_8, %logical_core_12, %logical_core_16, %logical_core_20, %logical_core_24, %logical_core_28}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_a_host_1(%logical_shim_noc_34, {%logical_mem_31}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo.link [@direct_a_host_1] -> [@direct_a_broadcast_1]([] [0])
    aie.objectfifo @direct_a_broadcast_2(%logical_mem_32 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_1, %logical_core_5, %logical_core_9, %logical_core_13, %logical_core_17, %logical_core_21, %logical_core_25, %logical_core_29}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_a_host_2(%logical_shim_noc_35, {%logical_mem_32}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo.link [@direct_a_host_2] -> [@direct_a_broadcast_2]([] [0])
    aie.objectfifo @direct_a_broadcast_3(%logical_mem_33 dimensionsToStream [<size = 2, stride = 512>, <size = 4, stride = 1024>, <size = 512, stride = 1>], {%logical_core_2, %logical_core_6, %logical_core_10, %logical_core_14, %logical_core_18, %logical_core_22, %logical_core_26, %logical_core_30}, 2 : i32) : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_a_host_3(%logical_shim_noc_36, {%logical_mem_33}, 2 : i32) {prod_dma_channel = 0 : i32} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo.link [@direct_a_host_3] -> [@direct_a_broadcast_3]([] [0])
    aie.objectfifo @direct_w_broadcast_0(%logical_mem_37, {%logical_core, %logical_core_0, %logical_core_1, %logical_core_2}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_0(%logical_shim_noc_45, {%logical_mem_37}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_0] -> [@direct_w_broadcast_0]([] [0])
    aie.objectfifo @direct_w_broadcast_1(%logical_mem_38, {%logical_core_3, %logical_core_4, %logical_core_5, %logical_core_6}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_1(%logical_shim_noc_46, {%logical_mem_38}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_1] -> [@direct_w_broadcast_1]([] [0])
    aie.objectfifo @direct_w_broadcast_2(%logical_mem_39, {%logical_core_7, %logical_core_8, %logical_core_9, %logical_core_10}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_2(%logical_shim_noc_47, {%logical_mem_39}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_2] -> [@direct_w_broadcast_2]([] [0])
    aie.objectfifo @direct_w_broadcast_3(%logical_mem_40, {%logical_core_11, %logical_core_12, %logical_core_13, %logical_core_14}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_3(%logical_shim_noc_48, {%logical_mem_40}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_3] -> [@direct_w_broadcast_3]([] [0])
    aie.objectfifo @direct_w_broadcast_4(%logical_mem_41, {%logical_core_15, %logical_core_16, %logical_core_17, %logical_core_18}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_4(%logical_shim_noc_49, {%logical_mem_41}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_4] -> [@direct_w_broadcast_4]([] [0])
    aie.objectfifo @direct_w_broadcast_5(%logical_mem_42, {%logical_core_19, %logical_core_20, %logical_core_21, %logical_core_22}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_5(%logical_shim_noc_50, {%logical_mem_42}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_5] -> [@direct_w_broadcast_5]([] [0])
    aie.objectfifo @direct_w_broadcast_6(%logical_mem_43, {%logical_core_23, %logical_core_24, %logical_core_25, %logical_core_26}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_6(%logical_shim_noc_51, {%logical_mem_43}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_6] -> [@direct_w_broadcast_6]([] [0])
    aie.objectfifo @direct_w_broadcast_7(%logical_mem_44, {%logical_core_27, %logical_core_28, %logical_core_29, %logical_core_30}, 2 : i32) : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo @direct_w_host_7(%logical_shim_noc_52, {%logical_mem_44}, 2 : i32) {prod_dma_channel = 1 : i32} : !aie.objectfifo<memref<4352xui8>>
    aie.objectfifo.link [@direct_w_host_7] -> [@direct_w_broadcast_7]([] [0])
    aie.objectfifo @direct_y_host_0(%logical_mem_53, {%logical_shim_noc_54}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_0_0(%logical_core, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_0_1(%logical_core_0, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_0_2(%logical_core_1, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_0_3(%logical_core_2, {%logical_mem_53}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_0_0, @direct_y_worker_0_1, @direct_y_worker_0_2, @direct_y_worker_0_3] -> [@direct_y_host_0]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_1(%logical_mem_55, {%logical_shim_noc_56}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_1_0(%logical_core_3, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_1_1(%logical_core_4, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_1_2(%logical_core_5, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_1_3(%logical_core_6, {%logical_mem_55}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_1_0, @direct_y_worker_1_1, @direct_y_worker_1_2, @direct_y_worker_1_3] -> [@direct_y_host_1]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_2(%logical_mem_57, {%logical_shim_noc_58}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_2_0(%logical_core_7, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_2_1(%logical_core_8, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_2_2(%logical_core_9, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_2_3(%logical_core_10, {%logical_mem_57}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_2_0, @direct_y_worker_2_1, @direct_y_worker_2_2, @direct_y_worker_2_3] -> [@direct_y_host_2]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_3(%logical_mem_59, {%logical_shim_noc_60}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_3_0(%logical_core_11, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_3_1(%logical_core_12, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_3_2(%logical_core_13, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_3_3(%logical_core_14, {%logical_mem_59}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_3_0, @direct_y_worker_3_1, @direct_y_worker_3_2, @direct_y_worker_3_3] -> [@direct_y_host_3]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_4(%logical_mem_61, {%logical_shim_noc_62}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_4_0(%logical_core_15, {%logical_mem_61}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_4_1(%logical_core_16, {%logical_mem_61}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_4_2(%logical_core_17, {%logical_mem_61}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_4_3(%logical_core_18, {%logical_mem_61}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_4_0, @direct_y_worker_4_1, @direct_y_worker_4_2, @direct_y_worker_4_3] -> [@direct_y_host_4]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_5(%logical_mem_63, {%logical_shim_noc_64}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_5_0(%logical_core_19, {%logical_mem_63}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_5_1(%logical_core_20, {%logical_mem_63}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_5_2(%logical_core_21, {%logical_mem_63}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_5_3(%logical_core_22, {%logical_mem_63}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_5_0, @direct_y_worker_5_1, @direct_y_worker_5_2, @direct_y_worker_5_3] -> [@direct_y_host_5]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_6(%logical_mem_65, {%logical_shim_noc_66}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_6_0(%logical_core_23, {%logical_mem_65}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_6_1(%logical_core_24, {%logical_mem_65}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_6_2(%logical_core_25, {%logical_mem_65}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_6_3(%logical_core_26, {%logical_mem_65}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_6_0, @direct_y_worker_6_1, @direct_y_worker_6_2, @direct_y_worker_6_3] -> [@direct_y_host_6]([0, 1024, 2048, 3072] [])
    aie.objectfifo @direct_y_host_7(%logical_mem_67, {%logical_shim_noc_68}, 2 : i32) {cons_dma_channels = array<i32: 0>} : !aie.objectfifo<memref<4096xbf16>>
    aie.objectfifo @direct_y_worker_7_0(%logical_core_27, {%logical_mem_67}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_7_1(%logical_core_28, {%logical_mem_67}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_7_2(%logical_core_29, {%logical_mem_67}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo @direct_y_worker_7_3(%logical_core_30, {%logical_mem_67}, 2 : i32) : !aie.objectfifo<memref<1024xbf16>>
    aie.objectfifo.link [@direct_y_worker_7_0, @direct_y_worker_7_1, @direct_y_worker_7_2, @direct_y_worker_7_3] -> [@direct_y_host_7]([0, 1024, 2048, 3072] [])
    %direct_acc0_0_0 = aie.buffer(%logical_core) {sym_name = "direct_acc0_0_0"} : memref<1024xf32>
    %direct_acc1_0_0 = aie.buffer(%logical_core) {sym_name = "direct_acc1_0_0"} : memref<1024xf32>
    %direct_dequant_0_0 = aie.buffer(%logical_core) {sym_name = "direct_dequant_0_0"} : memref<4096xbf16>
    func.func private @w4a16_prefill_reuse_init(memref<1024xf32>) attributes {link_with = "w4a16_prefill_reuse_bf16_0c5db4b1a9334cad1e30bdaab43c390bf5eed6b430f3969bd3d45ad01fd72368_8768ada43abd02bde39395e8d826206ab8ad6324d0ee0b067733fbe76a2f290e_r2.o"}
    func.func private @w4a16_prefill_reuse_accumulate_low(memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) attributes {link_with = "w4a16_prefill_reuse_bf16_0c5db4b1a9334cad1e30bdaab43c390bf5eed6b430f3969bd3d45ad01fd72368_8768ada43abd02bde39395e8d826206ab8ad6324d0ee0b067733fbe76a2f290e_r2.o"}
    func.func private @w4a16_prefill_reuse_accumulate_high(memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) attributes {link_with = "w4a16_prefill_reuse_bf16_0c5db4b1a9334cad1e30bdaab43c390bf5eed6b430f3969bd3d45ad01fd72368_8768ada43abd02bde39395e8d826206ab8ad6324d0ee0b067733fbe76a2f290e_r2.o"}
    func.func private @w4a16_prefill_reuse_finish(memref<1024xf32>, memref<1024xbf16>) attributes {link_with = "w4a16_prefill_reuse_bf16_0c5db4b1a9334cad1e30bdaab43c390bf5eed6b430f3969bd3d45ad01fd72368_8768ada43abd02bde39395e8d826206ab8ad6324d0ee0b067733fbe76a2f290e_r2.o"}
    %direct_acc0_0_1 = aie.buffer(%logical_core_0) {sym_name = "direct_acc0_0_1"} : memref<1024xf32>
    %direct_acc1_0_1 = aie.buffer(%logical_core_0) {sym_name = "direct_acc1_0_1"} : memref<1024xf32>
    %direct_dequant_0_1 = aie.buffer(%logical_core_0) {sym_name = "direct_dequant_0_1"} : memref<4096xbf16>
    %direct_acc0_0_2 = aie.buffer(%logical_core_1) {sym_name = "direct_acc0_0_2"} : memref<1024xf32>
    %direct_acc1_0_2 = aie.buffer(%logical_core_1) {sym_name = "direct_acc1_0_2"} : memref<1024xf32>
    %direct_dequant_0_2 = aie.buffer(%logical_core_1) {sym_name = "direct_dequant_0_2"} : memref<4096xbf16>
    %direct_acc0_0_3 = aie.buffer(%logical_core_2) {sym_name = "direct_acc0_0_3"} : memref<1024xf32>
    %direct_acc1_0_3 = aie.buffer(%logical_core_2) {sym_name = "direct_acc1_0_3"} : memref<1024xf32>
    %direct_dequant_0_3 = aie.buffer(%logical_core_2) {sym_name = "direct_dequant_0_3"} : memref<4096xbf16>
    %direct_acc0_1_0 = aie.buffer(%logical_core_3) {sym_name = "direct_acc0_1_0"} : memref<1024xf32>
    %direct_acc1_1_0 = aie.buffer(%logical_core_3) {sym_name = "direct_acc1_1_0"} : memref<1024xf32>
    %direct_dequant_1_0 = aie.buffer(%logical_core_3) {sym_name = "direct_dequant_1_0"} : memref<4096xbf16>
    %direct_acc0_1_1 = aie.buffer(%logical_core_4) {sym_name = "direct_acc0_1_1"} : memref<1024xf32>
    %direct_acc1_1_1 = aie.buffer(%logical_core_4) {sym_name = "direct_acc1_1_1"} : memref<1024xf32>
    %direct_dequant_1_1 = aie.buffer(%logical_core_4) {sym_name = "direct_dequant_1_1"} : memref<4096xbf16>
    %direct_acc0_1_2 = aie.buffer(%logical_core_5) {sym_name = "direct_acc0_1_2"} : memref<1024xf32>
    %direct_acc1_1_2 = aie.buffer(%logical_core_5) {sym_name = "direct_acc1_1_2"} : memref<1024xf32>
    %direct_dequant_1_2 = aie.buffer(%logical_core_5) {sym_name = "direct_dequant_1_2"} : memref<4096xbf16>
    %direct_acc0_1_3 = aie.buffer(%logical_core_6) {sym_name = "direct_acc0_1_3"} : memref<1024xf32>
    %direct_acc1_1_3 = aie.buffer(%logical_core_6) {sym_name = "direct_acc1_1_3"} : memref<1024xf32>
    %direct_dequant_1_3 = aie.buffer(%logical_core_6) {sym_name = "direct_dequant_1_3"} : memref<4096xbf16>
    %direct_acc0_2_0 = aie.buffer(%logical_core_7) {sym_name = "direct_acc0_2_0"} : memref<1024xf32>
    %direct_acc1_2_0 = aie.buffer(%logical_core_7) {sym_name = "direct_acc1_2_0"} : memref<1024xf32>
    %direct_dequant_2_0 = aie.buffer(%logical_core_7) {sym_name = "direct_dequant_2_0"} : memref<4096xbf16>
    %direct_acc0_2_1 = aie.buffer(%logical_core_8) {sym_name = "direct_acc0_2_1"} : memref<1024xf32>
    %direct_acc1_2_1 = aie.buffer(%logical_core_8) {sym_name = "direct_acc1_2_1"} : memref<1024xf32>
    %direct_dequant_2_1 = aie.buffer(%logical_core_8) {sym_name = "direct_dequant_2_1"} : memref<4096xbf16>
    %direct_acc0_2_2 = aie.buffer(%logical_core_9) {sym_name = "direct_acc0_2_2"} : memref<1024xf32>
    %direct_acc1_2_2 = aie.buffer(%logical_core_9) {sym_name = "direct_acc1_2_2"} : memref<1024xf32>
    %direct_dequant_2_2 = aie.buffer(%logical_core_9) {sym_name = "direct_dequant_2_2"} : memref<4096xbf16>
    %direct_acc0_2_3 = aie.buffer(%logical_core_10) {sym_name = "direct_acc0_2_3"} : memref<1024xf32>
    %direct_acc1_2_3 = aie.buffer(%logical_core_10) {sym_name = "direct_acc1_2_3"} : memref<1024xf32>
    %direct_dequant_2_3 = aie.buffer(%logical_core_10) {sym_name = "direct_dequant_2_3"} : memref<4096xbf16>
    %direct_acc0_3_0 = aie.buffer(%logical_core_11) {sym_name = "direct_acc0_3_0"} : memref<1024xf32>
    %direct_acc1_3_0 = aie.buffer(%logical_core_11) {sym_name = "direct_acc1_3_0"} : memref<1024xf32>
    %direct_dequant_3_0 = aie.buffer(%logical_core_11) {sym_name = "direct_dequant_3_0"} : memref<4096xbf16>
    %direct_acc0_3_1 = aie.buffer(%logical_core_12) {sym_name = "direct_acc0_3_1"} : memref<1024xf32>
    %direct_acc1_3_1 = aie.buffer(%logical_core_12) {sym_name = "direct_acc1_3_1"} : memref<1024xf32>
    %direct_dequant_3_1 = aie.buffer(%logical_core_12) {sym_name = "direct_dequant_3_1"} : memref<4096xbf16>
    %direct_acc0_3_2 = aie.buffer(%logical_core_13) {sym_name = "direct_acc0_3_2"} : memref<1024xf32>
    %direct_acc1_3_2 = aie.buffer(%logical_core_13) {sym_name = "direct_acc1_3_2"} : memref<1024xf32>
    %direct_dequant_3_2 = aie.buffer(%logical_core_13) {sym_name = "direct_dequant_3_2"} : memref<4096xbf16>
    %direct_acc0_3_3 = aie.buffer(%logical_core_14) {sym_name = "direct_acc0_3_3"} : memref<1024xf32>
    %direct_acc1_3_3 = aie.buffer(%logical_core_14) {sym_name = "direct_acc1_3_3"} : memref<1024xf32>
    %direct_dequant_3_3 = aie.buffer(%logical_core_14) {sym_name = "direct_dequant_3_3"} : memref<4096xbf16>
    %direct_acc0_4_0 = aie.buffer(%logical_core_15) {sym_name = "direct_acc0_4_0"} : memref<1024xf32>
    %direct_acc1_4_0 = aie.buffer(%logical_core_15) {sym_name = "direct_acc1_4_0"} : memref<1024xf32>
    %direct_dequant_4_0 = aie.buffer(%logical_core_15) {sym_name = "direct_dequant_4_0"} : memref<4096xbf16>
    %direct_acc0_4_1 = aie.buffer(%logical_core_16) {sym_name = "direct_acc0_4_1"} : memref<1024xf32>
    %direct_acc1_4_1 = aie.buffer(%logical_core_16) {sym_name = "direct_acc1_4_1"} : memref<1024xf32>
    %direct_dequant_4_1 = aie.buffer(%logical_core_16) {sym_name = "direct_dequant_4_1"} : memref<4096xbf16>
    %direct_acc0_4_2 = aie.buffer(%logical_core_17) {sym_name = "direct_acc0_4_2"} : memref<1024xf32>
    %direct_acc1_4_2 = aie.buffer(%logical_core_17) {sym_name = "direct_acc1_4_2"} : memref<1024xf32>
    %direct_dequant_4_2 = aie.buffer(%logical_core_17) {sym_name = "direct_dequant_4_2"} : memref<4096xbf16>
    %direct_acc0_4_3 = aie.buffer(%logical_core_18) {sym_name = "direct_acc0_4_3"} : memref<1024xf32>
    %direct_acc1_4_3 = aie.buffer(%logical_core_18) {sym_name = "direct_acc1_4_3"} : memref<1024xf32>
    %direct_dequant_4_3 = aie.buffer(%logical_core_18) {sym_name = "direct_dequant_4_3"} : memref<4096xbf16>
    %direct_acc0_5_0 = aie.buffer(%logical_core_19) {sym_name = "direct_acc0_5_0"} : memref<1024xf32>
    %direct_acc1_5_0 = aie.buffer(%logical_core_19) {sym_name = "direct_acc1_5_0"} : memref<1024xf32>
    %direct_dequant_5_0 = aie.buffer(%logical_core_19) {sym_name = "direct_dequant_5_0"} : memref<4096xbf16>
    %direct_acc0_5_1 = aie.buffer(%logical_core_20) {sym_name = "direct_acc0_5_1"} : memref<1024xf32>
    %direct_acc1_5_1 = aie.buffer(%logical_core_20) {sym_name = "direct_acc1_5_1"} : memref<1024xf32>
    %direct_dequant_5_1 = aie.buffer(%logical_core_20) {sym_name = "direct_dequant_5_1"} : memref<4096xbf16>
    %direct_acc0_5_2 = aie.buffer(%logical_core_21) {sym_name = "direct_acc0_5_2"} : memref<1024xf32>
    %direct_acc1_5_2 = aie.buffer(%logical_core_21) {sym_name = "direct_acc1_5_2"} : memref<1024xf32>
    %direct_dequant_5_2 = aie.buffer(%logical_core_21) {sym_name = "direct_dequant_5_2"} : memref<4096xbf16>
    %direct_acc0_5_3 = aie.buffer(%logical_core_22) {sym_name = "direct_acc0_5_3"} : memref<1024xf32>
    %direct_acc1_5_3 = aie.buffer(%logical_core_22) {sym_name = "direct_acc1_5_3"} : memref<1024xf32>
    %direct_dequant_5_3 = aie.buffer(%logical_core_22) {sym_name = "direct_dequant_5_3"} : memref<4096xbf16>
    %direct_acc0_6_0 = aie.buffer(%logical_core_23) {sym_name = "direct_acc0_6_0"} : memref<1024xf32>
    %direct_acc1_6_0 = aie.buffer(%logical_core_23) {sym_name = "direct_acc1_6_0"} : memref<1024xf32>
    %direct_dequant_6_0 = aie.buffer(%logical_core_23) {sym_name = "direct_dequant_6_0"} : memref<4096xbf16>
    %direct_acc0_6_1 = aie.buffer(%logical_core_24) {sym_name = "direct_acc0_6_1"} : memref<1024xf32>
    %direct_acc1_6_1 = aie.buffer(%logical_core_24) {sym_name = "direct_acc1_6_1"} : memref<1024xf32>
    %direct_dequant_6_1 = aie.buffer(%logical_core_24) {sym_name = "direct_dequant_6_1"} : memref<4096xbf16>
    %direct_acc0_6_2 = aie.buffer(%logical_core_25) {sym_name = "direct_acc0_6_2"} : memref<1024xf32>
    %direct_acc1_6_2 = aie.buffer(%logical_core_25) {sym_name = "direct_acc1_6_2"} : memref<1024xf32>
    %direct_dequant_6_2 = aie.buffer(%logical_core_25) {sym_name = "direct_dequant_6_2"} : memref<4096xbf16>
    %direct_acc0_6_3 = aie.buffer(%logical_core_26) {sym_name = "direct_acc0_6_3"} : memref<1024xf32>
    %direct_acc1_6_3 = aie.buffer(%logical_core_26) {sym_name = "direct_acc1_6_3"} : memref<1024xf32>
    %direct_dequant_6_3 = aie.buffer(%logical_core_26) {sym_name = "direct_dequant_6_3"} : memref<4096xbf16>
    %direct_acc0_7_0 = aie.buffer(%logical_core_27) {sym_name = "direct_acc0_7_0"} : memref<1024xf32>
    %direct_acc1_7_0 = aie.buffer(%logical_core_27) {sym_name = "direct_acc1_7_0"} : memref<1024xf32>
    %direct_dequant_7_0 = aie.buffer(%logical_core_27) {sym_name = "direct_dequant_7_0"} : memref<4096xbf16>
    %direct_acc0_7_1 = aie.buffer(%logical_core_28) {sym_name = "direct_acc0_7_1"} : memref<1024xf32>
    %direct_acc1_7_1 = aie.buffer(%logical_core_28) {sym_name = "direct_acc1_7_1"} : memref<1024xf32>
    %direct_dequant_7_1 = aie.buffer(%logical_core_28) {sym_name = "direct_dequant_7_1"} : memref<4096xbf16>
    %direct_acc0_7_2 = aie.buffer(%logical_core_29) {sym_name = "direct_acc0_7_2"} : memref<1024xf32>
    %direct_acc1_7_2 = aie.buffer(%logical_core_29) {sym_name = "direct_acc1_7_2"} : memref<1024xf32>
    %direct_dequant_7_2 = aie.buffer(%logical_core_29) {sym_name = "direct_dequant_7_2"} : memref<4096xbf16>
    %direct_acc0_7_3 = aie.buffer(%logical_core_30) {sym_name = "direct_acc0_7_3"} : memref<1024xf32>
    %direct_acc1_7_3 = aie.buffer(%logical_core_30) {sym_name = "direct_acc1_7_3"} : memref<1024xf32>
    %direct_dequant_7_3 = aie.buffer(%logical_core_30) {sym_name = "direct_dequant_7_3"} : memref<4096xbf16>
    %core_0_2 = aie.core(%logical_core) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_0, %direct_dequant_0_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_0_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_0_3 = aie.core(%logical_core_0) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_1, %direct_dequant_0_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_0_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_0_4 = aie.core(%logical_core_1) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_2, %direct_dequant_0_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_0_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_0_5 = aie.core(%logical_core_2) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_0_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_0_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_0_3, %direct_dequant_0_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_0(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_0_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_0_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_0_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_0_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_1_2 = aie.core(%logical_core_3) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_0, %direct_dequant_1_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_1_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_1_3 = aie.core(%logical_core_4) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_1, %direct_dequant_1_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_1_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_1_4 = aie.core(%logical_core_5) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_2, %direct_dequant_1_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_1_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_1_5 = aie.core(%logical_core_6) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_1_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_1_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_1_3, %direct_dequant_1_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_1(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_1_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_1_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_1_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_1_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_2_2 = aie.core(%logical_core_7) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_0, %direct_dequant_2_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_2_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_2_3 = aie.core(%logical_core_8) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_1, %direct_dequant_2_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_2_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_2_4 = aie.core(%logical_core_9) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_2, %direct_dequant_2_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_2_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_2_5 = aie.core(%logical_core_10) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_2_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_2_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_2_3, %direct_dequant_2_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_2(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_2_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_2_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_2_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_2_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_3_2 = aie.core(%logical_core_11) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_0, %direct_dequant_3_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_3_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_3_3 = aie.core(%logical_core_12) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_1, %direct_dequant_3_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_3_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_3_4 = aie.core(%logical_core_13) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_2, %direct_dequant_3_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_3_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_3_5 = aie.core(%logical_core_14) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_3_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_3_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_3_3, %direct_dequant_3_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_3(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_3_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_3_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_3_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_3_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_4_2 = aie.core(%logical_core_15) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_0, %direct_dequant_4_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_4_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_4_3 = aie.core(%logical_core_16) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_1, %direct_dequant_4_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_4_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_4_4 = aie.core(%logical_core_17) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_2, %direct_dequant_4_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_4_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_4_5 = aie.core(%logical_core_18) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_4_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_4_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_4(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_4_3, %direct_dequant_4_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_4(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_4_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_4_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_4_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_4_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_5_2 = aie.core(%logical_core_19) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_0, %direct_dequant_5_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_5_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_5_3 = aie.core(%logical_core_20) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_1, %direct_dequant_5_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_5_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_5_4 = aie.core(%logical_core_21) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_2, %direct_dequant_5_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_5_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_5_5 = aie.core(%logical_core_22) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_5_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_5_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_5(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_5_3, %direct_dequant_5_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_5(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_5_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_5_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_5_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_5_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_6_2 = aie.core(%logical_core_23) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_0, %direct_dequant_6_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_6_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_6_3 = aie.core(%logical_core_24) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_1, %direct_dequant_6_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_6_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_6_4 = aie.core(%logical_core_25) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_2, %direct_dequant_6_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_6_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_6_5 = aie.core(%logical_core_26) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_6_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_6_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_6(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_6_3, %direct_dequant_6_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_6(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_6_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_6_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_6_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_6_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_7_2 = aie.core(%logical_core_27) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_0) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_0) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_0(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_0, %direct_dequant_7_0) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_0(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_0, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_7_0(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_0, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_0(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_7_3 = aie.core(%logical_core_28) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_1) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_1) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_1(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_1, %direct_dequant_7_1) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_1(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_1, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_7_1(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_1, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_1(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_7_4 = aie.core(%logical_core_29) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_2) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_2) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_2(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_2, %direct_dequant_7_2) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_2(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_2, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_7_2(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_2, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_2(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    %core_7_5 = aie.core(%logical_core_30) {
      %c0 = arith.constant 0 : index
      %c9223372036854775807 = arith.constant 9223372036854775807 : index
      %c1 = arith.constant 1 : index
      scf.for %arg0 = %c0 to %c9223372036854775807 step %c1 {
        %c0_69 = arith.constant 0 : index
        %c4 = arith.constant 4 : index
        %c1_70 = arith.constant 1 : index
        scf.for %arg1 = %c0_69 to %c4 step %c1_70 {
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_71 = arith.constant 0 : index
          %c20 = arith.constant 20 : index
          %c1_72 = arith.constant 1 : index
          scf.for %arg2 = %c0_71 to %c20 step %c1_72 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %0 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %1 = aie.objectfifo.subview.access %0[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %1) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %2 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %3 = aie.objectfifo.subview.access %2[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %3) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_73 = arith.constant 0 : index
          %c20_74 = arith.constant 20 : index
          %c1_75 = arith.constant 1 : index
          scf.for %arg2 = %c0_73 to %c20_74 step %c1_75 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %4 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %5) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %6 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %7 = aie.objectfifo.subview.access %6[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %7) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_76 = arith.constant 0 : index
          %c20_77 = arith.constant 20 : index
          %c1_78 = arith.constant 1 : index
          scf.for %arg2 = %c0_76 to %c20_77 step %c1_78 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %8 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %9 = aie.objectfifo.subview.access %8[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %9) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %10 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %11 = aie.objectfifo.subview.access %10[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %11) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_79 = arith.constant 0 : index
          %c20_80 = arith.constant 20 : index
          %c1_81 = arith.constant 1 : index
          scf.for %arg2 = %c0_79 to %c20_80 step %c1_81 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %12 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %13 = aie.objectfifo.subview.access %12[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %13) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %14 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %15 = aie.objectfifo.subview.access %14[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %15) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_82 = arith.constant 0 : index
          %c20_83 = arith.constant 20 : index
          %c1_84 = arith.constant 1 : index
          scf.for %arg2 = %c0_82 to %c20_83 step %c1_84 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %16 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %17 = aie.objectfifo.subview.access %16[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %17) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %18 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %19 = aie.objectfifo.subview.access %18[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %19) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_85 = arith.constant 0 : index
          %c20_86 = arith.constant 20 : index
          %c1_87 = arith.constant 1 : index
          scf.for %arg2 = %c0_85 to %c20_86 step %c1_87 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %20 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %21 = aie.objectfifo.subview.access %20[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %21) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %22 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %23 = aie.objectfifo.subview.access %22[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %23) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_88 = arith.constant 0 : index
          %c20_89 = arith.constant 20 : index
          %c1_90 = arith.constant 1 : index
          scf.for %arg2 = %c0_88 to %c20_89 step %c1_90 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %24 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %25 = aie.objectfifo.subview.access %24[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %25) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %26 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %27 = aie.objectfifo.subview.access %26[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %27) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          func.call @w4a16_prefill_reuse_init(%direct_acc0_7_3) : (memref<1024xf32>) -> ()
          func.call @w4a16_prefill_reuse_init(%direct_acc1_7_3) : (memref<1024xf32>) -> ()
          %c0_91 = arith.constant 0 : index
          %c20_92 = arith.constant 20 : index
          %c1_93 = arith.constant 1 : index
          scf.for %arg2 = %c0_91 to %c20_92 step %c1_93 {
            %32 = aie.objectfifo.acquire @direct_a_broadcast_3(Consume, 1) : !aie.objectfifosubview<memref<4096xbf16>>
            %33 = aie.objectfifo.subview.access %32[0] : !aie.objectfifosubview<memref<4096xbf16>> -> memref<4096xbf16>
            %34 = aie.objectfifo.acquire @direct_w_broadcast_7(Consume, 1) : !aie.objectfifosubview<memref<4352xui8>>
            %35 = aie.objectfifo.subview.access %34[0] : !aie.objectfifosubview<memref<4352xui8>> -> memref<4352xui8>
            func.call @w4a16_prefill_reuse_accumulate_low(%33, %35, %direct_acc0_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            func.call @w4a16_prefill_reuse_accumulate_high(%33, %35, %direct_acc1_7_3, %direct_dequant_7_3) : (memref<4096xbf16>, memref<4352xui8>, memref<1024xf32>, memref<4096xbf16>) -> ()
            aie.objectfifo.release @direct_a_broadcast_3(Consume, 1)
            aie.objectfifo.release @direct_w_broadcast_7(Consume, 1)
          }
          %28 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %29 = aie.objectfifo.subview.access %28[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc0_7_3, %29) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
          %30 = aie.objectfifo.acquire @direct_y_worker_7_3(Produce, 1) : !aie.objectfifosubview<memref<1024xbf16>>
          %31 = aie.objectfifo.subview.access %30[0] : !aie.objectfifosubview<memref<1024xbf16>> -> memref<1024xbf16>
          func.call @w4a16_prefill_reuse_finish(%direct_acc1_7_3, %31) : (memref<1024xf32>, memref<1024xbf16>) -> ()
          aie.objectfifo.release @direct_y_worker_7_3(Produce, 1)
        }
      }
      aie.end
    } {dynamic_objfifo_lowering = true, stack_size = 2048 : i32}
    aie.runtime_sequence(%arg0: memref<1310720xbf16>, %arg1: memref<31195136xui8>, %arg2: memref<2097152xbf16>) {
      %0 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 0 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%0)
      %1 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 8192 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%1)
      %2 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 16384 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%2)
      %3 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 24576 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%3)
      %4 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 32768 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%4)
      %5 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 40960 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%5)
      %6 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 49152 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%6)
      %7 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 57344 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%7)
      %8 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%8)
      %9 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%9)
      %10 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%10)
      %11 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%11)
      %12 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 0 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%12)
      %13 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 487424 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%13)
      %14 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 974848 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%14)
      %15 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1462272 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%15)
      %16 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1949696 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%16)
      %17 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2437120 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%17)
      %18 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2924544 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%18)
      %19 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3411968 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%19)
      %20 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1024 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%20)
      %21 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 9216 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%21)
      %22 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 17408 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%22)
      %23 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 25600 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%23)
      %24 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 33792 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%24)
      %25 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 41984 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%25)
      %26 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 50176 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%26)
      %27 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 58368 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%27)
      %28 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%28)
      %29 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%29)
      %30 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%30)
      %31 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%31)
      %32 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3899392 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%32)
      %33 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4386816 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%33)
      %34 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4874240 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%34)
      %35 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5361664 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%35)
      %36 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5849088 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%36)
      %37 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6336512 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%37)
      %38 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6823936 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%38)
      %39 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7311360 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%39)
      aiex.dma_await_task(%0)
      aiex.dma_await_task(%1)
      aiex.dma_await_task(%2)
      aiex.dma_await_task(%3)
      aiex.dma_await_task(%4)
      aiex.dma_await_task(%5)
      aiex.dma_await_task(%6)
      aiex.dma_await_task(%7)
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
      aiex.dma_free_task(%16)
      aiex.dma_free_task(%17)
      aiex.dma_free_task(%18)
      aiex.dma_free_task(%19)
      %40 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 2048 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%40)
      %41 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 10240 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%41)
      %42 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 18432 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%42)
      %43 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 26624 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%43)
      %44 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 34816 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%44)
      %45 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 43008 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%45)
      %46 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 51200 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%46)
      %47 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 59392 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%47)
      %48 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%48)
      %49 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%49)
      %50 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%50)
      %51 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%51)
      %52 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7798784 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%52)
      %53 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8286208 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%53)
      %54 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8773632 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%54)
      %55 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9261056 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%55)
      %56 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9748480 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%56)
      %57 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10235904 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%57)
      %58 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10723328 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%58)
      %59 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11210752 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%59)
      aiex.dma_await_task(%20)
      aiex.dma_await_task(%21)
      aiex.dma_await_task(%22)
      aiex.dma_await_task(%23)
      aiex.dma_await_task(%24)
      aiex.dma_await_task(%25)
      aiex.dma_await_task(%26)
      aiex.dma_await_task(%27)
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
      aiex.dma_free_task(%32)
      aiex.dma_free_task(%33)
      aiex.dma_free_task(%34)
      aiex.dma_free_task(%35)
      aiex.dma_free_task(%36)
      aiex.dma_free_task(%37)
      aiex.dma_free_task(%38)
      aiex.dma_free_task(%39)
      %60 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 3072 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%60)
      %61 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 11264 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%61)
      %62 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 19456 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%62)
      %63 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 27648 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%63)
      %64 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 35840 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%64)
      %65 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 44032 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%65)
      %66 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 52224 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%66)
      %67 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 60416 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%67)
      %68 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%68)
      %69 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%69)
      %70 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%70)
      %71 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%71)
      %72 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11698176 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%72)
      %73 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12185600 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%73)
      %74 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12673024 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%74)
      %75 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13160448 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%75)
      %76 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13647872 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%76)
      %77 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14135296 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%77)
      %78 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14622720 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%78)
      %79 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15110144 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%79)
      aiex.dma_await_task(%40)
      aiex.dma_await_task(%41)
      aiex.dma_await_task(%42)
      aiex.dma_await_task(%43)
      aiex.dma_await_task(%44)
      aiex.dma_await_task(%45)
      aiex.dma_await_task(%46)
      aiex.dma_await_task(%47)
      aiex.dma_free_task(%40)
      aiex.dma_free_task(%41)
      aiex.dma_free_task(%42)
      aiex.dma_free_task(%43)
      aiex.dma_free_task(%44)
      aiex.dma_free_task(%45)
      aiex.dma_free_task(%46)
      aiex.dma_free_task(%47)
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
      %80 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 4096 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%80)
      %81 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 12288 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%81)
      %82 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 20480 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%82)
      %83 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 28672 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%83)
      %84 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 36864 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%84)
      %85 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 45056 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%85)
      %86 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 53248 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%86)
      %87 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 61440 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%87)
      %88 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%88)
      %89 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%89)
      %90 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%90)
      %91 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%91)
      %92 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15597568 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%92)
      %93 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16084992 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%93)
      %94 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16572416 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%94)
      %95 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17059840 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%95)
      %96 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17547264 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%96)
      %97 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18034688 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%97)
      %98 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18522112 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%98)
      %99 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19009536 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%99)
      aiex.dma_await_task(%60)
      aiex.dma_await_task(%61)
      aiex.dma_await_task(%62)
      aiex.dma_await_task(%63)
      aiex.dma_await_task(%64)
      aiex.dma_await_task(%65)
      aiex.dma_await_task(%66)
      aiex.dma_await_task(%67)
      aiex.dma_free_task(%60)
      aiex.dma_free_task(%61)
      aiex.dma_free_task(%62)
      aiex.dma_free_task(%63)
      aiex.dma_free_task(%64)
      aiex.dma_free_task(%65)
      aiex.dma_free_task(%66)
      aiex.dma_free_task(%67)
      aiex.dma_free_task(%68)
      aiex.dma_free_task(%69)
      aiex.dma_free_task(%70)
      aiex.dma_free_task(%71)
      aiex.dma_free_task(%72)
      aiex.dma_free_task(%73)
      aiex.dma_free_task(%74)
      aiex.dma_free_task(%75)
      aiex.dma_free_task(%76)
      aiex.dma_free_task(%77)
      aiex.dma_free_task(%78)
      aiex.dma_free_task(%79)
      %100 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 5120 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%100)
      %101 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 13312 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%101)
      %102 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 21504 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%102)
      %103 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 29696 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%103)
      %104 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 37888 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%104)
      %105 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 46080 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%105)
      %106 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 54272 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%106)
      %107 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 62464 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%107)
      %108 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%108)
      %109 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%109)
      %110 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%110)
      %111 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%111)
      %112 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19496960 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%112)
      %113 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19984384 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%113)
      %114 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20471808 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%114)
      %115 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20959232 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%115)
      %116 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21446656 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%116)
      %117 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21934080 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%117)
      %118 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22421504 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%118)
      %119 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22908928 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%119)
      aiex.dma_await_task(%80)
      aiex.dma_await_task(%81)
      aiex.dma_await_task(%82)
      aiex.dma_await_task(%83)
      aiex.dma_await_task(%84)
      aiex.dma_await_task(%85)
      aiex.dma_await_task(%86)
      aiex.dma_await_task(%87)
      aiex.dma_free_task(%80)
      aiex.dma_free_task(%81)
      aiex.dma_free_task(%82)
      aiex.dma_free_task(%83)
      aiex.dma_free_task(%84)
      aiex.dma_free_task(%85)
      aiex.dma_free_task(%86)
      aiex.dma_free_task(%87)
      aiex.dma_free_task(%88)
      aiex.dma_free_task(%89)
      aiex.dma_free_task(%90)
      aiex.dma_free_task(%91)
      aiex.dma_free_task(%92)
      aiex.dma_free_task(%93)
      aiex.dma_free_task(%94)
      aiex.dma_free_task(%95)
      aiex.dma_free_task(%96)
      aiex.dma_free_task(%97)
      aiex.dma_free_task(%98)
      aiex.dma_free_task(%99)
      %120 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 6144 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%120)
      %121 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 14336 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%121)
      %122 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 22528 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%122)
      %123 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 30720 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%123)
      %124 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 38912 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%124)
      %125 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 47104 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%125)
      %126 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 55296 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%126)
      %127 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 63488 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%127)
      %128 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%128)
      %129 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%129)
      %130 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%130)
      %131 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%131)
      %132 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23396352 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%132)
      %133 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23883776 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%133)
      %134 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24371200 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%134)
      %135 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24858624 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%135)
      %136 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25346048 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%136)
      %137 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25833472 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%137)
      %138 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26320896 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%138)
      %139 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26808320 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%139)
      aiex.dma_await_task(%100)
      aiex.dma_await_task(%101)
      aiex.dma_await_task(%102)
      aiex.dma_await_task(%103)
      aiex.dma_await_task(%104)
      aiex.dma_await_task(%105)
      aiex.dma_await_task(%106)
      aiex.dma_await_task(%107)
      aiex.dma_free_task(%100)
      aiex.dma_free_task(%101)
      aiex.dma_free_task(%102)
      aiex.dma_free_task(%103)
      aiex.dma_free_task(%104)
      aiex.dma_free_task(%105)
      aiex.dma_free_task(%106)
      aiex.dma_free_task(%107)
      aiex.dma_free_task(%108)
      aiex.dma_free_task(%109)
      aiex.dma_free_task(%110)
      aiex.dma_free_task(%111)
      aiex.dma_free_task(%112)
      aiex.dma_free_task(%113)
      aiex.dma_free_task(%114)
      aiex.dma_free_task(%115)
      aiex.dma_free_task(%116)
      aiex.dma_free_task(%117)
      aiex.dma_free_task(%118)
      aiex.dma_free_task(%119)
      %140 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 7168 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%140)
      %141 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 15360 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%141)
      %142 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 23552 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%142)
      %143 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 31744 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%143)
      %144 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 39936 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%144)
      %145 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 48128 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%145)
      %146 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 56320 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%146)
      %147 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 64512 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%147)
      %148 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 0 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%148)
      %149 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 81920 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%149)
      %150 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 163840 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%150)
      %151 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 245760 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%151)
      %152 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27295744 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%152)
      %153 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27783168 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%153)
      %154 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28270592 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%154)
      %155 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28758016 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%155)
      %156 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29245440 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%156)
      %157 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29732864 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%157)
      %158 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30220288 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%158)
      %159 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30707712 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%159)
      aiex.dma_await_task(%120)
      aiex.dma_await_task(%121)
      aiex.dma_await_task(%122)
      aiex.dma_await_task(%123)
      aiex.dma_await_task(%124)
      aiex.dma_await_task(%125)
      aiex.dma_await_task(%126)
      aiex.dma_await_task(%127)
      aiex.dma_free_task(%120)
      aiex.dma_free_task(%121)
      aiex.dma_free_task(%122)
      aiex.dma_free_task(%123)
      aiex.dma_free_task(%124)
      aiex.dma_free_task(%125)
      aiex.dma_free_task(%126)
      aiex.dma_free_task(%127)
      aiex.dma_free_task(%128)
      aiex.dma_free_task(%129)
      aiex.dma_free_task(%130)
      aiex.dma_free_task(%131)
      aiex.dma_free_task(%132)
      aiex.dma_free_task(%133)
      aiex.dma_free_task(%134)
      aiex.dma_free_task(%135)
      aiex.dma_free_task(%136)
      aiex.dma_free_task(%137)
      aiex.dma_free_task(%138)
      aiex.dma_free_task(%139)
      %160 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 524288 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%160)
      %161 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 532480 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%161)
      %162 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 540672 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%162)
      %163 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 548864 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%163)
      %164 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 557056 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%164)
      %165 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 565248 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%165)
      %166 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 573440 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%166)
      %167 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 581632 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%167)
      %168 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%168)
      %169 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%169)
      %170 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%170)
      %171 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%171)
      %172 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 0 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%172)
      %173 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 487424 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%173)
      %174 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 974848 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%174)
      %175 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1462272 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%175)
      %176 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1949696 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%176)
      %177 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2437120 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%177)
      %178 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2924544 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%178)
      %179 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3411968 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%179)
      aiex.dma_await_task(%140)
      aiex.dma_await_task(%141)
      aiex.dma_await_task(%142)
      aiex.dma_await_task(%143)
      aiex.dma_await_task(%144)
      aiex.dma_await_task(%145)
      aiex.dma_await_task(%146)
      aiex.dma_await_task(%147)
      aiex.dma_free_task(%140)
      aiex.dma_free_task(%141)
      aiex.dma_free_task(%142)
      aiex.dma_free_task(%143)
      aiex.dma_free_task(%144)
      aiex.dma_free_task(%145)
      aiex.dma_free_task(%146)
      aiex.dma_free_task(%147)
      aiex.dma_free_task(%148)
      aiex.dma_free_task(%149)
      aiex.dma_free_task(%150)
      aiex.dma_free_task(%151)
      aiex.dma_free_task(%152)
      aiex.dma_free_task(%153)
      aiex.dma_free_task(%154)
      aiex.dma_free_task(%155)
      aiex.dma_free_task(%156)
      aiex.dma_free_task(%157)
      aiex.dma_free_task(%158)
      aiex.dma_free_task(%159)
      %180 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 525312 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%180)
      %181 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 533504 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%181)
      %182 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 541696 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%182)
      %183 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 549888 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%183)
      %184 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 558080 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%184)
      %185 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 566272 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%185)
      %186 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 574464 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%186)
      %187 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 582656 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%187)
      %188 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%188)
      %189 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%189)
      %190 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%190)
      %191 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%191)
      %192 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3899392 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%192)
      %193 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4386816 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%193)
      %194 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4874240 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%194)
      %195 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5361664 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%195)
      %196 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5849088 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%196)
      %197 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6336512 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%197)
      %198 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6823936 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%198)
      %199 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7311360 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%199)
      aiex.dma_await_task(%160)
      aiex.dma_await_task(%161)
      aiex.dma_await_task(%162)
      aiex.dma_await_task(%163)
      aiex.dma_await_task(%164)
      aiex.dma_await_task(%165)
      aiex.dma_await_task(%166)
      aiex.dma_await_task(%167)
      aiex.dma_free_task(%160)
      aiex.dma_free_task(%161)
      aiex.dma_free_task(%162)
      aiex.dma_free_task(%163)
      aiex.dma_free_task(%164)
      aiex.dma_free_task(%165)
      aiex.dma_free_task(%166)
      aiex.dma_free_task(%167)
      aiex.dma_free_task(%168)
      aiex.dma_free_task(%169)
      aiex.dma_free_task(%170)
      aiex.dma_free_task(%171)
      aiex.dma_free_task(%172)
      aiex.dma_free_task(%173)
      aiex.dma_free_task(%174)
      aiex.dma_free_task(%175)
      aiex.dma_free_task(%176)
      aiex.dma_free_task(%177)
      aiex.dma_free_task(%178)
      aiex.dma_free_task(%179)
      %200 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 526336 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%200)
      %201 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 534528 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%201)
      %202 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 542720 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%202)
      %203 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 550912 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%203)
      %204 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 559104 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%204)
      %205 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 567296 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%205)
      %206 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 575488 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%206)
      %207 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 583680 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%207)
      %208 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%208)
      %209 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%209)
      %210 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%210)
      %211 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%211)
      %212 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7798784 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%212)
      %213 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8286208 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%213)
      %214 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8773632 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%214)
      %215 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9261056 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%215)
      %216 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9748480 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%216)
      %217 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10235904 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%217)
      %218 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10723328 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%218)
      %219 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11210752 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%219)
      aiex.dma_await_task(%180)
      aiex.dma_await_task(%181)
      aiex.dma_await_task(%182)
      aiex.dma_await_task(%183)
      aiex.dma_await_task(%184)
      aiex.dma_await_task(%185)
      aiex.dma_await_task(%186)
      aiex.dma_await_task(%187)
      aiex.dma_free_task(%180)
      aiex.dma_free_task(%181)
      aiex.dma_free_task(%182)
      aiex.dma_free_task(%183)
      aiex.dma_free_task(%184)
      aiex.dma_free_task(%185)
      aiex.dma_free_task(%186)
      aiex.dma_free_task(%187)
      aiex.dma_free_task(%188)
      aiex.dma_free_task(%189)
      aiex.dma_free_task(%190)
      aiex.dma_free_task(%191)
      aiex.dma_free_task(%192)
      aiex.dma_free_task(%193)
      aiex.dma_free_task(%194)
      aiex.dma_free_task(%195)
      aiex.dma_free_task(%196)
      aiex.dma_free_task(%197)
      aiex.dma_free_task(%198)
      aiex.dma_free_task(%199)
      %220 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 527360 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%220)
      %221 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 535552 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%221)
      %222 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 543744 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%222)
      %223 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 551936 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%223)
      %224 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 560128 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%224)
      %225 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 568320 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%225)
      %226 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 576512 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%226)
      %227 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 584704 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%227)
      %228 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%228)
      %229 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%229)
      %230 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%230)
      %231 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%231)
      %232 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11698176 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%232)
      %233 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12185600 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%233)
      %234 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12673024 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%234)
      %235 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13160448 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%235)
      %236 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13647872 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%236)
      %237 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14135296 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%237)
      %238 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14622720 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%238)
      %239 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15110144 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%239)
      aiex.dma_await_task(%200)
      aiex.dma_await_task(%201)
      aiex.dma_await_task(%202)
      aiex.dma_await_task(%203)
      aiex.dma_await_task(%204)
      aiex.dma_await_task(%205)
      aiex.dma_await_task(%206)
      aiex.dma_await_task(%207)
      aiex.dma_free_task(%200)
      aiex.dma_free_task(%201)
      aiex.dma_free_task(%202)
      aiex.dma_free_task(%203)
      aiex.dma_free_task(%204)
      aiex.dma_free_task(%205)
      aiex.dma_free_task(%206)
      aiex.dma_free_task(%207)
      aiex.dma_free_task(%208)
      aiex.dma_free_task(%209)
      aiex.dma_free_task(%210)
      aiex.dma_free_task(%211)
      aiex.dma_free_task(%212)
      aiex.dma_free_task(%213)
      aiex.dma_free_task(%214)
      aiex.dma_free_task(%215)
      aiex.dma_free_task(%216)
      aiex.dma_free_task(%217)
      aiex.dma_free_task(%218)
      aiex.dma_free_task(%219)
      %240 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 528384 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%240)
      %241 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 536576 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%241)
      %242 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 544768 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%242)
      %243 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 552960 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%243)
      %244 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 561152 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%244)
      %245 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 569344 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%245)
      %246 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 577536 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%246)
      %247 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 585728 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%247)
      %248 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%248)
      %249 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%249)
      %250 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%250)
      %251 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%251)
      %252 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15597568 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%252)
      %253 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16084992 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%253)
      %254 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16572416 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%254)
      %255 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17059840 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%255)
      %256 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17547264 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%256)
      %257 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18034688 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%257)
      %258 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18522112 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%258)
      %259 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19009536 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%259)
      aiex.dma_await_task(%220)
      aiex.dma_await_task(%221)
      aiex.dma_await_task(%222)
      aiex.dma_await_task(%223)
      aiex.dma_await_task(%224)
      aiex.dma_await_task(%225)
      aiex.dma_await_task(%226)
      aiex.dma_await_task(%227)
      aiex.dma_free_task(%220)
      aiex.dma_free_task(%221)
      aiex.dma_free_task(%222)
      aiex.dma_free_task(%223)
      aiex.dma_free_task(%224)
      aiex.dma_free_task(%225)
      aiex.dma_free_task(%226)
      aiex.dma_free_task(%227)
      aiex.dma_free_task(%228)
      aiex.dma_free_task(%229)
      aiex.dma_free_task(%230)
      aiex.dma_free_task(%231)
      aiex.dma_free_task(%232)
      aiex.dma_free_task(%233)
      aiex.dma_free_task(%234)
      aiex.dma_free_task(%235)
      aiex.dma_free_task(%236)
      aiex.dma_free_task(%237)
      aiex.dma_free_task(%238)
      aiex.dma_free_task(%239)
      %260 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 529408 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%260)
      %261 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 537600 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%261)
      %262 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 545792 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%262)
      %263 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 553984 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%263)
      %264 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 562176 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%264)
      %265 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 570368 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%265)
      %266 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 578560 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%266)
      %267 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 586752 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%267)
      %268 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%268)
      %269 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%269)
      %270 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%270)
      %271 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%271)
      %272 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19496960 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%272)
      %273 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19984384 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%273)
      %274 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20471808 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%274)
      %275 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20959232 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%275)
      %276 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21446656 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%276)
      %277 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21934080 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%277)
      %278 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22421504 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%278)
      %279 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22908928 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%279)
      aiex.dma_await_task(%240)
      aiex.dma_await_task(%241)
      aiex.dma_await_task(%242)
      aiex.dma_await_task(%243)
      aiex.dma_await_task(%244)
      aiex.dma_await_task(%245)
      aiex.dma_await_task(%246)
      aiex.dma_await_task(%247)
      aiex.dma_free_task(%240)
      aiex.dma_free_task(%241)
      aiex.dma_free_task(%242)
      aiex.dma_free_task(%243)
      aiex.dma_free_task(%244)
      aiex.dma_free_task(%245)
      aiex.dma_free_task(%246)
      aiex.dma_free_task(%247)
      aiex.dma_free_task(%248)
      aiex.dma_free_task(%249)
      aiex.dma_free_task(%250)
      aiex.dma_free_task(%251)
      aiex.dma_free_task(%252)
      aiex.dma_free_task(%253)
      aiex.dma_free_task(%254)
      aiex.dma_free_task(%255)
      aiex.dma_free_task(%256)
      aiex.dma_free_task(%257)
      aiex.dma_free_task(%258)
      aiex.dma_free_task(%259)
      %280 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 530432 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%280)
      %281 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 538624 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%281)
      %282 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 546816 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%282)
      %283 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 555008 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%283)
      %284 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 563200 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%284)
      %285 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 571392 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%285)
      %286 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 579584 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%286)
      %287 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 587776 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%287)
      %288 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%288)
      %289 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%289)
      %290 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%290)
      %291 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%291)
      %292 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23396352 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%292)
      %293 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23883776 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%293)
      %294 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24371200 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%294)
      %295 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24858624 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%295)
      %296 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25346048 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%296)
      %297 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25833472 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%297)
      %298 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26320896 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%298)
      %299 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26808320 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%299)
      aiex.dma_await_task(%260)
      aiex.dma_await_task(%261)
      aiex.dma_await_task(%262)
      aiex.dma_await_task(%263)
      aiex.dma_await_task(%264)
      aiex.dma_await_task(%265)
      aiex.dma_await_task(%266)
      aiex.dma_await_task(%267)
      aiex.dma_free_task(%260)
      aiex.dma_free_task(%261)
      aiex.dma_free_task(%262)
      aiex.dma_free_task(%263)
      aiex.dma_free_task(%264)
      aiex.dma_free_task(%265)
      aiex.dma_free_task(%266)
      aiex.dma_free_task(%267)
      aiex.dma_free_task(%268)
      aiex.dma_free_task(%269)
      aiex.dma_free_task(%270)
      aiex.dma_free_task(%271)
      aiex.dma_free_task(%272)
      aiex.dma_free_task(%273)
      aiex.dma_free_task(%274)
      aiex.dma_free_task(%275)
      aiex.dma_free_task(%276)
      aiex.dma_free_task(%277)
      aiex.dma_free_task(%278)
      aiex.dma_free_task(%279)
      %300 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 531456 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%300)
      %301 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 539648 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%301)
      %302 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 547840 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%302)
      %303 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 556032 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%303)
      %304 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 564224 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%304)
      %305 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 572416 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%305)
      %306 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 580608 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%306)
      %307 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 588800 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%307)
      %308 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 327680 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%308)
      %309 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 409600 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%309)
      %310 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 491520 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%310)
      %311 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 573440 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%311)
      %312 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27295744 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%312)
      %313 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27783168 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%313)
      %314 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28270592 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%314)
      %315 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28758016 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%315)
      %316 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29245440 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%316)
      %317 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29732864 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%317)
      %318 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30220288 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%318)
      %319 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30707712 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%319)
      aiex.dma_await_task(%280)
      aiex.dma_await_task(%281)
      aiex.dma_await_task(%282)
      aiex.dma_await_task(%283)
      aiex.dma_await_task(%284)
      aiex.dma_await_task(%285)
      aiex.dma_await_task(%286)
      aiex.dma_await_task(%287)
      aiex.dma_free_task(%280)
      aiex.dma_free_task(%281)
      aiex.dma_free_task(%282)
      aiex.dma_free_task(%283)
      aiex.dma_free_task(%284)
      aiex.dma_free_task(%285)
      aiex.dma_free_task(%286)
      aiex.dma_free_task(%287)
      aiex.dma_free_task(%288)
      aiex.dma_free_task(%289)
      aiex.dma_free_task(%290)
      aiex.dma_free_task(%291)
      aiex.dma_free_task(%292)
      aiex.dma_free_task(%293)
      aiex.dma_free_task(%294)
      aiex.dma_free_task(%295)
      aiex.dma_free_task(%296)
      aiex.dma_free_task(%297)
      aiex.dma_free_task(%298)
      aiex.dma_free_task(%299)
      %320 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1048576 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%320)
      %321 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1056768 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%321)
      %322 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1064960 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%322)
      %323 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1073152 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%323)
      %324 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1081344 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%324)
      %325 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1089536 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%325)
      %326 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1097728 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%326)
      %327 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1105920 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%327)
      %328 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%328)
      %329 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%329)
      %330 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%330)
      %331 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%331)
      %332 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 0 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%332)
      %333 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 487424 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%333)
      %334 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 974848 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%334)
      %335 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1462272 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%335)
      %336 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1949696 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%336)
      %337 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2437120 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%337)
      %338 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2924544 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%338)
      %339 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3411968 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%339)
      aiex.dma_await_task(%300)
      aiex.dma_await_task(%301)
      aiex.dma_await_task(%302)
      aiex.dma_await_task(%303)
      aiex.dma_await_task(%304)
      aiex.dma_await_task(%305)
      aiex.dma_await_task(%306)
      aiex.dma_await_task(%307)
      aiex.dma_free_task(%300)
      aiex.dma_free_task(%301)
      aiex.dma_free_task(%302)
      aiex.dma_free_task(%303)
      aiex.dma_free_task(%304)
      aiex.dma_free_task(%305)
      aiex.dma_free_task(%306)
      aiex.dma_free_task(%307)
      aiex.dma_free_task(%308)
      aiex.dma_free_task(%309)
      aiex.dma_free_task(%310)
      aiex.dma_free_task(%311)
      aiex.dma_free_task(%312)
      aiex.dma_free_task(%313)
      aiex.dma_free_task(%314)
      aiex.dma_free_task(%315)
      aiex.dma_free_task(%316)
      aiex.dma_free_task(%317)
      aiex.dma_free_task(%318)
      aiex.dma_free_task(%319)
      %340 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1049600 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%340)
      %341 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1057792 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%341)
      %342 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1065984 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%342)
      %343 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1074176 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%343)
      %344 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1082368 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%344)
      %345 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1090560 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%345)
      %346 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1098752 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%346)
      %347 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1106944 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%347)
      %348 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%348)
      %349 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%349)
      %350 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%350)
      %351 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%351)
      %352 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3899392 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%352)
      %353 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4386816 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%353)
      %354 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4874240 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%354)
      %355 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5361664 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%355)
      %356 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5849088 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%356)
      %357 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6336512 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%357)
      %358 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6823936 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%358)
      %359 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7311360 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%359)
      aiex.dma_await_task(%320)
      aiex.dma_await_task(%321)
      aiex.dma_await_task(%322)
      aiex.dma_await_task(%323)
      aiex.dma_await_task(%324)
      aiex.dma_await_task(%325)
      aiex.dma_await_task(%326)
      aiex.dma_await_task(%327)
      aiex.dma_free_task(%320)
      aiex.dma_free_task(%321)
      aiex.dma_free_task(%322)
      aiex.dma_free_task(%323)
      aiex.dma_free_task(%324)
      aiex.dma_free_task(%325)
      aiex.dma_free_task(%326)
      aiex.dma_free_task(%327)
      aiex.dma_free_task(%328)
      aiex.dma_free_task(%329)
      aiex.dma_free_task(%330)
      aiex.dma_free_task(%331)
      aiex.dma_free_task(%332)
      aiex.dma_free_task(%333)
      aiex.dma_free_task(%334)
      aiex.dma_free_task(%335)
      aiex.dma_free_task(%336)
      aiex.dma_free_task(%337)
      aiex.dma_free_task(%338)
      aiex.dma_free_task(%339)
      %360 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1050624 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%360)
      %361 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1058816 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%361)
      %362 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1067008 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%362)
      %363 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1075200 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%363)
      %364 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1083392 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%364)
      %365 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1091584 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%365)
      %366 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1099776 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%366)
      %367 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1107968 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%367)
      %368 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%368)
      %369 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%369)
      %370 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%370)
      %371 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%371)
      %372 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7798784 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%372)
      %373 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8286208 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%373)
      %374 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8773632 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%374)
      %375 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9261056 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%375)
      %376 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9748480 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%376)
      %377 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10235904 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%377)
      %378 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10723328 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%378)
      %379 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11210752 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%379)
      aiex.dma_await_task(%340)
      aiex.dma_await_task(%341)
      aiex.dma_await_task(%342)
      aiex.dma_await_task(%343)
      aiex.dma_await_task(%344)
      aiex.dma_await_task(%345)
      aiex.dma_await_task(%346)
      aiex.dma_await_task(%347)
      aiex.dma_free_task(%340)
      aiex.dma_free_task(%341)
      aiex.dma_free_task(%342)
      aiex.dma_free_task(%343)
      aiex.dma_free_task(%344)
      aiex.dma_free_task(%345)
      aiex.dma_free_task(%346)
      aiex.dma_free_task(%347)
      aiex.dma_free_task(%348)
      aiex.dma_free_task(%349)
      aiex.dma_free_task(%350)
      aiex.dma_free_task(%351)
      aiex.dma_free_task(%352)
      aiex.dma_free_task(%353)
      aiex.dma_free_task(%354)
      aiex.dma_free_task(%355)
      aiex.dma_free_task(%356)
      aiex.dma_free_task(%357)
      aiex.dma_free_task(%358)
      aiex.dma_free_task(%359)
      %380 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1051648 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%380)
      %381 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1059840 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%381)
      %382 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1068032 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%382)
      %383 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1076224 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%383)
      %384 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1084416 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%384)
      %385 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1092608 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%385)
      %386 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1100800 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%386)
      %387 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1108992 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%387)
      %388 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%388)
      %389 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%389)
      %390 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%390)
      %391 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%391)
      %392 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11698176 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%392)
      %393 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12185600 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%393)
      %394 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12673024 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%394)
      %395 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13160448 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%395)
      %396 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13647872 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%396)
      %397 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14135296 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%397)
      %398 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14622720 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%398)
      %399 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15110144 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%399)
      aiex.dma_await_task(%360)
      aiex.dma_await_task(%361)
      aiex.dma_await_task(%362)
      aiex.dma_await_task(%363)
      aiex.dma_await_task(%364)
      aiex.dma_await_task(%365)
      aiex.dma_await_task(%366)
      aiex.dma_await_task(%367)
      aiex.dma_free_task(%360)
      aiex.dma_free_task(%361)
      aiex.dma_free_task(%362)
      aiex.dma_free_task(%363)
      aiex.dma_free_task(%364)
      aiex.dma_free_task(%365)
      aiex.dma_free_task(%366)
      aiex.dma_free_task(%367)
      aiex.dma_free_task(%368)
      aiex.dma_free_task(%369)
      aiex.dma_free_task(%370)
      aiex.dma_free_task(%371)
      aiex.dma_free_task(%372)
      aiex.dma_free_task(%373)
      aiex.dma_free_task(%374)
      aiex.dma_free_task(%375)
      aiex.dma_free_task(%376)
      aiex.dma_free_task(%377)
      aiex.dma_free_task(%378)
      aiex.dma_free_task(%379)
      %400 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1052672 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%400)
      %401 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1060864 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%401)
      %402 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1069056 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%402)
      %403 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1077248 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%403)
      %404 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1085440 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%404)
      %405 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1093632 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%405)
      %406 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1101824 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%406)
      %407 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1110016 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%407)
      %408 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%408)
      %409 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%409)
      %410 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%410)
      %411 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%411)
      %412 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15597568 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%412)
      %413 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16084992 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%413)
      %414 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16572416 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%414)
      %415 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17059840 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%415)
      %416 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17547264 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%416)
      %417 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18034688 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%417)
      %418 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18522112 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%418)
      %419 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19009536 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%419)
      aiex.dma_await_task(%380)
      aiex.dma_await_task(%381)
      aiex.dma_await_task(%382)
      aiex.dma_await_task(%383)
      aiex.dma_await_task(%384)
      aiex.dma_await_task(%385)
      aiex.dma_await_task(%386)
      aiex.dma_await_task(%387)
      aiex.dma_free_task(%380)
      aiex.dma_free_task(%381)
      aiex.dma_free_task(%382)
      aiex.dma_free_task(%383)
      aiex.dma_free_task(%384)
      aiex.dma_free_task(%385)
      aiex.dma_free_task(%386)
      aiex.dma_free_task(%387)
      aiex.dma_free_task(%388)
      aiex.dma_free_task(%389)
      aiex.dma_free_task(%390)
      aiex.dma_free_task(%391)
      aiex.dma_free_task(%392)
      aiex.dma_free_task(%393)
      aiex.dma_free_task(%394)
      aiex.dma_free_task(%395)
      aiex.dma_free_task(%396)
      aiex.dma_free_task(%397)
      aiex.dma_free_task(%398)
      aiex.dma_free_task(%399)
      %420 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1053696 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%420)
      %421 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1061888 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%421)
      %422 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1070080 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%422)
      %423 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1078272 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%423)
      %424 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1086464 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%424)
      %425 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1094656 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%425)
      %426 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1102848 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%426)
      %427 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1111040 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%427)
      %428 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%428)
      %429 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%429)
      %430 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%430)
      %431 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%431)
      %432 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19496960 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%432)
      %433 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19984384 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%433)
      %434 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20471808 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%434)
      %435 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20959232 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%435)
      %436 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21446656 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%436)
      %437 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21934080 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%437)
      %438 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22421504 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%438)
      %439 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22908928 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%439)
      aiex.dma_await_task(%400)
      aiex.dma_await_task(%401)
      aiex.dma_await_task(%402)
      aiex.dma_await_task(%403)
      aiex.dma_await_task(%404)
      aiex.dma_await_task(%405)
      aiex.dma_await_task(%406)
      aiex.dma_await_task(%407)
      aiex.dma_free_task(%400)
      aiex.dma_free_task(%401)
      aiex.dma_free_task(%402)
      aiex.dma_free_task(%403)
      aiex.dma_free_task(%404)
      aiex.dma_free_task(%405)
      aiex.dma_free_task(%406)
      aiex.dma_free_task(%407)
      aiex.dma_free_task(%408)
      aiex.dma_free_task(%409)
      aiex.dma_free_task(%410)
      aiex.dma_free_task(%411)
      aiex.dma_free_task(%412)
      aiex.dma_free_task(%413)
      aiex.dma_free_task(%414)
      aiex.dma_free_task(%415)
      aiex.dma_free_task(%416)
      aiex.dma_free_task(%417)
      aiex.dma_free_task(%418)
      aiex.dma_free_task(%419)
      %440 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1054720 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%440)
      %441 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1062912 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%441)
      %442 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1071104 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%442)
      %443 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1079296 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%443)
      %444 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1087488 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%444)
      %445 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1095680 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%445)
      %446 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1103872 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%446)
      %447 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1112064 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%447)
      %448 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%448)
      %449 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%449)
      %450 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%450)
      %451 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%451)
      %452 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23396352 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%452)
      %453 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23883776 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%453)
      %454 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24371200 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%454)
      %455 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24858624 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%455)
      %456 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25346048 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%456)
      %457 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25833472 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%457)
      %458 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26320896 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%458)
      %459 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26808320 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%459)
      aiex.dma_await_task(%420)
      aiex.dma_await_task(%421)
      aiex.dma_await_task(%422)
      aiex.dma_await_task(%423)
      aiex.dma_await_task(%424)
      aiex.dma_await_task(%425)
      aiex.dma_await_task(%426)
      aiex.dma_await_task(%427)
      aiex.dma_free_task(%420)
      aiex.dma_free_task(%421)
      aiex.dma_free_task(%422)
      aiex.dma_free_task(%423)
      aiex.dma_free_task(%424)
      aiex.dma_free_task(%425)
      aiex.dma_free_task(%426)
      aiex.dma_free_task(%427)
      aiex.dma_free_task(%428)
      aiex.dma_free_task(%429)
      aiex.dma_free_task(%430)
      aiex.dma_free_task(%431)
      aiex.dma_free_task(%432)
      aiex.dma_free_task(%433)
      aiex.dma_free_task(%434)
      aiex.dma_free_task(%435)
      aiex.dma_free_task(%436)
      aiex.dma_free_task(%437)
      aiex.dma_free_task(%438)
      aiex.dma_free_task(%439)
      %460 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1055744 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%460)
      %461 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1063936 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%461)
      %462 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1072128 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%462)
      %463 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1080320 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%463)
      %464 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1088512 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%464)
      %465 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1096704 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%465)
      %466 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1104896 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%466)
      %467 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1113088 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%467)
      %468 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 655360 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%468)
      %469 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 737280 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%469)
      %470 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 819200 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%470)
      %471 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 901120 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%471)
      %472 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27295744 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%472)
      %473 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27783168 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%473)
      %474 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28270592 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%474)
      %475 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28758016 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%475)
      %476 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29245440 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%476)
      %477 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29732864 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%477)
      %478 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30220288 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%478)
      %479 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30707712 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%479)
      aiex.dma_await_task(%440)
      aiex.dma_await_task(%441)
      aiex.dma_await_task(%442)
      aiex.dma_await_task(%443)
      aiex.dma_await_task(%444)
      aiex.dma_await_task(%445)
      aiex.dma_await_task(%446)
      aiex.dma_await_task(%447)
      aiex.dma_free_task(%440)
      aiex.dma_free_task(%441)
      aiex.dma_free_task(%442)
      aiex.dma_free_task(%443)
      aiex.dma_free_task(%444)
      aiex.dma_free_task(%445)
      aiex.dma_free_task(%446)
      aiex.dma_free_task(%447)
      aiex.dma_free_task(%448)
      aiex.dma_free_task(%449)
      aiex.dma_free_task(%450)
      aiex.dma_free_task(%451)
      aiex.dma_free_task(%452)
      aiex.dma_free_task(%453)
      aiex.dma_free_task(%454)
      aiex.dma_free_task(%455)
      aiex.dma_free_task(%456)
      aiex.dma_free_task(%457)
      aiex.dma_free_task(%458)
      aiex.dma_free_task(%459)
      %480 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1572864 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%480)
      %481 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1581056 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%481)
      %482 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1589248 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%482)
      %483 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1597440 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%483)
      %484 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1605632 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%484)
      %485 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1613824 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%485)
      %486 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1622016 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%486)
      %487 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1630208 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%487)
      %488 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%488)
      %489 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%489)
      %490 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%490)
      %491 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%491)
      %492 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 0 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%492)
      %493 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 487424 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%493)
      %494 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 974848 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%494)
      %495 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1462272 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%495)
      %496 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 1949696 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%496)
      %497 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2437120 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%497)
      %498 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 2924544 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%498)
      %499 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3411968 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%499)
      aiex.dma_await_task(%460)
      aiex.dma_await_task(%461)
      aiex.dma_await_task(%462)
      aiex.dma_await_task(%463)
      aiex.dma_await_task(%464)
      aiex.dma_await_task(%465)
      aiex.dma_await_task(%466)
      aiex.dma_await_task(%467)
      aiex.dma_free_task(%460)
      aiex.dma_free_task(%461)
      aiex.dma_free_task(%462)
      aiex.dma_free_task(%463)
      aiex.dma_free_task(%464)
      aiex.dma_free_task(%465)
      aiex.dma_free_task(%466)
      aiex.dma_free_task(%467)
      aiex.dma_free_task(%468)
      aiex.dma_free_task(%469)
      aiex.dma_free_task(%470)
      aiex.dma_free_task(%471)
      aiex.dma_free_task(%472)
      aiex.dma_free_task(%473)
      aiex.dma_free_task(%474)
      aiex.dma_free_task(%475)
      aiex.dma_free_task(%476)
      aiex.dma_free_task(%477)
      aiex.dma_free_task(%478)
      aiex.dma_free_task(%479)
      %500 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1573888 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%500)
      %501 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1582080 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%501)
      %502 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1590272 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%502)
      %503 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1598464 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%503)
      %504 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1606656 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%504)
      %505 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1614848 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%505)
      %506 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1623040 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%506)
      %507 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1631232 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%507)
      %508 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%508)
      %509 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%509)
      %510 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%510)
      %511 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%511)
      %512 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 3899392 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%512)
      %513 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4386816 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%513)
      %514 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 4874240 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%514)
      %515 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5361664 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%515)
      %516 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 5849088 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%516)
      %517 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6336512 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%517)
      %518 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 6823936 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%518)
      %519 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7311360 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%519)
      aiex.dma_await_task(%480)
      aiex.dma_await_task(%481)
      aiex.dma_await_task(%482)
      aiex.dma_await_task(%483)
      aiex.dma_await_task(%484)
      aiex.dma_await_task(%485)
      aiex.dma_await_task(%486)
      aiex.dma_await_task(%487)
      aiex.dma_free_task(%480)
      aiex.dma_free_task(%481)
      aiex.dma_free_task(%482)
      aiex.dma_free_task(%483)
      aiex.dma_free_task(%484)
      aiex.dma_free_task(%485)
      aiex.dma_free_task(%486)
      aiex.dma_free_task(%487)
      aiex.dma_free_task(%488)
      aiex.dma_free_task(%489)
      aiex.dma_free_task(%490)
      aiex.dma_free_task(%491)
      aiex.dma_free_task(%492)
      aiex.dma_free_task(%493)
      aiex.dma_free_task(%494)
      aiex.dma_free_task(%495)
      aiex.dma_free_task(%496)
      aiex.dma_free_task(%497)
      aiex.dma_free_task(%498)
      aiex.dma_free_task(%499)
      %520 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1574912 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%520)
      %521 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1583104 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%521)
      %522 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1591296 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%522)
      %523 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1599488 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%523)
      %524 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1607680 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%524)
      %525 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1615872 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%525)
      %526 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1624064 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%526)
      %527 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1632256 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%527)
      %528 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%528)
      %529 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%529)
      %530 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%530)
      %531 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%531)
      %532 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 7798784 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%532)
      %533 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8286208 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%533)
      %534 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 8773632 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%534)
      %535 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9261056 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%535)
      %536 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 9748480 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%536)
      %537 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10235904 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%537)
      %538 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 10723328 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%538)
      %539 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11210752 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%539)
      aiex.dma_await_task(%500)
      aiex.dma_await_task(%501)
      aiex.dma_await_task(%502)
      aiex.dma_await_task(%503)
      aiex.dma_await_task(%504)
      aiex.dma_await_task(%505)
      aiex.dma_await_task(%506)
      aiex.dma_await_task(%507)
      aiex.dma_free_task(%500)
      aiex.dma_free_task(%501)
      aiex.dma_free_task(%502)
      aiex.dma_free_task(%503)
      aiex.dma_free_task(%504)
      aiex.dma_free_task(%505)
      aiex.dma_free_task(%506)
      aiex.dma_free_task(%507)
      aiex.dma_free_task(%508)
      aiex.dma_free_task(%509)
      aiex.dma_free_task(%510)
      aiex.dma_free_task(%511)
      aiex.dma_free_task(%512)
      aiex.dma_free_task(%513)
      aiex.dma_free_task(%514)
      aiex.dma_free_task(%515)
      aiex.dma_free_task(%516)
      aiex.dma_free_task(%517)
      aiex.dma_free_task(%518)
      aiex.dma_free_task(%519)
      %540 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1575936 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%540)
      %541 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1584128 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%541)
      %542 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1592320 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%542)
      %543 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1600512 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%543)
      %544 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1608704 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%544)
      %545 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1616896 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%545)
      %546 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1625088 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%546)
      %547 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1633280 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%547)
      %548 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%548)
      %549 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%549)
      %550 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%550)
      %551 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%551)
      %552 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 11698176 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%552)
      %553 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12185600 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%553)
      %554 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 12673024 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%554)
      %555 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13160448 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%555)
      %556 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 13647872 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%556)
      %557 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14135296 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%557)
      %558 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 14622720 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%558)
      %559 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15110144 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%559)
      aiex.dma_await_task(%520)
      aiex.dma_await_task(%521)
      aiex.dma_await_task(%522)
      aiex.dma_await_task(%523)
      aiex.dma_await_task(%524)
      aiex.dma_await_task(%525)
      aiex.dma_await_task(%526)
      aiex.dma_await_task(%527)
      aiex.dma_free_task(%520)
      aiex.dma_free_task(%521)
      aiex.dma_free_task(%522)
      aiex.dma_free_task(%523)
      aiex.dma_free_task(%524)
      aiex.dma_free_task(%525)
      aiex.dma_free_task(%526)
      aiex.dma_free_task(%527)
      aiex.dma_free_task(%528)
      aiex.dma_free_task(%529)
      aiex.dma_free_task(%530)
      aiex.dma_free_task(%531)
      aiex.dma_free_task(%532)
      aiex.dma_free_task(%533)
      aiex.dma_free_task(%534)
      aiex.dma_free_task(%535)
      aiex.dma_free_task(%536)
      aiex.dma_free_task(%537)
      aiex.dma_free_task(%538)
      aiex.dma_free_task(%539)
      %560 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1576960 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%560)
      %561 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1585152 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%561)
      %562 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1593344 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%562)
      %563 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1601536 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%563)
      %564 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1609728 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%564)
      %565 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1617920 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%565)
      %566 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1626112 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%566)
      %567 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1634304 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%567)
      %568 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%568)
      %569 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%569)
      %570 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%570)
      %571 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%571)
      %572 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 15597568 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%572)
      %573 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16084992 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%573)
      %574 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 16572416 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%574)
      %575 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17059840 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%575)
      %576 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 17547264 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%576)
      %577 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18034688 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%577)
      %578 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 18522112 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%578)
      %579 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19009536 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%579)
      aiex.dma_await_task(%540)
      aiex.dma_await_task(%541)
      aiex.dma_await_task(%542)
      aiex.dma_await_task(%543)
      aiex.dma_await_task(%544)
      aiex.dma_await_task(%545)
      aiex.dma_await_task(%546)
      aiex.dma_await_task(%547)
      aiex.dma_free_task(%540)
      aiex.dma_free_task(%541)
      aiex.dma_free_task(%542)
      aiex.dma_free_task(%543)
      aiex.dma_free_task(%544)
      aiex.dma_free_task(%545)
      aiex.dma_free_task(%546)
      aiex.dma_free_task(%547)
      aiex.dma_free_task(%548)
      aiex.dma_free_task(%549)
      aiex.dma_free_task(%550)
      aiex.dma_free_task(%551)
      aiex.dma_free_task(%552)
      aiex.dma_free_task(%553)
      aiex.dma_free_task(%554)
      aiex.dma_free_task(%555)
      aiex.dma_free_task(%556)
      aiex.dma_free_task(%557)
      aiex.dma_free_task(%558)
      aiex.dma_free_task(%559)
      %580 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1577984 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%580)
      %581 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1586176 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%581)
      %582 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1594368 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%582)
      %583 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1602560 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%583)
      %584 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1610752 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%584)
      %585 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1618944 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%585)
      %586 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1627136 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%586)
      %587 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1635328 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%587)
      %588 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%588)
      %589 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%589)
      %590 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%590)
      %591 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%591)
      %592 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19496960 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%592)
      %593 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 19984384 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%593)
      %594 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20471808 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%594)
      %595 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 20959232 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%595)
      %596 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21446656 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%596)
      %597 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 21934080 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%597)
      %598 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22421504 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%598)
      %599 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 22908928 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%599)
      aiex.dma_await_task(%560)
      aiex.dma_await_task(%561)
      aiex.dma_await_task(%562)
      aiex.dma_await_task(%563)
      aiex.dma_await_task(%564)
      aiex.dma_await_task(%565)
      aiex.dma_await_task(%566)
      aiex.dma_await_task(%567)
      aiex.dma_free_task(%560)
      aiex.dma_free_task(%561)
      aiex.dma_free_task(%562)
      aiex.dma_free_task(%563)
      aiex.dma_free_task(%564)
      aiex.dma_free_task(%565)
      aiex.dma_free_task(%566)
      aiex.dma_free_task(%567)
      aiex.dma_free_task(%568)
      aiex.dma_free_task(%569)
      aiex.dma_free_task(%570)
      aiex.dma_free_task(%571)
      aiex.dma_free_task(%572)
      aiex.dma_free_task(%573)
      aiex.dma_free_task(%574)
      aiex.dma_free_task(%575)
      aiex.dma_free_task(%576)
      aiex.dma_free_task(%577)
      aiex.dma_free_task(%578)
      aiex.dma_free_task(%579)
      %600 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1579008 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%600)
      %601 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1587200 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%601)
      %602 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1595392 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%602)
      %603 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1603584 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%603)
      %604 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1611776 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%604)
      %605 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1619968 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%605)
      %606 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1628160 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%606)
      %607 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1636352 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%607)
      %608 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%608)
      %609 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%609)
      %610 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%610)
      %611 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%611)
      %612 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23396352 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%612)
      %613 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 23883776 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%613)
      %614 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24371200 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%614)
      %615 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 24858624 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%615)
      %616 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25346048 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%616)
      %617 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 25833472 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%617)
      %618 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26320896 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%618)
      %619 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 26808320 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%619)
      aiex.dma_await_task(%580)
      aiex.dma_await_task(%581)
      aiex.dma_await_task(%582)
      aiex.dma_await_task(%583)
      aiex.dma_await_task(%584)
      aiex.dma_await_task(%585)
      aiex.dma_await_task(%586)
      aiex.dma_await_task(%587)
      aiex.dma_free_task(%580)
      aiex.dma_free_task(%581)
      aiex.dma_free_task(%582)
      aiex.dma_free_task(%583)
      aiex.dma_free_task(%584)
      aiex.dma_free_task(%585)
      aiex.dma_free_task(%586)
      aiex.dma_free_task(%587)
      aiex.dma_free_task(%588)
      aiex.dma_free_task(%589)
      aiex.dma_free_task(%590)
      aiex.dma_free_task(%591)
      aiex.dma_free_task(%592)
      aiex.dma_free_task(%593)
      aiex.dma_free_task(%594)
      aiex.dma_free_task(%595)
      aiex.dma_free_task(%596)
      aiex.dma_free_task(%597)
      aiex.dma_free_task(%598)
      aiex.dma_free_task(%599)
      %620 = aiex.dma_configure_task_for @direct_y_host_0 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1580032 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%620)
      %621 = aiex.dma_configure_task_for @direct_y_host_1 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1588224 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%621)
      %622 = aiex.dma_configure_task_for @direct_y_host_2 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1596416 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%622)
      %623 = aiex.dma_configure_task_for @direct_y_host_3 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1604608 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%623)
      %624 = aiex.dma_configure_task_for @direct_y_host_4 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1612800 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%624)
      %625 = aiex.dma_configure_task_for @direct_y_host_5 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1620992 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%625)
      %626 = aiex.dma_configure_task_for @direct_y_host_6 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1629184 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%626)
      %627 = aiex.dma_configure_task_for @direct_y_host_7 {
        aie.dma_bd(%arg2 : memref<2097152xbf16> offset = 1637376 len = 8192 sizes = [1, 2, 8, 512] strides = [0, 512, 65536, 1])
        aie.end
      } {issue_token = true}
      aiex.dma_start_task(%627)
      %628 = aiex.dma_configure_task_for @direct_a_host_0 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 983040 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%628)
      %629 = aiex.dma_configure_task_for @direct_a_host_1 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1064960 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%629)
      %630 = aiex.dma_configure_task_for @direct_a_host_2 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1146880 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%630)
      %631 = aiex.dma_configure_task_for @direct_a_host_3 {
        aie.dma_bd(%arg0 : memref<1310720xbf16> offset = 1228800 len = 81920 sizes = [1, 80, 2, 512] strides = [0, 512, 40960, 1])
        aie.end
      }
      aiex.dma_start_task(%631)
      %632 = aiex.dma_configure_task_for @direct_w_host_0 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27295744 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%632)
      %633 = aiex.dma_configure_task_for @direct_w_host_1 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 27783168 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%633)
      %634 = aiex.dma_configure_task_for @direct_w_host_2 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28270592 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%634)
      %635 = aiex.dma_configure_task_for @direct_w_host_3 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 28758016 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%635)
      %636 = aiex.dma_configure_task_for @direct_w_host_4 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29245440 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%636)
      %637 = aiex.dma_configure_task_for @direct_w_host_5 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 29732864 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%637)
      %638 = aiex.dma_configure_task_for @direct_w_host_6 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30220288 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%638)
      %639 = aiex.dma_configure_task_for @direct_w_host_7 {
        aie.dma_bd(%arg1 : memref<31195136xui8> offset = 30707712 len = 87040 sizes = [1, 1, 1, 87040] strides = [0, 0, 0, 1])
        aie.end
      }
      aiex.dma_start_task(%639)
      aiex.dma_await_task(%600)
      aiex.dma_await_task(%601)
      aiex.dma_await_task(%602)
      aiex.dma_await_task(%603)
      aiex.dma_await_task(%604)
      aiex.dma_await_task(%605)
      aiex.dma_await_task(%606)
      aiex.dma_await_task(%607)
      aiex.dma_free_task(%600)
      aiex.dma_free_task(%601)
      aiex.dma_free_task(%602)
      aiex.dma_free_task(%603)
      aiex.dma_free_task(%604)
      aiex.dma_free_task(%605)
      aiex.dma_free_task(%606)
      aiex.dma_free_task(%607)
      aiex.dma_free_task(%608)
      aiex.dma_free_task(%609)
      aiex.dma_free_task(%610)
      aiex.dma_free_task(%611)
      aiex.dma_free_task(%612)
      aiex.dma_free_task(%613)
      aiex.dma_free_task(%614)
      aiex.dma_free_task(%615)
      aiex.dma_free_task(%616)
      aiex.dma_free_task(%617)
      aiex.dma_free_task(%618)
      aiex.dma_free_task(%619)
      aiex.dma_await_task(%620)
      aiex.dma_await_task(%621)
      aiex.dma_await_task(%622)
      aiex.dma_await_task(%623)
      aiex.dma_await_task(%624)
      aiex.dma_await_task(%625)
      aiex.dma_await_task(%626)
      aiex.dma_await_task(%627)
      aiex.dma_free_task(%620)
      aiex.dma_free_task(%621)
      aiex.dma_free_task(%622)
      aiex.dma_free_task(%623)
      aiex.dma_free_task(%624)
      aiex.dma_free_task(%625)
      aiex.dma_free_task(%626)
      aiex.dma_free_task(%627)
      aiex.dma_free_task(%628)
      aiex.dma_free_task(%629)
      aiex.dma_free_task(%630)
      aiex.dma_free_task(%631)
      aiex.dma_free_task(%632)
      aiex.dma_free_task(%633)
      aiex.dma_free_task(%634)
      aiex.dma_free_task(%635)
      aiex.dma_free_task(%636)
      aiex.dma_free_task(%637)
      aiex.dma_free_task(%638)
      aiex.dma_free_task(%639)
    }
  }
}
