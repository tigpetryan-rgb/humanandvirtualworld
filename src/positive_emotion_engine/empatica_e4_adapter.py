from __future__ import annotations

import csv
import io
import math
from typing import Any

from .acquisition_quality import AcquisitionContractError


def _rows(text: str) -> list[list[str]]:
    rows = []
    for row in csv.reader(io.StringIO(text)):
        cleaned = [cell.strip() for cell in row]
        if any(cleaned):
            rows.append(cleaned)
    return rows


def parse_eda_csv(text: str, *, max_duration_s: float | None = None) -> dict[str, Any]:
    rows = _rows(text)
    if len(rows) < 3:
        raise AcquisitionContractError("EDA.csv is too short")
    start_epoch_s = float(rows[0][0])
    hz = float(rows[1][0])
    if not math.isfinite(start_epoch_s) or not math.isfinite(hz) or hz <= 0:
        raise AcquisitionContractError("invalid EDA metadata")
    samples = []
    for index, row in enumerate(rows[2:]):
        t_s = index / hz
        if max_duration_s is not None and t_s > max_duration_s:
            break
        value = float(row[0])
        samples.append({"seq": index, "relative_time_ms": round(t_s * 1000.0, 6), "value": value})
    if not samples:
        raise AcquisitionContractError("EDA.csv has no usable samples")
    return {"start_epoch_s": start_epoch_s, "nominal_hz": hz, "samples": samples}


def parse_ibi_csv(text: str, *, max_duration_s: float | None = None) -> dict[str, Any]:
    rows = _rows(text)
    if len(rows) < 2:
        raise AcquisitionContractError("IBI.csv is too short")
    start_epoch_s = float(rows[0][0])
    if not math.isfinite(start_epoch_s):
        raise AcquisitionContractError("invalid IBI start time")
    samples = []
    for row in rows[1:]:
        if len(row) < 2 or not row[0] or not row[1]:
            continue
        offset_s = float(row[0])
        ibi_s = float(row[1])
        if not math.isfinite(offset_s) or not math.isfinite(ibi_s):
            raise AcquisitionContractError("invalid IBI sample")
        if max_duration_s is not None and offset_s > max_duration_s:
            break
        samples.append({
            "seq": len(samples),
            "relative_time_ms": round(offset_s * 1000.0, 6),
            "value": round(ibi_s * 1000.0, 6),
        })
    if not samples:
        raise AcquisitionContractError("IBI.csv has no usable samples")
    return {"start_epoch_s": start_epoch_s, "samples": samples}


def build_recording_from_empatica(
    eda_text: str,
    ibi_text: str,
    *,
    session_id: str,
    data_class: str = "deidentified_recorded",
    max_duration_s: float | None = 300.0,
) -> dict[str, Any]:
    eda = parse_eda_csv(eda_text, max_duration_s=max_duration_s)
    ibi = parse_ibi_csv(ibi_text, max_duration_s=max_duration_s)
    origin_epoch_s = min(eda["start_epoch_s"], ibi["start_epoch_s"])

    def absolute_relative(start_epoch_s: float, relative_ms: float) -> float:
        return round((start_epoch_s - origin_epoch_s) * 1000.0 + relative_ms, 6)

    eda_samples = [
        {
            "seq": sample["seq"],
            "source_time_ms": absolute_relative(eda["start_epoch_s"], sample["relative_time_ms"]),
            "value": sample["value"],
        }
        for sample in eda["samples"]
    ]
    ibi_samples = [
        {
            "seq": sample["seq"],
            "source_time_ms": absolute_relative(ibi["start_epoch_s"], sample["relative_time_ms"]),
            "value": sample["value"],
        }
        for sample in ibi["samples"]
    ]

    return {
        "schema_version": "2.0.0",
        "session_id": session_id,
        "data_class": data_class,
        "channels": [
            {
                "name": "eda_us",
                "unit": "uS",
                "sampling_mode": "regular",
                "nominal_hz": eda["nominal_hz"],
                "clock": {"offset_ms": 0.0, "drift_ppm": 0.0},
                "samples": eda_samples,
            },
            {
                "name": "heart_ibi_ms",
                "unit": "ms",
                "sampling_mode": "event",
                "nominal_hz": None,
                "clock": {"offset_ms": 0.0, "drift_ppm": 0.0},
                "samples": ibi_samples,
            },
        ],
    }
