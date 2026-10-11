import json
import time

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Invoice

from .client import GeminiError, chat_completion
from .models import AILog, EmailDraft
from .prompts import HOTEL_CONTACT, email_prompt, report_prompt, room_advisor_prompt


def _json_object(raw):
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError
    return data


def _log(user, feature, status, request_summary, response_summary=None, error_code="", started=None):
    return AILog.objects.create(user=user if getattr(user, "is_authenticated", False) else None, feature=feature, status=status, request_summary=request_summary, response_summary=response_summary or {}, error_code=error_code, duration_ms=max(int((time.monotonic() - started) * 1000), 0) if started else 0)


def advise_rooms(*, user, needs, rooms):
    started = time.monotonic()
    allowed = {room.pk: room for room in rooms}
    fallback = [{"room_id": room.pk, "room_number": room.room_number, "reason": "Phù hợp bộ lọc và còn trống trong khoảng ngày đã chọn."} for room in rooms[:3]]
    summary = {"needs": needs[:300], "allowed_room_ids": list(allowed)}
    try:
        data = _json_object(chat_completion(room_advisor_prompt(needs, rooms)))
        suggestions = []
        for item in data.get("suggestions", [])[:3]:
            room = allowed.get(item.get("room_id"))
            if room and str(item.get("room_number")) == room.room_number:
                suggestions.append({"room_id": room.pk, "room_number": room.room_number, "reason": str(item.get("reason", "Phù hợp nhu cầu."))[:300]})
        if not suggestions:
            raise ValueError
        _log(user, AILog.Feature.ROOM_ADVISOR, AILog.Status.SUCCESS, summary, {"suggested_room_ids": [x["room_id"] for x in suggestions]}, started=started)
        return suggestions, AILog.Status.SUCCESS
    except (GeminiError, ValueError, TypeError, json.JSONDecodeError) as error:
        code = getattr(error, "code", "INVALID_RESPONSE")
        _log(user, AILog.Feature.ROOM_ADVISOR, AILog.Status.FALLBACK, summary, {"suggested_room_ids": [x["room_id"] for x in fallback]}, code, started)
        return fallback, AILog.Status.FALLBACK


def _email_data(booking, email_type):
    invoice = Invoice.objects.filter(booking=booking).first()
    return {"email_type": email_type, "customer_name": booking.customer.full_name, "booking_code": booking.booking_code, "room_type": booking.room.room_type.name, "check_in": booking.check_in_date.isoformat(), "check_out": booking.check_out_date.isoformat(), "total_amount": int(invoice.total_amount) if invoice else None, "balance_due": int(invoice.balance_due) if invoice else None, "hotel_contact": HOTEL_CONTACT}


def _static_email(data):
    labels = {EmailDraft.EmailType.CONFIRMATION: "Xác nhận đặt phòng", EmailDraft.EmailType.CANCELLATION: "Thông báo hủy đặt phòng", EmailDraft.EmailType.PAYMENT_REMINDER: "Nhắc thanh toán"}
    subject = f"SPK Hotel - {labels[data['email_type']]} {data['booking_code']}"
    body = f"Kính gửi {data['customer_name']},\n\nSPK Hotel thông báo về booking {data['booking_code']}, loại phòng {data['room_type']}, từ {data['check_in']} đến {data['check_out']}."
    if data["balance_due"] is not None:
        body += f" Số tiền còn thiếu: {data['balance_due']:,} đồng."
    return {"subject": subject, "body": body + f"\n\nTrân trọng,\n{HOTEL_CONTACT}"}


@transaction.atomic
def generate_email_draft(*, actor, booking, email_type):
    started = time.monotonic()
    data = _email_data(booking, email_type)
    generated_by_ai = True
    try:
        content = _json_object(chat_completion(email_prompt(data)))
        if not isinstance(content.get("subject"), str) or not isinstance(content.get("body"), str):
            raise ValueError
        status, code = AILog.Status.SUCCESS, ""
    except (GeminiError, ValueError, TypeError, json.JSONDecodeError) as error:
        content, generated_by_ai = _static_email(data), False
        status, code = AILog.Status.FALLBACK, getattr(error, "code", "INVALID_RESPONSE")
    draft = EmailDraft.objects.create(booking=booking, email_type=email_type, recipient_email=booking.customer.email, subject=content["subject"][:200], body=content["body"], created_by=actor, generated_by_ai=generated_by_ai)
    _log(actor, AILog.Feature.EMAIL, status, {"booking_code": booking.booking_code, "email_type": email_type}, {"draft_id": draft.pk}, code, started)
    return draft, status


def analyze_report(*, user, report):
    started = time.monotonic()
    data = {"start_date": report["start_date"].isoformat(), "end_date": report["end_date"].isoformat(), "occupancy_rate": report["occupancy"]["rate"], "revenue": int(report["revenue"]), "booking_count": report["booking_count"], "cancellation_rate": report["cancellation_rate"], "top_room_type": (report["top_room_type"] or {}).get("room__room_type__name"), "top_service": (report["top_service"] or {}).get("service__name")}
    fallback = {"comment": "Không thể kết nối AI. Số liệu gốc vẫn được hiển thị và không bị thay đổi.", "trends": [], "warnings": [], "promotions": []}
    try:
        result = _json_object(chat_completion(report_prompt(data)))
        if not isinstance(result.get("comment"), str):
            raise ValueError
        result["trends"] = [str(x)[:300] for x in result.get("trends", [])[:5]]
        result["warnings"] = [str(x)[:300] for x in result.get("warnings", [])[:5]]
        result["promotions"] = [str(x)[:300] for x in result.get("promotions", [])[:3]]
        _log(user, AILog.Feature.REPORT, AILog.Status.SUCCESS, data, {"promotion_count": len(result["promotions"])}, started=started)
        return result, AILog.Status.SUCCESS
    except (GeminiError, ValueError, TypeError, json.JSONDecodeError) as error:
        _log(user, AILog.Feature.REPORT, AILog.Status.FALLBACK, data, {}, getattr(error, "code", "INVALID_RESPONSE"), started)
        return fallback, AILog.Status.FALLBACK


@transaction.atomic
def approve_email_draft(*, actor, draft, subject, body, simulate_send=False):
    if draft.status != EmailDraft.Status.DRAFT:
        raise ValidationError("Chỉ có thể duyệt email đang ở trạng thái bản nháp.")
    draft.subject = subject.strip()[:200]
    draft.body = body.strip()
    if not draft.subject or not draft.body:
        raise ValidationError("Tiêu đề và nội dung email không được để trống.")
    draft.status = EmailDraft.Status.SIMULATED_SENT if simulate_send else EmailDraft.Status.APPROVED
    draft.approved_by = actor
    draft.approved_at = timezone.now()
    draft.save()
    return draft


@transaction.atomic
def cancel_email_draft(*, actor, draft):
    if draft.status != EmailDraft.Status.DRAFT:
        raise ValidationError("Chỉ có thể hủy email đang ở trạng thái bản nháp.")
    draft.status = EmailDraft.Status.CANCELLED
    draft.save(update_fields=["status", "updated_at"])
    return draft
