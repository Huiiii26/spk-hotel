from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required

from .forms import RoomForm, RoomTypeForm
from .models import Room, RoomType
from .services import save_room, save_room_type


def public_room_type_list(request):
    room_types = RoomType.objects.filter(is_active=True).prefetch_related("rooms")
    return render(request, "rooms/public_room_type_list.html", {"room_types": room_types})


def public_room_type_detail(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk, is_active=True)
    rooms = room_type.rooms.filter(is_active=True).order_by("floor", "room_number")
    return render(
        request,
        "rooms/public_room_type_detail.html",
        {"room_type": room_type, "rooms": rooms},
    )


@role_required(User.Role.MANAGER)
def room_type_list(request):
    room_types = RoomType.objects.prefetch_related("rooms").all()
    return render(request, "rooms/room_type_list.html", {"room_types": room_types})


@role_required(User.Role.MANAGER)
def room_type_create(request):
    form = RoomTypeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        save_room_type(actor=request.user, form=form)
        messages.success(request, "Đã tạo loại phòng.")
        return redirect("rooms-staff:room-type-list")
    return render(request, "rooms/room_type_form.html", {"form": form, "title": "Thêm loại phòng"})


@role_required(User.Role.MANAGER)
def room_type_update(request, pk):
    room_type = get_object_or_404(RoomType, pk=pk)
    form = RoomTypeForm(request.POST or None, request.FILES or None, instance=room_type)
    if request.method == "POST" and form.is_valid():
        save_room_type(actor=request.user, form=form)
        messages.success(request, "Đã cập nhật loại phòng.")
        return redirect("rooms-staff:room-type-list")
    return render(request, "rooms/room_type_form.html", {"form": form, "title": "Sửa loại phòng"})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def room_list(request):
    rooms = Room.objects.select_related("room_type").all()
    return render(request, "rooms/room_list.html", {"rooms": rooms})


@role_required(User.Role.MANAGER)
def room_create(request):
    form = RoomForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_room(actor=request.user, form=form)
        messages.success(request, "Đã tạo phòng.")
        return redirect("rooms-staff:room-list")
    return render(request, "rooms/room_form.html", {"form": form, "title": "Thêm phòng"})


@role_required(User.Role.MANAGER)
def room_update(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(request.POST or None, instance=room)
    if request.method == "POST" and form.is_valid():
        save_room(actor=request.user, form=form)
        messages.success(request, "Đã cập nhật phòng.")
        return redirect("rooms-staff:room-list")
    return render(request, "rooms/room_form.html", {"form": form, "title": "Sửa phòng"})
