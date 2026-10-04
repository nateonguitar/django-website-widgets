import dataclasses
from dataclasses import dataclass


@dataclass(kw_only=True)
class TipResponseDto:
    """One tip, rendered on the server for the page to insert."""

    html: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
