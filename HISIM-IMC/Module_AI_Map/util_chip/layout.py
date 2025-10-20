from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class TierLayout:
    """Describes the tile grid of a single tier/chiplet."""

    rows: int
    cols: int
    origin_row: int = 0
    origin_col: int = 0

    def __post_init__(self) -> None:  # type: ignore[override]
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("rows and cols must be positive")

    @property
    def capacity(self) -> int:
        return self.rows * self.cols


class ChipletLayout:
    """Stores the layout description for all stacks and tiers."""

    def __init__(self, stacks: Sequence[Sequence[TierLayout]]):
        if not stacks:
            raise ValueError("ChipletLayout requires at least one stack")
        if not all(stack for stack in stacks):
            raise ValueError("Each stack must contain at least one tier")

        # Normalize to lists to allow index access
        self._stacks: List[List[TierLayout]] = [list(stack) for stack in stacks]

        tier_count = len(self._stacks[0])
        for stack in self._stacks:
            if len(stack) != tier_count:
                raise ValueError("All stacks must expose the same tier count")

    @classmethod
    def uniform(
        cls, num_stacks: int, num_tiers: int, tiles_per_tier: int
    ) -> "ChipletLayout":
        if num_stacks <= 0 or num_tiers <= 0:
            raise ValueError("num_stacks and num_tiers must be positive")
        if tiles_per_tier <= 0:
            raise ValueError("tiles_per_tier must be positive")

        rows = int(math.ceil(math.sqrt(tiles_per_tier)))
        cols = int(math.ceil(tiles_per_tier / rows))

        tier = TierLayout(rows=rows, cols=cols)
        stacks: List[List[TierLayout]] = [
            [tier for _ in range(num_tiers)] for _ in range(num_stacks)
        ]
        return cls(stacks)

    def stack_count(self) -> int:
        return len(self._stacks)

    def tier_count(self) -> int:
        return len(self._stacks[0])

    def tier(self, stack_idx: int, tier_idx: int) -> TierLayout:
        return self._stacks[stack_idx][tier_idx]

    def tier_capacity(self, stack_idx: int, tier_idx: int) -> int:
        return self.tier(stack_idx, tier_idx).capacity

    def tier_shape(self, stack_idx: int, tier_idx: int) -> Tuple[int, int]:
        tier = self.tier(stack_idx, tier_idx)
        return tier.rows, tier.cols

    def tier_origin(self, stack_idx: int, tier_idx: int) -> Tuple[int, int]:
        tier = self.tier(stack_idx, tier_idx)
        return tier.origin_row, tier.origin_col

    def max_capacity(self) -> int:
        return max(tier.capacity for tier in self.iter_tiers())

    def iter_tiers(self) -> Iterable[TierLayout]:
        for stack in self._stacks:
            for tier in stack:
                yield tier

    def global_shape(self) -> Tuple[int, int]:
        max_row = 0
        max_col = 0
        for stack in range(self.stack_count()):
            for tier in range(self.tier_count()):
                layout = self.tier(stack, tier)
                max_row = max(max_row, layout.origin_row + layout.rows)
                max_col = max(max_col, layout.origin_col + layout.cols)
        return max_row, max_col

    def position_from_index(
        self,
        stack_idx: int,
        tier_idx: int,
        tile_index: int,
        serpentine: bool,
        mirror: bool,
    ) -> Tuple[int, int]:
        layout = self.tier(stack_idx, tier_idx)
        if tile_index < 0 or tile_index >= layout.capacity:
            raise IndexError("Tile index out of range for tier")

        row = tile_index // layout.cols
        col = tile_index % layout.cols

        if serpentine and row % 2 == 1:
            col = layout.cols - col - 1
        if mirror:
            row = layout.rows - row - 1
            col = layout.cols - col - 1

        origin_row, origin_col = layout.origin_row, layout.origin_col
        return origin_row + row, origin_col + col

