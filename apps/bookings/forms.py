from datetime import timedelta

from django import forms

from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType


DATETIME_INPUT_FORMATS = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"]


class AvailabilitySearchForm(forms.Form):
    check_in_date = forms.DateTimeField(
        label="Ngày, giờ nhận phòng",
        input_formats=DATETIME_INPUT_FORMATS,
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}),
    )
    check_out_date = forms.DateTimeField(
        label="Ngày, giờ trả phòng",
        input_formats=DATETIME_INPUT_FORMATS,
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}),
    )
    guest_count = forms.IntegerField(
        label="Số khách",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )
    room_type = forms.ModelChoiceField(
        label="Loại phòng",
        queryset=RoomType.objects.none(),
        required=False,
        empty_label="Tất cả loại phòng",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    max_budget = forms.DecimalField(
        label="Ngân sách tối đa mỗi đêm",
        max_digits=12,
        decimal_places=0,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": 1000}),
    )
    amenities = forms.CharField(
        label="Tiện ích mong muốn",
        required=False,
        help_text="Nhập các tiện ích, cách nhau bằng dấu phẩy. Ví dụ: WiFi, ban công.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "WiFi, điều hòa"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_type"].queryset = RoomType.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in_date")
        check_out = cleaned_data.get("check_out_date")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out_date", "Thời gian trả phòng phải sau thời gian nhận phòng.")
        return cleaned_data

    def amenity_list(self):
        value = self.cleaned_data.get("amenities", "")
        return [item.strip() for item in value.split(",") if item.strip()]


class BookingFormBase(forms.Form):
    room = forms.ModelChoiceField(
        label="Phòng",
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    check_in_date = forms.DateTimeField(
        label="Ngày, giờ nhận phòng",
        input_formats=DATETIME_INPUT_FORMATS,
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}),
    )
    check_out_date = forms.DateTimeField(
        label="Ngày, giờ trả phòng",
        input_formats=DATETIME_INPUT_FORMATS,
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local", "class": "form-control"}),
    )
    guest_count = forms.IntegerField(
        label="Số khách",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )
    notes = forms.CharField(
        label="Ghi chú",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.select_related("room_type").filter(
            is_active=True,
            room_type__is_active=True,
        ).exclude(status=Room.Status.MAINTENANCE)

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in_date")
        check_out = cleaned_data.get("check_out_date")
        room = cleaned_data.get("room")
        guest_count = cleaned_data.get("guest_count")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out_date", "Thời gian trả phòng phải sau thời gian nhận phòng.")
        if room and guest_count and guest_count > room.room_type.capacity:
            self.add_error("guest_count", "Số khách vượt quá sức chứa của phòng.")
        return cleaned_data


class CustomerBookingForm(BookingFormBase):
    pass


class ReceptionistBookingForm(BookingFormBase):
    customer = forms.ModelChoiceField(
        label="Khách hàng",
        queryset=Customer.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    field_order = ["customer", "room", "check_in_date", "check_out_date", "guest_count", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.order_by("full_name")


class CancellationForm(forms.Form):
    reason = forms.CharField(
        label="Lý do hủy",
        required=False,
        max_length=255,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 3, "placeholder": "Nhập lý do hủy (không bắt buộc)"}
        ),
    )


class CalendarFilterForm(forms.Form):
    start_date = forms.DateField(
        label="Từ ngày",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date = forms.DateField(
        label="Đến ngày",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end:
            if end < start:
                self.add_error("end_date", "Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")
            elif end - start > timedelta(days=62):
                self.add_error("end_date", "Khoảng xem lịch tối đa là 62 ngày.")
        return cleaned_data


def attach_service_error(form, error):
    """Đưa lỗi nghiệp vụ về form thay vì hiển thị lỗi hệ thống."""

    if hasattr(error, "message_dict"):
        for field, messages in error.message_dict.items():
            target = field if field in form.fields else None
            for message in messages:
                form.add_error(target, message)
    else:
        for message in getattr(error, "messages", [str(error)]):
            form.add_error(None, message)
