from django import forms

from apps.bookings.forms import AvailabilitySearchForm

from .models import EmailDraft


class RoomAdvisorForm(AvailabilitySearchForm):
    needs = forms.CharField(label="Nhu cầu thêm", required=False, max_length=1000, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ví dụ: cần phòng yên tĩnh, phù hợp gia đình..."}))


class EmailGenerateForm(forms.Form):
    email_type = forms.ChoiceField(label="Loại email", choices=EmailDraft.EmailType.choices, widget=forms.Select(attrs={"class": "form-select"}))


class EmailDraftReviewForm(forms.ModelForm):
    simulate_send = forms.BooleanField(label="Mô phỏng gửi sau khi duyệt", required=False)

    class Meta:
        model = EmailDraft
        fields = ("subject", "body")
        widgets = {"subject": forms.TextInput(attrs={"class": "form-control"}), "body": forms.Textarea(attrs={"class": "form-control", "rows": 12})}
