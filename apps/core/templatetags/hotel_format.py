from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def vnd(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")
    return f"{amount:,.0f}".replace(",", ".") + " ₫"


@register.filter
def vi_date(value):
    """Hiển thị ngày theo định dạng Việt Nam dd/MM/yyyy."""

    if not value:
        return "—"
    try:
        return value.strftime("%d/%m/%Y")
    except (AttributeError, ValueError):
        return value


@register.filter(expects_localtime=True)
def vi_datetime(value):
    """Hiển thị ngày giờ theo định dạng Việt Nam."""

    if not value:
        return "—"
    try:
        return value.strftime("%H:%M %d/%m/%Y")
    except (AttributeError, ValueError):
        return value
