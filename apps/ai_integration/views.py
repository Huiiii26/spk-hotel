from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.bookings.models import Booking
from apps.bookings.services import find_available_rooms
from apps.reports.forms import ReportFilterForm
from apps.reports.services import build_report_data

from .forms import EmailDraftReviewForm, EmailGenerateForm, RoomAdvisorForm
from .models import AILog, EmailDraft
from .services import advise_rooms, analyze_report, approve_email_draft, cancel_email_draft, generate_email_draft


@role_required(User.Role.CUSTOMER, User.Role.MANAGER, User.Role.RECEPTIONIST)
def room_advisor(request):
    form = RoomAdvisorForm(request.POST or None)
    rooms = suggestions = []
    ai_status = None
    no_rooms = False
    if request.method == "POST" and form.is_valid():
        rooms = find_available_rooms(check_in_date=form.cleaned_data["check_in_date"], check_out_date=form.cleaned_data["check_out_date"], guest_count=form.cleaned_data["guest_count"], room_type=form.cleaned_data.get("room_type"), max_budget=form.cleaned_data.get("max_budget"), amenities=form.amenity_list())
        no_rooms = not rooms
        if rooms:
            suggestions, ai_status = advise_rooms(user=request.user, needs=form.cleaned_data["needs"], rooms=rooms)
    return render(request, "ai_integration/room_advisor.html", {"form": form, "rooms": rooms, "suggestions": suggestions, "ai_status": ai_status, "no_rooms": no_rooms})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT)
def email_generate(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related("customer", "room__room_type"), pk=booking_id)
    form = EmailGenerateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email_type = form.cleaned_data["email_type"]
        if request.user.role == User.Role.ACCOUNTANT and email_type != EmailDraft.EmailType.PAYMENT_REMINDER:
            messages.error(request, "Kế toán chỉ được sinh email nhắc thanh toán.")
        else:
            draft, status = generate_email_draft(actor=request.user, booking=booking, email_type=email_type)
            return redirect("ai-integration:email-review", pk=draft.pk)
    return render(request, "ai_integration/email_generate.html", {"form": form, "booking": booking})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT)
def email_review(request, pk):
    draft = get_object_or_404(EmailDraft.objects.select_related("booking", "booking__customer"), pk=pk)
    if request.user.role == User.Role.ACCOUNTANT and draft.email_type != EmailDraft.EmailType.PAYMENT_REMINDER:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Kế toán chỉ được duyệt email nhắc thanh toán.")
    form = EmailDraftReviewForm(request.POST or None, instance=draft)
    if request.method == "POST" and form.is_valid():
        approve_email_draft(actor=request.user, draft=draft, subject=form.cleaned_data["subject"], body=form.cleaned_data["body"], simulate_send=form.cleaned_data["simulate_send"])
        messages.success(request, "Đã mô phỏng gửi email." if form.cleaned_data["simulate_send"] else "Đã duyệt bản nháp email.")
        return redirect("ai-integration:email-review", pk=draft.pk)
    return render(request, "ai_integration/email_review.html", {"form": form, "draft": draft})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT)
@require_POST
def email_cancel(request, pk):
    draft = get_object_or_404(EmailDraft.objects.select_related("booking"), pk=pk)
    if request.user.role == User.Role.ACCOUNTANT and draft.email_type != EmailDraft.EmailType.PAYMENT_REMINDER:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Kế toán chỉ được thao tác email nhắc thanh toán.")
    try:
        cancel_email_draft(actor=request.user, draft=draft)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
        return redirect("ai-integration:email-review", pk=draft.pk)
    return redirect("bookings-staff:detail", pk=draft.booking_id)


@role_required(User.Role.MANAGER, User.Role.ACCOUNTANT)
def ai_report(request):
    today = timezone.localdate()
    defaults = {"start_date": today.replace(day=1), "end_date": today, "group_by": "day"}
    form = ReportFilterForm(request.POST or None, initial=defaults)
    report = analysis = ai_status = None
    if request.method == "POST" and form.is_valid():
        report = build_report_data(**form.cleaned_data)
        analysis, ai_status = analyze_report(user=request.user, report=report)
    return render(request, "ai_integration/ai_report.html", {"form": form, "report": report, "analysis": analysis, "ai_status": ai_status})


@role_required(User.Role.MANAGER)
def ai_log_list(request):
    return render(request, "ai_integration/ai_log_list.html", {"logs": AILog.objects.select_related("user")[:100]})
