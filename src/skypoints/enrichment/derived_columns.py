"""
Enrichment engine for calculating business derived columns:
- Completed years of Age from DOB
- 90-day Stale Member loyalty flag
"""
from datetime import date, datetime, timezone
from typing import Optional, List
from skypoints.models.canonical import MemberRecord


def calculate_age(dob: Optional[date], as_of_date: Optional[date] = None) -> Optional[int]:
    """
    Calculate completed years of age from Date of Birth relative to an as_of_date.
    
    Evaluates exact birthday anniversaries, handling leap year births cleanly.
    Returns None if DOB is missing or in the future.
    """
    if dob is None:
        return None

    if as_of_date is None:
        as_of_date = date.today()

    if dob > as_of_date:
        return None

    # Exact birthday calculation: subtract 1 if current date is before birthday in current year
    has_had_birthday_this_year = (as_of_date.month, as_of_date.day) >= (dob.month, dob.day)
    age = as_of_date.year - dob.year - (0 if has_had_birthday_this_year else 1)
    return max(0, age)


def calculate_stale_member(
    last_flight_date: Optional[date],
    as_of_date: Optional[date] = None,
    threshold_days: int = 90,
) -> Optional[bool]:
    """
    Calculate the Stale Member status:
    - TRUE if days since last flight > 90 days.
    - FALSE if days since last flight <= 90 days (exactly 90 days is NOT stale).
    - None if last_flight_date is missing / unknown.
    """
    if last_flight_date is None:
        return None

    if as_of_date is None:
        as_of_date = date.today()

    days_since_flight = (as_of_date - last_flight_date).days
    return days_since_flight > threshold_days


def enrich_member_record(
    record: MemberRecord,
    as_of_date: Optional[date] = None,
    threshold_days: int = 90,
) -> MemberRecord:
    """
    Enrich a single MemberRecord with derived 'age' and 'stale_member' values.
    Returns the enriched record.
    """
    if as_of_date is None:
        as_of_date = date.today()

    record.age = calculate_age(record.dob, as_of_date=as_of_date)
    record.stale_member = calculate_stale_member(
        record.last_flight_date, as_of_date=as_of_date, threshold_days=threshold_days
    )
    return record


def enrich_member_records(
    records: List[MemberRecord],
    as_of_date: Optional[date] = None,
    threshold_days: int = 90,
) -> List[MemberRecord]:
    """
    Enrich a batch of MemberRecords with derived columns.
    """
    if as_of_date is None:
        as_of_date = date.today()

    for record in records:
        enrich_member_record(record, as_of_date=as_of_date, threshold_days=threshold_days)
    return records


# SQL snippets for database-native transformations in DuckDB
def get_duckdb_age_expression(as_of_date_str: str = "CURRENT_DATE") -> str:
    """Return DuckDB SQL expression to derive completed years of age."""
    return f"""
        CASE
            WHEN dob IS NULL THEN NULL
            WHEN dob > {as_of_date_str} THEN NULL
            ELSE
                date_diff('year', dob, {as_of_date_str}) -
                CASE
                    WHEN (month({as_of_date_str}), day({as_of_date_str})) < (month(dob), day(dob)) THEN 1
                    ELSE 0
                END
        END
    """


def get_duckdb_stale_expression(as_of_date_str: str = "CURRENT_DATE", threshold_days: int = 90) -> str:
    """Return DuckDB SQL expression to derive stale_member boolean."""
    return f"""
        CASE
            WHEN last_flight_date IS NULL THEN NULL
            ELSE (date_diff('day', last_flight_date, {as_of_date_str}) > {threshold_days})
        END
    """
