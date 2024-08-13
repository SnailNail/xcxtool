"""Custom string.Formatter for backup paths and filenames"""
import string
import _string
from typing import Sequence, Any, Mapping, NamedTuple


_MISSING = object()


class _MissingField(NamedTuple):
    name: str | int
    original_field: str

    def __str__(self):
        return f"{{{self.original_field}}}"


class ForgivingFormatter(string.Formatter):
    """Custom formatter for backup paths and filenames.

    Differs from the standard formatter by ignoring unknown fields. If a field is
    not defined, it is left as-is and any format spec is stripped. E.g.:

        >>> f = ForgivingFormatter()
        >>> f.format("{missing:^12")
        "{missing}"
    """

    def get_value(
        self, key: int | str, args: Sequence[Any], kwargs: Mapping[str, Any]
    ) -> Any:
        """Get the base value referenced by the field name.

        key is looked up in args or kwargs. If it is not found, a sentinel
        value is returned.
        """
        try:
            return super().get_value(key, args, kwargs)
        except (IndexError, KeyError):
            return _MISSING

    def get_field(
        self, field_name: str, args: Sequence[Any], kwargs: Mapping[str, Any]
    ) -> tuple[Any, str]:
        """Resolve the possibly compound value from the field name.

        If the first part of a value is not found (i.e. the name or index that
        would otherwise have been passed in via self.format(*args, **kwargs) a
        _MissingField instance is returned so we can detect it later in the
        formatting process.
        """
        first, rest = _string.formatter_field_name_split(field_name)

        obj = self.get_value(first, args, kwargs)

        if obj is _MISSING:
            return _MissingField(first, field_name), first

        for is_attr, i in rest:
            if is_attr:
                obj = getattr(obj, i)
            else:
                obj = obj[i]

        return obj, first

    def format_field(self, value: Any, format_spec: str) -> Any:
        """Do the actual job of formatting a field.

        Since we can't intercept the format spec at any point before this
        function is called (without re-implementing the Formatter._vformat()
        method) we need to detect a missing value here. Hence the _MissingValue
        class.
        """
        if isinstance(value, _MissingField):
            format_spec = ""
        return format(value, format_spec)
