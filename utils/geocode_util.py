from typing import Optional, Tuple
from geopy.geocoders import Nominatim


def geocode_address(address: str, timeout: int = 10) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode an address to latitude and longitude coordinates.

    Args:
        address: Address string to geocode
        timeout: Request timeout in seconds

    Returns:
        Tuple of (latitude, longitude) or (None, None) if geocoding fails
    """
    geolocator = Nominatim(user_agent="karting_app")

    try:
        location = geolocator.geocode(address, timeout=timeout)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass

    return None, None
