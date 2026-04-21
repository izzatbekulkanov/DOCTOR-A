document.addEventListener("DOMContentLoaded", () => {
    const iconSelect = document.getElementById("icon_class");
    const iconPreview = document.querySelector("[data-service-icon]");
    const iconLabel = document.querySelector("[data-service-icon-label]");
    const orderInput = document.getElementById("sort_order");
    const orderPreview = document.querySelector("[data-service-order]");
    const statusInput = document.getElementById("is_active");
    const statusPreview = document.querySelector("[data-service-status]");
    const iconSelectRoot = document.querySelector("[data-icon-select]");
    const iconSelectTrigger = document.querySelector("[data-icon-select-trigger]");
    const iconSelectTriggerIcon = document.querySelector("[data-icon-select-trigger-icon]");
    const iconSelectTriggerTitle = document.querySelector("[data-icon-select-trigger-title]");
    const iconSelectTriggerSubtitle = document.querySelector("[data-icon-select-trigger-subtitle]");
    const iconSelectOptions = document.querySelectorAll("[data-icon-option]");

    const closeIconPanel = () => {
        if (!iconSelectRoot || !iconSelectTrigger) {
            return;
        }

        iconSelectRoot.classList.remove("is-open");
        iconSelectTrigger.setAttribute("aria-expanded", "false");
    };

    const openIconPanel = () => {
        if (!iconSelectRoot || !iconSelectTrigger) {
            return;
        }

        iconSelectRoot.classList.add("is-open");
        iconSelectTrigger.setAttribute("aria-expanded", "true");
    };

    const syncActiveOption = () => {
        if (!iconSelectOptions.length || !iconSelect) {
            return;
        }

        iconSelectOptions.forEach((option) => {
            option.classList.toggle("is-active", option.dataset.value === iconSelect.value);
        });
    };

    const updatePreview = () => {
        if (iconSelect && iconPreview) {
            iconPreview.className = iconSelect.value;
        }

        if (iconSelect && iconLabel) {
            iconLabel.textContent = iconSelect.value;
        }

        if (iconSelect && iconSelectTriggerIcon) {
            iconSelectTriggerIcon.className = iconSelect.value;
        }

        if (iconSelect && iconSelectTriggerTitle) {
            const activeOption = Array.from(iconSelectOptions).find((option) => option.dataset.value === iconSelect.value);
            iconSelectTriggerTitle.textContent = activeOption?.dataset.label || iconSelect.value;
        }

        if (iconSelect && iconSelectTriggerSubtitle) {
            iconSelectTriggerSubtitle.textContent = iconSelect.value;
        }

        if (orderInput && orderPreview) {
            orderPreview.textContent = orderInput.value || "0";
        }

        if (statusInput && statusPreview) {
            statusPreview.textContent = statusInput.checked ? "Faol" : "Faol emas";
        }

        syncActiveOption();
    };

    if (iconSelectTrigger && iconSelectRoot) {
        iconSelectTrigger.addEventListener("click", () => {
            if (iconSelectRoot.classList.contains("is-open")) {
                closeIconPanel();
                return;
            }

            openIconPanel();
        });
    }

    if (iconSelectOptions.length && iconSelect) {
        iconSelectOptions.forEach((option) => {
            option.addEventListener("click", () => {
                iconSelect.value = option.dataset.value || "";
                updatePreview();
                closeIconPanel();
            });
        });
    }

    document.addEventListener("click", (event) => {
        if (!iconSelectRoot || iconSelectRoot.contains(event.target)) {
            return;
        }

        closeIconPanel();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeIconPanel();
        }
    });

    if (iconSelect) {
        iconSelect.addEventListener("change", updatePreview);
    }

    if (orderInput) {
        orderInput.addEventListener("input", updatePreview);
    }

    if (statusInput) {
        statusInput.addEventListener("change", updatePreview);
    }

    updatePreview();
});
