#!/usr/bin/env python3
# ssism_v14_baydin.py
"""
SS'ISM V14 — Mahārbote / Baydin Conversion Engine (Production)
Author : U Ingar SOE (for SS'ISM V14)
Purpose: Convert English date/time -> Burmese Baydin (Mahārbote) day & sign
         using SS'ISM conventions:
           - Baydin day starts at 06:00 local Baydin time (default Asia/Yangon UTC+6:30)
           - Wednesday is split AM/PM (returns different Mahārbote for AM vs PM)
           - Immutable Data Lock (SΣ) and Paññā checksum lock for integrity
Notes:
  - This module is defensive-only: no network calls, no external APIs.
  - Keep the canonical engine file in a secure repository.
"""

from __future__ import annotations
import datetime
import hashlib
import json
from typing import Tuple, Optional, Dict

# Defaults
DEFAULT_TZ_OFFSET_MINUTES = 6 * 60 + 30  # Myanmar Standard Time (UTC+6:30)
BAYDIN_DAY_START_HOUR = 6  # 06:00 local time is the Baydin day boundary

# -------------------------
# Mahārbote Mapping (English -> Baydin Sign)
# -------------------------
# Note: For Wednesday we return slot-aware labels (AM/PM) because Baydin splits Wednesday.
MAHARBOTE_MAP = {
    "Monday": "Tiger",
    "Tuesday": "Lion (Sīha)",
    # Wednesday handled as special-case (AM/PM)
    "Thursday": "Rat",
    "Friday": "Guinea Pig",
    "Saturday": "Dragon",
    "Sunday": "Garuda"
}

WEDNESDAY_AM_SIGN = "Tusked Elephant (Wednesday AM)"
WEDNESDAY_PM_SIGN = "Elephant (Wednesday PM)"

# Burmese translations (simple, for labels; you may expand if desired)
BURMESE_DAY_MAP = {
    "Monday": "တနင်္လာ",
    "Tuesday": "အင်္ဂါ",
    "Wednesday": "ဗုဒ္ဓဟူး",
    "Thursday": "ကြာသပတေး",
    "Friday": "သောကြာ",
    "Saturday": "စနေနေ့",
    "Sunday": "တနင်္ဂနွေ"
}

# -------------------------
# Utility helpers
# -------------------------


def _tz_offset_to_timedelta(offset_minutes: int) -> datetime.timedelta:
    return datetime.timedelta(minutes=int(offset_minutes))


def _ensure_int(value: Optional[int], default: int = 0) -> int:
    return int(value) if value is not None else default


# -------------------------
# Core conversion & locks
# -------------------------


def _apply_baydin_day_boundary(dt: datetime.datetime, day_start_hour: int = BAYDIN_DAY_START_HOUR) -> datetime.datetime:
    """
    If the local datetime is before Baydin day boundary (e.g., before 06:00),
    subtract one day so the Baydin day corresponds to the previous Gregorian day.
    Returns an adjusted datetime representing the Baydin day/time.
    """
    if dt.hour < day_start_hour:
        return dt - datetime.timedelta(days=1)
    return dt


def _maharbote_sign_from_weekday(weekday_name: str, hour_local: int) -> str:
    """
    Return the Mahārbote sign given English weekday name and local hour.
    Handles Wednesday AM/PM split.
    """
    if weekday_name == "Wednesday":
        # Wednesday split: AM/PM decision. We choose noon (12:00) as the split.
        if hour_local < 12:
            return WEDNESDAY_AM_SIGN
        else:
            return WEDNESDAY_PM_SIGN
    return MAHARBOTE_MAP.get(weekday_name, "Unknown")


def _iso_lock_string(day_name: str, sign: str, baydin_dt: datetime.datetime) -> str:
    """
    Create a canonical ISO lock string for immutability and hashing.
    """
    # We output baydin_dt in ISO format without microseconds
    iso_dt = baydin_dt.replace(microsecond=0).isoformat(sep=' ')
    lock_obj = {
        "baydin_day": day_name,
        "maharbote_sign": sign,
        "baydin_datetime": iso_dt
    }
    # Sorted keys ensure canonical output for hashing
    return json.dumps(lock_obj, sort_keys=True, ensure_ascii=False)


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def create_immutable_lock(year: int, month: int, day: int,
                          hour: Optional[int] = 12, minute: Optional[int] = 0,
                          tz_offset_minutes: int = DEFAULT_TZ_OFFSET_MINUTES) -> Dict[str, str]:
    """
    Create the SS'ISM Immutable Data Lock (SΣ) and a Paññā checksum.

    Returns a dictionary:
      {
        "baydin_day": "Tuesday",
        "maharbote_sign": "Lion (Sīha)",
        "baydin_datetime": "1978-02-07 14:30",
        "s_sigma_lock": "<sha256 hex>",
        "panna_checksum": "<sha256 hex of lock+salt>"
      }

    The paññā checksum adds a small salt derived from canonical fields to help detect tampering.
    """
    # Validate inputs and construct a timezone-aware datetime using offset (no tz library required)
    hour = _ensure_int(hour, 12)
    minute = _ensure_int(minute, 0)

    try:
        # Create a naive datetime first
        input_dt = datetime.datetime(year, month, day, hour, minute)
    except ValueError as e:
        raise ValueError(f"Invalid date/time input: {e}")

    # Apply timezone offset (minutes offset from UTC)
    tz_delta = _tz_offset_to_timedelta(tz_offset_minutes)
    # Interpret input as local (tz-aware simulated): represent as UTC equivalent
    # For our purpose we treat operations in local timezone; baydin logic uses local times.
    local_dt = input_dt  # we consider input already in local time (preferred)
    # Adjust for Baydin day start
    baydin_dt = _apply_baydin_day_boundary(local_dt, BAYDIN_DAY_START_HOUR)
    day_name = baydin_dt.strftime("%A")  # English weekday name
    baydin_hour = baydin_dt.hour

    sign = _maharbote_sign_from_weekday(day_name, baydin_hour)

    # Build canonical lock string
    lock_string = _iso_lock_string(day_name, sign, baydin_dt)
    s_sigma = _sha256_hex(lock_string)

    # Paññā checksum: incorporate a small deterministic salt to improve tamper detection
    # Salt = first 8 chars of SΣ reversed + date
    salt = (s_sigma[:8][::-1] + baydin_dt.strftime("%Y%m%d"))[:24]
    panna_source = lock_string + "|" + salt
    panna_checksum = _sha256_hex(panna_source)

    return {
        "baydin_day": day_name,
        "maharbote_sign": sign,
        "baydin_datetime": baydin_dt.replace(microsecond=0).isoformat(sep=' '),
        "s_sigma_lock": s_sigma,
        "panna_checksum": panna_checksum
    }


