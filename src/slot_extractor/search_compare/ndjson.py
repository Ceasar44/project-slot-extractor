"""Strict JSON framing for search trace streams and exports."""

import json
import math


def finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: finite_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite_json(v) for v in value]
    return value


def encode_event(request_id, side, seq, kind, payload, comparable):
    return (
        json.dumps(
            finite_json(
                {
                    "request_id": request_id,
                    "side": side,
                    "seq": seq,
                    "type": kind,
                    "payload": payload,
                    "comparable": comparable,
                }
            ),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
