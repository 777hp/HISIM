from __future__ import annotations

import math
import json
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


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

    def stack(self, stack_idx: int) -> Sequence[TierLayout]:
        return self._stacks[stack_idx]

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

    def stack_capacity(self, stack_idx: int) -> int:
        return sum(tier.capacity for tier in self.stack(stack_idx))

    def iter_tiers(self) -> Iterable[TierLayout]:
        for stack in self._stacks:
            for tier in stack:
                yield tier

    def stack_origin(self, stack_idx: int) -> Tuple[int, int]:
        stack = self.stack(stack_idx)
        min_row = min((tier.origin_row for tier in stack), default=0)
        min_col = min((tier.origin_col for tier in stack), default=0)
        return min_row, min_col

    def stack_shape(self, stack_idx: int) -> Tuple[int, int]:
        stack = self.stack(stack_idx)
        if not stack:
            return 0, 0

        min_row, min_col = self.stack_origin(stack_idx)
        max_row = max(tier.origin_row + tier.rows for tier in stack)
        max_col = max(tier.origin_col + tier.cols for tier in stack)
        return max_row - min_row, max_col - min_col

    def global_shape(self) -> Tuple[int, int]:
        """Return the bounding box (rows, cols) that encloses all tiers."""
        if not self._stacks:
            return 0, 0

        min_row = None
        min_col = None
        max_row = None
        max_col = None
        for stack in range(self.stack_count()):
            for tier in range(self.tier_count()):
                layout = self.tier(stack, tier)
                tier_min_row = layout.origin_row
                tier_min_col = layout.origin_col
                tier_max_row = layout.origin_row + layout.rows
                tier_max_col = layout.origin_col + layout.cols
                min_row = tier_min_row if min_row is None else min(min_row, tier_min_row)
                min_col = tier_min_col if min_col is None else min(min_col, tier_min_col)
                max_row = tier_max_row if max_row is None else max(max_row, tier_max_row)
                max_col = tier_max_col if max_col is None else max(max_col, tier_max_col)

        assert min_row is not None and min_col is not None and max_row is not None and max_col is not None
        return max_row - min_row, max_col - min_col

    def to_dict(self) -> Dict[str, object]:
        """Export the layout as a serialisable dictionary."""
        stacks: List[List[Mapping[str, int]]] = []
        for stack in self._stacks:
            stack_repr: List[Mapping[str, int]] = []
            for tier in stack:
                stack_repr.append(
                    {
                        "rows": tier.rows,
                        "cols": tier.cols,
                        "origin_row": tier.origin_row,
                        "origin_col": tier.origin_col,
                    }
                )
            stacks.append(stack_repr)
        return {"stacks": stacks}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ChipletLayout":
        """Create a layout from a nested mapping structure.

        The expected format is ``{"stacks": [[{"rows": int, "cols": int,
        "origin_row": int, "origin_col": int}, ...], ...]}`` which aligns with
        the JSON exported by :meth:`to_dict` and can be easily produced by
        external tools such as TAP.
        """
        stacks_data = data.get("stacks")
        if not isinstance(stacks_data, Sequence):
            raise ValueError("ChipletLayout dict must contain a 'stacks' sequence")

        stacks: List[List[TierLayout]] = []
        for stack in stacks_data:
            if not isinstance(stack, Sequence):
                raise ValueError("Each stack entry must be a sequence of tiers")
            parsed_stack: List[TierLayout] = []
            for tier in stack:
                if not isinstance(tier, Mapping):
                    raise ValueError("Each tier entry must be a mapping")
                try:
                    rows = int(tier["rows"])  # type: ignore[index]
                    cols = int(tier["cols"])  # type: ignore[index]
                except KeyError as exc:  # pragma: no cover - defensive
                    raise ValueError("Tier description missing rows/cols") from exc
                origin_row = int(tier.get("origin_row", 0))  # type: ignore[arg-type]
                origin_col = int(tier.get("origin_col", 0))  # type: ignore[arg-type]
                parsed_stack.append(
                    TierLayout(
                        rows=rows,
                        cols=cols,
                        origin_row=origin_row,
                        origin_col=origin_col,
                    )
                )
            stacks.append(parsed_stack)

        return cls(stacks)

    @classmethod
    def from_json(
        cls, path: "PathLike[str] | str", encoding: str = "utf-8"
    ) -> "ChipletLayout":
        """Load a layout description from a JSON file."""
        with open(Path(path), "r", encoding=encoding) as fh:
            data = json.load(fh)
        return cls.from_dict(data)

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

