from datetime import timedelta

from django import forms


class ReportFilterForm(forms.Form):
    class GroupBy:
        DAY = "day"
        MONTH = "month"

    start_date = forms.DateField(
        label="Từ ngày",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date = forms.DateField(
        label="Đến ngày",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    group_by = forms.ChoiceField(
        label="Nhóm biểu đồ theo",
        choices=((GroupBy.DAY, "Ngày"), (GroupBy.MONTH, "Tháng")),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if not start_date or not end_date:
            return cleaned_data
        if end_date < start_date:
            raise forms.ValidationError("Đến ngày phải lớn hơn hoặc bằng từ ngày.")
        if end_date - start_date > timedelta(days=366):
            raise forms.ValidationError("Khoảng thống kê không được vượt quá 366 ngày.")
        return cleaned_data
