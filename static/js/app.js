document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form[method='post'], form[method='POST']").forEach((form) => {
        form.addEventListener("submit", () => {
            form.querySelectorAll("button:not([type]), button[type='submit']").forEach((button) => {
                button.disabled = true;
                const originalText = button.textContent.trim();
                button.dataset.originalText = originalText;
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Đang xử lý...';
            });
        });
    });

    const sidebar = document.getElementById("dashboardSidebar");
    const toggle = document.getElementById("sidebarToggle");
    const backdrop = document.getElementById("sidebarBackdrop");
    const closeSidebar = () => {
        sidebar?.classList.remove("open");
        backdrop?.classList.remove("show");
    };
    toggle?.addEventListener("click", () => {
        sidebar?.classList.toggle("open");
        backdrop?.classList.toggle("show");
    });
    backdrop?.addEventListener("click", closeSidebar);

    const actionForm = document.getElementById("bookingActionForm");
    const actionTitle = document.getElementById("actionModalTitle");
    const actionMessage = document.getElementById("actionModalMessage");
    const reasonGroup = document.getElementById("cancellationReasonGroup");
    const reasonInput = document.getElementById("id_action_reason");
    document.querySelectorAll(".action-trigger").forEach((button) => {
        button.addEventListener("click", () => {
            if (actionForm) actionForm.action = button.dataset.actionUrl || "";
            if (actionTitle) actionTitle.textContent = button.dataset.actionTitle || "Xác nhận thao tác";
            if (actionMessage) actionMessage.textContent = button.dataset.actionMessage || "Bạn có chắc chắn?";
            const needsReason = button.dataset.requireReason === "true";
            reasonGroup?.classList.toggle("d-none", !needsReason);
            if (reasonInput) {
                reasonInput.required = needsReason;
                reasonInput.value = "";
            }
        });
    });
});
