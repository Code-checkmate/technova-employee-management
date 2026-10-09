/**
 * TechNova Employee Management System — Client-Side Scripts
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------------------
    // Mobile Sidebar Toggle
    // -------------------------------------------------------------------------
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");

    if (sidebarToggle && sidebar && backdrop) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("show");
            backdrop.classList.toggle("show");
        });

        backdrop.addEventListener("click", () => {
            sidebar.classList.remove("show");
            backdrop.classList.remove("show");
        });
    }

    // -------------------------------------------------------------------------
    // Delete Confirmation Modal Handling
    // -------------------------------------------------------------------------
    const deleteModal = document.getElementById("deleteConfirmModal");
    if (deleteModal) {
        deleteModal.addEventListener("show.bs.modal", (event) => {
            const button = event.relatedTarget;
            if (!button) return;

            const employeeId = button.getAttribute("data-employee-id");
            const employeeName = button.getAttribute("data-employee-name");

            const modalEmployeeName = deleteModal.querySelector("#modalEmployeeName");
            const deleteForm = deleteModal.querySelector("#deleteEmployeeForm");

            if (modalEmployeeName) {
                modalEmployeeName.textContent = employeeName || "this employee";
            }
            if (deleteForm && employeeId) {
                deleteForm.action = `/employees/${employeeId}/delete`;
            }
        });
    }

    // -------------------------------------------------------------------------
    // Auto-dismiss Flash Alerts
    // -------------------------------------------------------------------------
    const alertElements = document.querySelectorAll(".alert-dismissible");
    alertElements.forEach((alertEl) => {
        setTimeout(() => {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
                if (bsAlert) {
                    bsAlert.close();
                }
            } catch (e) {
                // Ignore if bootstrap is still loading
            }
        }, 6000);
    });

    // -------------------------------------------------------------------------
    // Health Ping Button on Database Status Page
    // -------------------------------------------------------------------------
    const refreshHealthBtn = document.getElementById("btnRefreshHealth");
    if (refreshHealthBtn) {
        refreshHealthBtn.addEventListener("click", async () => {
            refreshHealthBtn.disabled = true;
            const originalHtml = refreshHealthBtn.innerHTML;
            refreshHealthBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Checking...';

            try {
                const resp = await fetch("/health");
                const data = await resp.json();
                window.location.reload();
            } catch (err) {
                console.error("Health check error:", err);
                window.location.reload();
            }
        });
    }
});
