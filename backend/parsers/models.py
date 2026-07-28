from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedSymbol:
    name: str
    kind: str
    start_line: int
    end_line: int
    signature: str | None = None
    parent_name: str | None = None


@dataclass
class ParsedFile:
    path: str
    language: str
    size_bytes: int
    line_count: int
    symbols: list[ParsedSymbol] = field(default_factory=list)


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


@dataclass(frozen=True)
class ParseResult:
    files: list[ParsedFile]
    skipped_files: list[SkippedFile]
    file_count: int
    symbol_count: int
    skipped_count: int
