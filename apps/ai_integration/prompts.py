import json


HOTEL_CONTACT = "SPK Hotel · 0208 123 4567 · contact@spkhotel.vn"


def room_advisor_prompt(needs, rooms):
    safe_rooms = [{"room_id": r.pk, "room_number": r.room_number, "room_type": r.room_type.name, "capacity": r.room_type.capacity, "price_per_night": int(r.room_type.price_per_night), "amenities": r.room_type.amenities} for r in rooms]
    return (
        "Bạn là trợ lý SPK Hotel. Chỉ chọn tối đa 3 phòng trong ROOM_ALLOW_LIST. "
        "Không tự tạo ID. Trả đúng JSON: {\"suggestions\":[{\"room_id\":1,\"room_number\":\"301\",\"reason\":\"...\"}]}.\n"
        f"Nhu cầu: {needs[:1000]}\nROOM_ALLOW_LIST={json.dumps(safe_rooms, ensure_ascii=False)}"
    )


def email_prompt(data):
    return (
        "Viết email tiếng Việt lịch sự cho SPK Hotel. Trả đúng JSON gồm subject và body. "
        "Đây chỉ là bản nháp để nhân viên duyệt. Không thêm dữ liệu không có trong INPUT.\n"
        f"INPUT={json.dumps(data, ensure_ascii=False)}"
    )


def report_prompt(data):
    return (
        "Phân tích số liệu tổng hợp SPK Hotel, không tự tạo số liệu. Trả đúng JSON: "
        "{\"comment\":\"...\",\"trends\":[\"...\"],\"warnings\":[\"...\"],"
        "\"promotions\":[\"...\"]}. promotions tối đa 3 mục.\n"
        f"AGGREGATED_DATA={json.dumps(data, ensure_ascii=False)}"
    )
