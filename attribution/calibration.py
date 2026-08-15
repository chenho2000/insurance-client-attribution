"""Binned calibration layer: learns a reliability map from past outcomes.

Collects (predicted probability, realized 0/1) pairs across periods and
builds a monotone binned adjustment. Applied to the current period's
decision probabilities; the map is deterministic and fully inspectable,
consistent with the auditability narrative (no learned black box).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

BINS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.000001)
MIN_BIN_COUNT = 5


class BinnedCalibrator:
    def __init__(self) -> None:
        self.pairs: List[Tuple[float, float]] = []

    def add(self, predicted: float, realized: float) -> None:
        self.pairs.append((min(max(float(predicted), 0.0), 1.0), float(realized)))

    def _table(self) -> Optional[List[Tuple[float, float]]]:
        """(bin_center, empirical_rate) for bins with enough support."""
        if len(self.pairs) < 2 * MIN_BIN_COUNT:
            return None
        table: List[Tuple[float, float]] = []
        for lo, hi in zip(BINS, BINS[1:]):
            bucket = [r for p, r in self.pairs if lo <= p < hi]
            if len(bucket) >= MIN_BIN_COUNT:
                table.append(((lo + hi) / 2, sum(bucket) / len(bucket)))
        return table if len(table) >= 2 else None

    def calibrate(self, predicted: float) -> float:
        table = self._table()
        if table is None:
            return predicted  # insufficient history: pass through
        p = min(max(predicted, 0.0), 1.0)
        if p <= table[0][0]:
            return table[0][1]
        if p >= table[-1][0]:
            return table[-1][1]
        for (x0, y0), (x1, y1) in zip(table, table[1:]):
            if x0 <= p <= x1:
                w = (p - x0) / (x1 - x0)
                return y0 + w * (y1 - y0)
        return p

    @staticmethod
    def ece(pairs: Sequence[Tuple[float, float]]) -> Optional[float]:
        """Expected calibration error over the shared bin grid."""
        if not pairs:
            return None
        total = len(pairs)
        e = 0.0
        for lo, hi in zip(BINS, BINS[1:]):
            bucket = [(p, r) for p, r in pairs if lo <= p < hi]
            if bucket:
                mp = sum(p for p, _ in bucket) / len(bucket)
                mr = sum(r for _, r in bucket) / len(bucket)
                e += len(bucket) / total * abs(mp - mr)
        return e

    def summary(self) -> Dict[str, Any]:
        return {"pairs": len(self.pairs), "table": self._table()}
