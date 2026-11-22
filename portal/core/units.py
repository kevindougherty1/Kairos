"""Unit conversion at the interface. Everything is stored in metres and seconds."""

METRES_PER_MILE = 1609.344
METRES_PER_KM = 1000


def miles_to_m(miles):
    return round(miles * METRES_PER_MILE)


def m_to_miles(metres):
    return metres / METRES_PER_MILE


def format_distance(metres, units="mi"):
    """'13.1 mi' / '21.1 km'; whole numbers drop the decimal ('6 mi')."""
    if metres is None:
        return ""
    value = metres / (METRES_PER_KM if units == "km" else METRES_PER_MILE)
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{text} {units}"


def format_duration(seconds):
    """'1:05:30' or '45:00'."""
    if seconds is None:
        return ""
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
