"""Public result types for the compile pipeline."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Format(str, Enum):
    """Supported output formats."""

    PDF = "pdf"
    PNG = "png"
    SVG = "svg"

    @property
    def extension(self) -> str:
        return f".{self.value}"

    @property
    def media_type(self) -> str:
        return {
            Format.PDF: "application/pdf",
            Format.PNG: "image/png",
            Format.SVG: "image/svg+xml",
        }[self]


@dataclass(slots=True)
class CompileResult:
    """Structured result of compiling a single TeX file."""

    artifacts: dict[Format, Path] = field(default_factory=dict)
    page_counts: dict[Format, int] = field(default_factory=dict)
    detected_packages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        """Primary artifact path: PDF when present, else the first artifact."""
        if Format.PDF in self.artifacts:
            return self.artifacts[Format.PDF]
        if self.artifacts:
            return next(iter(self.artifacts.values()))
        raise ValueError("CompileResult has no artifacts")

    def to_manifest(self) -> dict[str, Any]:
        """JSON-friendly manifest of the metadata fields (artifacts excluded)."""
        return {
            "page_counts": {fmt.value: count for fmt, count in self.page_counts.items()},
            "detected_packages": list(self.detected_packages),
            "warnings": list(self.warnings),
            "timings": dict(self.timings),
        }


def parse_formats(value: str | Iterable[str | Format] | None) -> set[Format]:
    """Parse formats from comma-separated string, iterable, or None.

    Empty/None input returns an empty set so callers can layer in defaults.
    Unknown tokens raise ValueError.
    """
    if value is None:
        return set()

    if isinstance(value, str):
        tokens = [tok.strip() for tok in value.split(",") if tok.strip()]
    else:
        tokens = list(value)

    result: set[Format] = set()
    for tok in tokens:
        if isinstance(tok, Format):
            result.add(tok)
            continue
        try:
            result.add(Format(tok.lower()))
        except ValueError as e:
            valid = ", ".join(f.value for f in Format)
            raise ValueError(f"Unknown format '{tok}'. Valid formats: {valid}") from e
    return result


def resolve_formats(
    formats: str | Iterable[str | Format] | None = None,
    *,
    png: bool = False,
    svg: bool = False,
    strict_alias_combo: bool = False,
) -> set[Format]:
    """Resolve a request to a non-empty set of formats.

    Precedence: an explicit `formats` value wins; otherwise the legacy
    `png` / `svg` boolean aliases are folded in. If neither is supplied,
    defaults to {PDF}.

    `strict_alias_combo=True` reproduces the legacy CLI/API guard where
    passing both `png=True` and `svg=True` (without explicit `formats`) is
    rejected; callers that prefer the silent multi-format behaviour can
    leave the default. Raises ValueError when the guard fires.
    """
    parsed = parse_formats(formats)
    if parsed:
        return parsed

    if strict_alias_combo and png and svg:
        raise ValueError("Cannot specify both PNG and SVG output formats.")

    derived: set[Format] = set()
    if png:
        derived.add(Format.PNG)
    if svg:
        derived.add(Format.SVG)
    if not derived:
        derived.add(Format.PDF)
    return derived
