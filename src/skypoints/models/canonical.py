"""
Canonical data models for member profiles, redemptions, and raw landing audits.
"""
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class ValidationStatus(str, Enum):
    """Status indicating record data quality."""
    VALID = "VALID"
    WARNING = "WARNING"
    QUARANTINE = "QUARANTINE"


class RawRecord(BaseModel):
    """
    Bronze Layer: Raw payload representation capturing complete audit lineage.
    """
    model_config = ConfigDict(from_attributes=True)

    source_system: str
    source_file_name: str
    source_file_timestamp: datetime
    source_row_number: int
    raw_payload: str
    ingested_at: datetime = Field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database insertion."""
        return self.model_dump()


class MemberRecord(BaseModel):
    """
    Silver/Gold Layer: Canonical representation of an airline loyalty member.
    """
    model_config = ConfigDict(from_attributes=True)

    member_id: str = Field(description="Authoritative global member key (preserves leading zeros)")
    member_name: str = Field(description="Cleaned member full name")
    enrollment_date: Optional[date] = None
    last_flight_date: Optional[date] = None
    tier_code: Optional[str] = None
    agent_name: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    post_code: Optional[str] = None
    dob: Optional[date] = None
    is_active: str = Field(default="A", description="'A' for active, 'I' for inactive / moved")
    age: Optional[int] = Field(default=None, description="Derived completed years from DOB")
    stale_member: Optional[bool] = Field(default=None, description="True if flight date > 90 days ago")

    # Audit lineage attributes
    source_system: str
    source_file_name: str
    source_file_timestamp: datetime
    source_row_number: int
    ingested_at: datetime = Field(default_factory=utc_now)
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_reason: Optional[str] = None

    @field_validator("member_id", mode="before")
    @classmethod
    def ensure_string_id(cls, v: Any) -> str:
        """Ensure member_id preserves leading zeros as string."""
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("member_name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> str:
        """Strip extra whitespace from name."""
        if v is None:
            return ""
        return str(v).strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database insertion."""
        data = self.model_dump()
        data["validation_status"] = self.validation_status.value
        return data


class RedemptionRecord(BaseModel):
    """
    Gold Layer: Canonical representation of a loyalty redemption transaction.
    """
    model_config = ConfigDict(from_attributes=True)

    txn_id: str = Field(description="Unique redemption transaction identifier")
    member_id: str = Field(description="Foreign key referencing member_id")
    feed_date: Optional[date] = None
    txn_date: Optional[date] = None
    partner: str = Field(description="Airline redemption partner name")
    miles_redeemed: int = Field(description="Miles deducted for redemption")
    status: str = Field(description="Transaction status (e.g. COMPLETED, PENDING)")

    # Audit lineage attributes
    source_file_name: str
    source_file_timestamp: datetime
    ingested_at: datetime = Field(default_factory=utc_now)
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_reason: Optional[str] = None

    @field_validator("txn_id", "member_id", mode="before")
    @classmethod
    def ensure_string_keys(cls, v: Any) -> str:
        """Ensure identifiers preserve exact string values."""
        if v is None:
            return ""
        return str(v).strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database insertion."""
        data = self.model_dump()
        data["validation_status"] = self.validation_status.value
        return data
