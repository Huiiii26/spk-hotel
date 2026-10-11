from django import forms

from apps.accounts.models import User

from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            "full_name",
            "email",
            "phone",
            "address",
            "date_of_birth",
            "identity_document",
            "notes",
        )
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class CustomerProfileForm(CustomerForm):
    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data.get("email", "")).lower()
        if not email:
            raise forms.ValidationError("Email là bắt buộc đối với tài khoản website.")
        queryset = User.objects.filter(email__iexact=email)
        if self.instance.user_id:
            queryset = queryset.exclude(pk=self.instance.user_id)
        if queryset.exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email
