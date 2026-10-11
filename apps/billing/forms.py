from django import forms

from .models import Payment


class InvoiceAdjustmentForm(forms.Form):
    surcharge = forms.DecimalField(label="Phụ thu", min_value=0, max_digits=14, decimal_places=0, widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}))
    discount = forms.DecimalField(label="Giảm giá", min_value=0, max_digits=14, decimal_places=0, widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}))


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "paid_at", "reference", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "paid_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["paid_at"].input_formats = ["%Y-%m-%dT%H:%M"]
