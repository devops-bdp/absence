"""Formatting utilities"""


def format_hours(hours):
    """Format jam desimal ke format yang mudah dibaca"""
    h = int(hours)
    m = int((hours - h) * 60)
    if m > 0:
        return f"{h:,} jam {m} menit"
    else:
        return f"{h:,} jam"


def format_hours_simple(hours):
    """Format jam desimal ke format sederhana (untuk help text)"""
    return f"{hours:,.2f} jam"


def format_hours_excel(hours):
    """Format jam desimal ke format yang mudah dibaca untuk Excel"""
    h = int(hours)
    m = int((hours - h) * 60)
    if m > 0:
        return f"{h:,} jam {m} menit"
    else:
        return f"{h:,} jam"


def format_hours_pdf(hours):
    """Format jam desimal ke format yang mudah dibaca untuk PDF"""
    h = int(hours)
    m = int((hours - h) * 60)
    if m > 0:
        return f"{h:,} jam {m} menit"
    else:
        return f"{h:,} jam"

