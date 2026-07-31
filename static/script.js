document.addEventListener("DOMContentLoaded", function () {
    // 1. Live Instant Search on Student Table
    const searchInput = document.getElementById("studentSearchInput");
    const studentsTable = document.getElementById("studentsTable");

    if (searchInput && studentsTable) {
        searchInput.addEventListener("keyup", function () {
            const filter = searchInput.value.toLowerCase();
            const rows = studentsTable.querySelectorAll("tbody tr");

            rows.forEach(function (row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // 2. Mark All Present Button
    const markAllPresentBtn = document.getElementById("markAllPresentBtn");
    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener("click", function () {
            const presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
            presentRadios.forEach(function (radio) {
                radio.checked = true;
                
                // Update CSS highlight on parent labels
                const parentGroup = radio.closest(".status-selector-group");
                if (parentGroup) {
                    parentGroup.querySelectorAll(".status-option").forEach(function (opt) {
                        opt.classList.remove("selected");
                    });
                    const parentLabel = radio.closest(".status-option");
                    if (parentLabel) parentLabel.classList.add("selected");
                }
            });
        });
    }

    // 3. Interactive Radio Pill Selection
    const statusRadios = document.querySelectorAll(".status-option input[type='radio']");
    statusRadios.forEach(function (radio) {
        radio.addEventListener("change", function () {
            const parentGroup = radio.closest(".status-selector-group");
            if (parentGroup) {
                parentGroup.querySelectorAll(".status-option").forEach(function (opt) {
                    opt.classList.remove("selected");
                });
                const parentLabel = radio.closest(".status-option");
                if (parentLabel) parentLabel.classList.add("selected");
            }
        });
    });

    // 4. Auto-dismiss Flash Notifications after 5 seconds
    const flashAlerts = document.querySelectorAll(".flash-alert");
    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 0.5s ease";
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 5000);
    });
});