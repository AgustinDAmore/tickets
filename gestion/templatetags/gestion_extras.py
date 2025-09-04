from django import template
from datetime import timedelta

from django.utils.safestring import mark_safe
import re


register = template.Library()

def apply_inline_formats(text):
    """Aplica formatos en línea (negrita, color, etc.) a un fragmento de texto."""
    text = re.sub(r'N\((.*?)\)', r'<strong>\1</strong>', text)
    text = re.sub(r'I\((.*?)\)', r'<em>\1</em>', text)
    text = re.sub(r'S\((.*?)\)', r'<u>\1</u>', text)
    text = re.sub(r'T\((.*?)\)', r'<s>\1</s>', text)
    text = re.sub(r'M\(([^,)]+),\s*([^)]+)\)', r'<mark style="background-color:\1;">\2</mark>', text)
    text = re.sub(r'C\(([^,)]+),\s*([^)]+)\)', r'<span style="color:\1;">\2</span>', text)
    text = re.sub(r'url\((.*?)\)', r'<a href="\1" target="_blank" class="text-indigo-600 hover:underline">\1</a>', text)
    return text

@register.filter(name='format_text', is_safe=True)
def format_text(value):
    if not value:
        return ""

    lines = value.split('\n')
    new_html = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped_line = line.strip()

        if not stripped_line:
            if in_ul or in_ol:
                if in_ul: new_html.append('</ul>'); in_ul = False
                if in_ol: new_html.append('</ol>'); in_ol = False
            continue

        if stripped_line.startswith('* '):
            if in_ol: new_html.append('</ol>'); in_ol = False
            if not in_ul: new_html.append('<ul>'); in_ul = True
            content = apply_inline_formats(stripped_line[2:])
            new_html.append(f'<li>{content}</li>')

        elif re.match(r'^\d+\.\s', stripped_line):
            if in_ul: new_html.append('</ul>'); in_ul = False
            if not in_ol: new_html.append('<ol>'); in_ol = True
            item_content = re.sub(r'^\d+\.\s', '', stripped_line)
            content = apply_inline_formats(item_content)
            new_html.append(f'<li>{content}</li>')

        else:
            if in_ul: new_html.append('</ul>'); in_ul = False
            if in_ol: new_html.append('</ol>'); in_ol = False
            content = apply_inline_formats(line)
            new_html.append(f'<p>{content}</p>')

    if in_ul: new_html.append('</ul>')
    if in_ol: new_html.append('</ol>')

    return mark_safe(''.join(new_html))

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