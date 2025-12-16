import re


def format_time(seconds: float) -> str:
    """
    Format seconds as HH:MM:SS string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string in HH:MM:SS format
    """
    if seconds < 0:
        return "00:00:00"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def ordinal(number: int) -> str:
    """
    Convert number to ordinal string (1st, 2nd, 3rd, etc.).

    Args:
        number: Integer to convert

    Returns:
        Ordinal string representation
    """
    if 10 <= number % 100 <= 20:
        return f"{number}th"

    suffix_map = {1: 'st', 2: 'nd', 3: 'rd'}
    return f"{number}{suffix_map.get(number % 10, 'th')}"


def dms_to_decimal(dms_str: str) -> float:
    """
    Convert DMS (Degrees Minutes Seconds) string to decimal degrees.

    Args:
        dms_str: DMS string (e.g., "25°08'21.7\"N")

    Returns:
        Decimal degrees

    Raises:
        ValueError: If DMS format is invalid
    """
    pattern = r"(\d+)°(\d+)'([\d.]+)\"?([NSEW])"
    match = re.match(pattern, dms_str.strip())

    if not match:
        raise ValueError(f"Invalid DMS format: {dms_str}")

    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600

    if direction in ['S', 'W']:
        decimal = -decimal

    return decimal
