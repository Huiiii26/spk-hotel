from django import forms

from .models import Room, RoomType


class RoomTypeForm(forms.ModelForm):
    amenities_text = forms.CharField(
        label="Tiện ích",
        required=False,
        help_text="Nhập các tiện ích, ngăn cách bằng dấu phẩy.",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Wi-Fi, Điều hòa, Bồn tắm"}),
    )

    class Meta:
        model = RoomType
        fields = ("name", "description", "capacity", "price_per_hour", "price_per_night", "image", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "price_per_night": forms.NumberInput(attrs={"min": 0, "step": 1000}),
            "price_per_hour": forms.NumberInput(attrs={"min": 0, "step": 1000}),
            "capacity": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price_per_hour"].required = False
        self.fields["price_per_hour"].initial = self.instance.price_per_hour or 100000
        if self.instance.pk:
            self.fields["amenities_text"].initial = ", ".join(self.instance.amenities or [])
        for name, field in self.fields.items():
            if name == "is_active":
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_price_per_hour(self):
        return self.cleaned_data.get("price_per_hour") or 100000

    def clean_amenities_text(self):
        raw_value = self.cleaned_data.get("amenities_text", "")
        unique = []
        seen = set()
        for item in raw_value.split(","):
            value = " ".join(item.strip().split())
            key = value.casefold()
            if value and key not in seen:
                unique.append(value)
                seen.add(key)
        return unique

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.amenities = self.cleaned_data["amenities_text"]
        if commit:
            instance.save()
        return instance


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("room_number", "room_type", "floor", "status", "notes", "is_active")
        widgets = {
            "floor": forms.NumberInput(attrs={"min": 0}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_type"].queryset = RoomType.objects.order_by("name")
        for name, field in self.fields.items():
            if name == "is_active":
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
