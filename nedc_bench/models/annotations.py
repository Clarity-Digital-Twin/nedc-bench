"""
Data models for EEG event annotations
Matches CSV_BI format from NEDC v6.0.0
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventAnnotation(BaseModel):
    """Single annotation event matching CSV_BI format"""

    channel: Literal["TERM"] = "TERM"  # NEDC v6.0.0 uses TERM channel
    start_time: float = Field(ge=0, description="Start time in seconds")
    stop_time: float = Field(gt=0, description="Stop time in seconds")
    label: str = Field(description="Event label (e.g., 'seiz', 'bckg')")
    confidence: float = Field(ge=0, le=1, description="Confidence score")

    @property
    def duration(self) -> float:
        """Event duration in seconds"""
        return self.stop_time - self.start_time

    @field_validator("stop_time")
    @classmethod
    def validate_times(cls, v: float, info) -> float:
        """Ensure stop_time > start_time"""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError(f"stop_time ({v}) must be > start_time ({info.data['start_time']})")
        return v

    @classmethod
    def from_csv_bi_line(cls, line: str) -> EventAnnotation:
        """Parse from CSV_BI format line

        Format: channel,start_time,stop_time,label,confidence
        """
        parts = line.strip().split(",")
        if len(parts) != 5:
            raise ValueError(f"Invalid CSV_BI line: {line}")

        return cls(
            channel=parts[0],
            start_time=float(parts[1]),
            stop_time=float(parts[2]),
            label=parts[3],
            confidence=float(parts[4]),
        )


class AnnotationFile(BaseModel):
    """Complete annotation file matching CSV_BI structure"""

    version: str
    patient: str
    session: str
    events: list[EventAnnotation]
    duration: float = Field(description="Total file duration in seconds")

    @classmethod
    def from_csv_bi(cls, file_path: Path) -> AnnotationFile:
        """Parse CSV_BI format file

        Args:
            file_path: Path to CSV_BI file

        Returns:
            AnnotationFile with parsed events and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"CSV_BI file not found: {file_path}")

        metadata = {}
        events = []

        with open(file_path, encoding="utf-8") as f:  # noqa: PTH123
            for line in f:
                line = line.strip()  # noqa: PLW2901

                # Skip empty lines
                if not line:
                    continue

                # Parse metadata comments
                if line.startswith("#"):
                    match = re.match(r"#\s*(\w+)\s*=\s*(.+)", line)
                    if match:
                        key, value = match.groups()
                        metadata[key] = value.strip()
                    continue

                # Skip header line
                if line.startswith("channel,"):
                    continue

                # Parse event line
                try:
                    event = EventAnnotation.from_csv_bi_line(line)
                    events.append(event)
                except ValueError as e:
                    # Log but continue - some files may have malformed lines
                    print(f"Warning: Skipping malformed line in {file_path}: {e}")

        # Extract duration from metadata
        duration_str = metadata.get("duration", "0.0 secs")
        duration = float(duration_str.replace(" secs", ""))

        # Handle 'bname' as alias for 'patient' (NEDC uses both)
        patient = metadata.get("patient") or metadata.get("bname", "unknown")

        return cls(
            version=metadata.get("version", "unknown"),
            patient=patient,
            session=metadata.get("session", "unknown"),
            events=events,
            duration=duration,
        )
