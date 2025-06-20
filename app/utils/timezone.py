from datetime import timezone, datetime
from pytz import timezone as pytz_timezone

def convert_utc_to_local(dt: datetime, tz_name: str = "America/Lima") -> datetime:
    """Convert naive/UTC datetime to specified timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    target_tz = pytz_timezone(tz_name)
    return dt.astimezone(target_tz)
