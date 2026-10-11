from django.utils import timezone
from django.shortcuts import render

from apps.accounts.models import User
from apps.accounts.permissions import role_required

from .forms import ReportFilterForm
from .services import build_report_data


@role_required(User.Role.MANAGER, User.Role.ACCOUNTANT)
def report_dashboard(request):
    today = timezone.localdate()
    initial = {"start_date": today.replace(day=1), "end_date": today, "group_by": "day"}
    form = ReportFilterForm(request.GET or None, initial=initial)
    report = None
    if form.is_valid():
        report = build_report_data(**form.cleaned_data)
    elif not request.GET:
        report = build_report_data(**initial)
    return render(request, "reports/report_dashboard.html", {"form": form, "report": report})
