from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_timedelta(td: timedelta):
    """
    Formatea un objeto timedelta en una cadena legible como '3d 4h 15m'.
    """
    if not isinstance(td, timedelta):
        return "" # Devuelve vacío si no es un timedelta

    total_seconds = int(td.total_seconds())
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    if not parts and total_seconds > 0:
        return f"{total_seconds}s"

    return " ".join(parts) if parts else "0m"