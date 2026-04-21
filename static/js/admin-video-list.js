document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".video-preview-modal").forEach(function (modal) {
        const iframe = modal.querySelector("iframe[data-video-src]");
        if (!iframe) {
            return;
        }

        const videoSrc = iframe.dataset.videoSrc || iframe.getAttribute("src") || "";
        iframe.dataset.videoSrc = videoSrc;

        modal.addEventListener("show.bs.modal", function () {
            if (!iframe.getAttribute("src")) {
                iframe.setAttribute("src", videoSrc);
            }
        });

        modal.addEventListener("hidden.bs.modal", function () {
            iframe.setAttribute("src", "");
        });
    });

    document.querySelectorAll(".video-status-form").forEach(function (form) {
        const select = form.querySelector(".video-status-select");
        const saveButton = form.querySelector(".video-status-save");
        if (!select || !saveButton) {
            return;
        }

        const initialValue = select.value;

        function syncButtonState() {
            const isChanged = select.value !== initialValue;
            saveButton.classList.toggle("d-none", !isChanged);
            saveButton.disabled = !isChanged;
        }

        syncButtonState();
        select.addEventListener("change", syncButtonState);
    });
});
