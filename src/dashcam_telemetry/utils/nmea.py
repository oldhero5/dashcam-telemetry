"""NMEA coordinate conversion utilities."""


def nmea_to_decimal(nmea_val: float) -> float:
    """Convert NMEA format (DDMM.MMMM) to decimal degrees.

    NMEA format encodes coordinates as degrees and decimal minutes:
    - Latitude: DDMM.MMMM (e.g., 3840.7339 = 38°40.7339')
    - Longitude: DDDMM.MMMM (e.g., 07716.2932 = 77°16.2932')

    Args:
        nmea_val: Coordinate in NMEA format

    Returns:
        Coordinate in decimal degrees
    """
    degrees = int(nmea_val / 100)
    minutes = nmea_val - (degrees * 100)
    return degrees + minutes / 60.0


def decimal_to_nmea(decimal_deg: float) -> float:
    """Convert decimal degrees to NMEA format.

    Args:
        decimal_deg: Coordinate in decimal degrees

    Returns:
        Coordinate in NMEA format (DDMM.MMMM or DDDMM.MMMM)
    """
    degrees = int(abs(decimal_deg))
    minutes = (abs(decimal_deg) - degrees) * 60
    return degrees * 100 + minutes
