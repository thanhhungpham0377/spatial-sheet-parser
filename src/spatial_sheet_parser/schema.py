"""Schema contract models and validation result structures for Spatial Sheet Parser."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Schema Validation Error Codes
ERR_MISSING_METADATA = "MISSING_METADATA"
ERR_INVALID_METADATA_FIELD = "INVALID_METADATA_FIELD"
ERR_MISSING_TABLE_FIELD = "MISSING_TABLE_FIELD"
ERR_INVALID_TABLE_FIELD = "INVALID_TABLE_FIELD"
ERR_CONFIDENCE_OUT_OF_BOUNDS = "CONFIDENCE_OUT_OF_BOUNDS"
ERR_INVALID_COORDINATES = "INVALID_COORDINATES"
ERR_DUPLICATE_TABLE_ID = "DUPLICATE_TABLE_ID"
ERR_DUPLICATE_COLUMN_KEY = "DUPLICATE_COLUMN_KEY"
ERR_RECORD_KEY_MISMATCH = "RECORD_KEY_MISMATCH"
ERR_HIERARCHY_MISSING_PARENT = "HIERARCHY_MISSING_PARENT"
ERR_HIERARCHY_MISSING_CHILD = "HIERARCHY_MISSING_CHILD"
ERR_HIERARCHY_CHILD_PARENT_MISMATCH = "HIERARCHY_CHILD_PARENT_MISMATCH"
ERR_HIERARCHY_CYCLE_DETECTED = "HIERARCHY_CYCLE_DETECTED"
ERR_ORPHAN_HAS_PARENT = "ORPHAN_HAS_PARENT"
ERR_ORPHAN_IN_CHILDREN = "ORPHAN_IN_CHILDREN"
ERR_UNCLASSIFIED_ROW_MALFORMED = "UNCLASSIFIED_ROW_MALFORMED"


@dataclass
class ValidationError:
    """Represents a machine-readable schema contract validation error."""

    code: str
    path: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ValidationWarning:
    """Represents a machine-readable schema contract validation warning."""

    code: str
    path: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ValidationResult:
    """Machine-readable validation outcome for parser JSON output contract."""

    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)

    def add_error(
        self,
        code: str,
        path: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends a validation error and marks result as invalid."""
        self.is_valid = False
        self.errors.append(
            ValidationError(
                code=code,
                path=path,
                message=message,
                context=context or {},
            )
        )

    def add_warning(
        self,
        code: str,
        path: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends a validation warning without marking result invalid."""
        self.warnings.append(
            ValidationWarning(
                code=code,
                path=path,
                message=message,
                context=context or {},
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes validation result into machine-readable JSON structure."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }
