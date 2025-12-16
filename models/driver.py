from dataclasses import dataclass


@dataclass
class Driver:
    """Represents a race driver."""

    name: str

    def to_dict(self) -> dict:
        """Convert driver to dictionary for JSON serialization."""
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> 'Driver':
        """Create driver from dictionary."""
        return cls(name=data["name"])
