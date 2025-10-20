# -*- coding: utf-8 -*-
# *******************************************************************************
# Copyright (c)
# School of Electrical, Computer and Energy Engineering, Arizona State University
# Department of Electrical and Computer Engineering, University of Minnesota
#
# PI: Prof.Yu(Kevin) Cao
# All rights reserved.
#
# This source code is for HISIM: Analytical Performance Modeling and Design Exploration
# of 2.5D/3D Heterogeneous Integration for AI Computing
#
# Copyright of the model is maintained by the developers, and the model is distributed under
# the terms of the Creative Commons Attribution-NonCommercial 4.0 International Public License
# http://creativecommons.org/licenses/by-nc/4.0/legalcode.
# The source code is free and you can redistribute and/or modify it
# by providing that the following conditions are met:
#
#  1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#  2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Developer list:
#   Zhenyu Wang     Email: zwang586@asu.edu
#   Pragnya Nalla   Email: nalla052@umn.edu
#   Jingbo Sun      Email: jsun127@asu.edu
#   Jennifer Zhou   Email:
# *******************************************************************************/
from pathlib import Path
from typing import Optional

from Module_AI_Map.util_chip.layout import ChipletLayout
from hisim_model import HiSimModel


def load_layout(path: Path, label: str) -> Optional[ChipletLayout]:
    """Load a layout JSON file if it exists."""
    try:
        layout = ChipletLayout.from_json(path)
    except FileNotFoundError:
        print(f"[WARN] 未找到 {label} 布局文件 {path}，将回退为均匀布局。\n")
        return None
    except ValueError as exc:
        print(f"[WARN] 无法解析 {label} 布局文件 {path}: {exc}。将回退为均匀布局。\n")
        return None
    else:
        print(f"使用 {label} 布局文件: {path}\n")
        return layout


def wait_for_next_case() -> None:
    print("")
    input("Press Enter to execute next test case")
    print("")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    layout_3d_path = base_dir / "Demos" / "heterogeneous_3d_layout.json"
    layout_2p5d_path = base_dir / "Demos" / "heterogeneous_2p5d_layout.json"

    hetero_layout_3d = load_layout(layout_3d_path, "3D/3.5D")
    hetero_layout_2p5d = load_layout(layout_2p5d_path, "2.5D")

    # Test Case 1
    print("Test Case 1: Running HISIM to obtain PPA")
    print("AI Network: ViT")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-9-100-2-2-3.5D")
    case1_kwargs = dict(
        chip_architect="M3_5D",
        xbar_size=1024,
        N_tile=100,
        N_pe=9,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="vit",
        thermal=False,
        N_stack=2,
    )
    if hetero_layout_3d is not None:
        case1_kwargs["chiplet_layout"] = hetero_layout_3d
    hisim = HiSimModel(**case1_kwargs)
    hisim.run_model()
    print(
        "Test case 1 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 2
    print("Test Case 2: Running HISIM to obtain PPA")
    print("AI Network: densenet121")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-64-2-2")
    case2_kwargs = dict(
        chip_architect="M3_5D",
        xbar_size=1024,
        N_tile=64,
        N_pe=36,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=False,
        N_stack=2,
    )
    if hetero_layout_3d is not None:
        case2_kwargs["chiplet_layout"] = hetero_layout_3d
    hisim = HiSimModel(**case2_kwargs)
    hisim.run_model()
    print(
        "Test case 2 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 3
    print("Test Case 3: Running HISIM to obtain PPA for different TSV pitches")
    print("AI Network: densenet121")
    print("HW configuration ( Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-81-2-1-3D")
    case3_kwargs = dict(
        chip_architect="M3D",
        xbar_size=1024,
        N_tile=81,
        N_pe=36,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=False,
        N_stack=1,
    )
    hisim = HiSimModel(**case3_kwargs)
    tsv_pitch = [2, 3, 4, 5, 10, 20]  # um
    for pitch in tsv_pitch:
        print("TSV_pitch:", pitch, "um")
        hisim.set_tsv_pitch(pitch)
        hisim.run_model()
    hisim.set_tsv_pitch(case3_kwargs["tsv_pitch"])
    print(
        "Test case 3 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 4
    print("Test Case 4: Running HISIM to obtain PPA for different NoC bandwidths")
    print("AI Network: densenet121")
    print("HW configuration ( Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-81-2-1-3D")
    case4_kwargs = dict(
        chip_architect="M3D",
        xbar_size=1024,
        N_tile=81,
        N_pe=36,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=False,
        N_stack=1,
    )
    hisim = HiSimModel(**case4_kwargs)
    noc_width = [i for i in range(1, 32, 5)]  # um
    for width in noc_width[1:]:
        print("number of links of 2D NoC:", width)
        hisim.set_W2d(width)
        hisim.run_model()
    hisim.set_W2d(case4_kwargs["W2d"])
    print(
        "Test case 4 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 5
    print("Test Case 5: Running HISIM to obtain PPA and thermal for different Ntier")
    print("AI Network: densenet121")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-169-Depends on input config-1")
    case5_kwargs = dict(
        chip_architect="M3D",
        xbar_size=1024,
        N_tile=169,
        N_pe=36,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=True,
        N_stack=1,
    )
    hisim = HiSimModel(**case5_kwargs)
    for tier in range(1, 4):
        print("number of tiers:", tier)
        hisim.set_N_tier(tier)
        hisim.run_model()
    print(
        "Test case 5 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 6
    print("Test Case 6: Running HISIM to obtain PPA and thermal")
    print("AI Network: densenet121")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-81-2-1-3D")
    case6_kwargs = dict(
        chip_architect="M3D",
        xbar_size=1024,
        N_tile=81,
        N_pe=36,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=True,
        N_stack=1,
    )
    hisim = HiSimModel(**case6_kwargs)
    hisim.run_model()
    print(
        "Test case 6 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 7
    print("Test Case 7: Running HISIM to obtain PPA and thermal")
    print("AI Network: ViT")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-9-169-2-1-3D")
    case7_kwargs = dict(
        chip_architect="M3D",
        xbar_size=1024,
        N_tile=169,
        N_pe=9,
        N_tier=2,
        freq_computing=1,
        fclk_noc=1,
        placement_method=5,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="vit",
        thermal=True,
        N_stack=1,
    )
    hisim = HiSimModel(**case7_kwargs)
    hisim.run_model()
    print(
        "Test case 7 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
    wait_for_next_case()

    # Test Case 8
    print("Test Case 8: Running HISIM to obtain PPA and thermal")
    print("AI Network: densenet121")
    print("HW configuration (Xbar-Npe-Ntile-Ntier-Nstack-chip_arch):1024-36-81-1-2-2.5D")
    case8_kwargs = dict(
        chip_architect="H2_5D",
        xbar_size=1024,
        N_tile=81,
        N_pe=36,
        N_tier=1,
        freq_computing=1,
        fclk_noc=1,
        placement_method=1,
        router_times_scale=1,
        percent_router=1,
        tsv_pitch=5,
        W2d=32,
        ai_model="densenet121",
        thermal=False,
        N_stack=2,
    )
    if hetero_layout_2p5d is not None:
        case8_kwargs["chiplet_layout"] = hetero_layout_2p5d
    hisim = HiSimModel(**case8_kwargs)
    hisim.run_model()
    print(
        "Test case 8 done. Please check Results/PPA.csv for PPA information and Results/tile_map.png for tile mapping information"
    )
    print("")