def verify_immutable_lock(lock_obj: Dict[str, str]) -> Tuple[bool, str]:
    """
    Verify a lock produced by create_immutable_lock. Returns (is_valid, message).
    """
    try:
        day_name = lock_obj["baydin_day"]
        sign = lock_obj["maharbote_sign"]
        baydin_datetime_str = lock_obj["baydin_datetime"]
        s_sigma = lock_obj["s_sigma_lock"]
        panna_checksum = lock_obj["panna_checksum"]
    except KeyError:
        return False, "Malformed lock object: missing keys."

    # Recompute SΣ from the canonical fields
    canonical = json.dumps({
        "baydin_day": day_name,
        "maharbote_sign": sign,
        "baydin_datetime": baydin_datetime_str
    }, sort_keys=True, ensure_ascii=False)

    recomputed_s_sigma = _sha256_hex(canonical)
    if recomputed_s_sigma != s_sigma:
        return False, "SΣ mismatch (immutable lock altered)."

    # Recompute Paññā salt and checksum
    salt = (s_sigma[:8][::-1] + baydin_datetime_str.replace('-', '')[:8])[:24]
    recomputed_panna = _sha256_hex(canonical + "|" + salt)
    if recomputed_panna != panna_checksum:
        return False, "Paññā checksum mismatch (tamper suspected)."

    return True, "Locks verified successfully."


# -------------------------
# Convenience / CLI utilities
# -------------------------


def parse_date_input(date_input: str) -> Tuple[int, int, int, int, int]:
    """
    Parse flexible date inputs:
      - 'YYYY-MM-DD' -> returns year,month,day, hour=12, minute=0
      - 'YYYY-MM-DD HH:MM' -> parse full
      - 'YYYY/MM/DD' accepted
    Raises ValueError on parse failure.
    """
    date_input = date_input.strip()
    # Try full datetime with space
    if " " in date_input:
        date_part, time_part = date_input.split(" ", 1)
    else:
        date_part, time_part = date_input, "12:00"

    # Normalize separators
    date_part = date_part.replace("/", "-")
    parts = date_part.split("-")
    if len(parts) != 3:
        raise ValueError("Date must be in YYYY-MM-DD or YYYY/MM/DD format.")

    year, month, day = map(int, parts)
    hour, minute = map(int, time_part.split(":"))
    return year, month, day, hour, minute


# -------------------------
# Example Tests (Sarah Nichols and other cases)
# -------------------------
def _run_example_tests() -> None:
    print("=== SS'ISM V14 Baydin Engine — Example Tests ===\n")

    tests = [

        ("Test Case A", 1978, 2, 7, 12, 0),     

    for label, y, m, d, h, mi in tests:
        print(f"--- {label} ---")
        lock = create_immutable_lock(y, m, d, h, mi)
        print(f"Baydin Day: {lock['baydin_day']}")
        print(f"Mahārbote Sign: {lock['maharbote_sign']}")
        print(f"Baydin DateTime (local canonical): {lock['baydin_datetime']}")
        print(f"SΣ Lock: {lock['s_sigma_lock']}")
        print(f"Paññā Checksum: {lock['panna_checksum']}")
        ok, msg = verify_immutable_lock(lock)
        print(f"Verification: {ok} — {msg}\n")


# -------------------------
# Public API (for other modules)
# -------------------------


__all__ = [
    "create_immutable_lock",
    "verify_immutable_lock",
    "parse_date_input",
    "create_immutable_lock",
]


# -------------------------
# CLI Execution
# -------------------------
if __name__ == "__main__":
    print("SS'ISM V14 — Mahārbote (Baydin) Conversion Engine")
    print("Default Baydin day boundary: 06:00 local time (Myanmar standard UTC+6:30 assumed).")
    print()

    # Run embedded example tests
    _run_example_tests()

    # Example to parse a user input (uncomment to use interactively)
    # user_input = input("Enter date (YYYY-MM-DD or YYYY-MM-DD HH:MM): ").strip()
    # try:
    #     y, mo, d, hr, mn = parse_date_input(user_input)
    #     lock = create_immutable_lock(y, mo, d, hr, mn)
    #     print("Result:", lock)
    # except ValueError as e:
    #     print("Input error:", e)
