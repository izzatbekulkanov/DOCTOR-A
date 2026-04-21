(function () {
    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function ensureToastStack() {
        var stack = document.querySelector(".bot-toast-stack");
        if (!stack) {
            stack = document.createElement("div");
            stack.className = "bot-toast-stack";
            document.body.appendChild(stack);
        }
        return stack;
    }

    function showToast(message, type) {
        var stack = ensureToastStack();
        var toast = document.createElement("div");
        toast.className = "bot-toast is-" + (type || "success");
        toast.textContent = message || "Amal bajarildi.";
        stack.appendChild(toast);
        window.setTimeout(function () {
            toast.remove();
        }, 4200);
    }

    function firstAlertFrom(doc) {
        var alert = doc.querySelector(".app-body .alert");
        if (!alert) {
            return { message: "Amal bajarildi.", type: "success" };
        }
        var message = alert.textContent.replace(/\s+/g, " ").trim();
        var type = "success";
        if (alert.classList.contains("alert-danger")) {
            type = "error";
        } else if (alert.classList.contains("alert-warning")) {
            type = "warning";
        } else if (alert.classList.contains("alert-info")) {
            type = "info";
        }
        return { message: message, type: type };
    }

    function replaceAppBody(html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, "text/html");
        var nextBody = doc.querySelector(".app-body");
        var currentBody = document.querySelector(".app-body");
        if (nextBody && currentBody) {
            currentBody.replaceWith(nextBody);
        }
        return firstAlertFrom(doc);
    }

    function formatDateTime(value) {
        if (!value || value === "-") {
            return "-";
        }
        var date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return date.toLocaleString("uz-UZ", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });
    }

    function setText(selector, text) {
        var element = document.querySelector(selector);
        if (element) {
            element.textContent = text || "-";
        }
    }

    function updateWorkerStatus() {
        var panel = document.querySelector(".bot-worker-panel");
        if (!panel) {
            return;
        }

        var url = panel.getAttribute("data-worker-status-url");
        if (!url) {
            return;
        }

        fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (payload) {
                if (!payload || !payload.ok) {
                    return;
                }

                var dot = document.querySelector("[data-worker-status-dot]");
                if (dot) {
                    dot.classList.remove("is-online", "is-offline", "is-warning");
                    dot.classList.add(payload.is_running ? "is-online" : "is-offline");
                }

                setText("[data-worker-status-label]", payload.is_running ? "Ishlayapti" : "To'xtagan");
                setText("[data-worker-pids]", payload.pids && payload.pids.length ? payload.pids.join(", ") : "-");
                setText("[data-worker-period]", payload.period_label || "Ishlamayapti");
                setText("[data-worker-last-poll]", formatDateTime(payload.last_polling_label));
            })
            .catch(function () {
                return null;
            });
    }

    document.addEventListener("submit", function (event) {
        var form = event.target;
        var appBody = form.closest(".bot-admin");
        if (!appBody) {
            return;
        }

        event.preventDefault();
        var method = (form.getAttribute("method") || "GET").toUpperCase();
        var url = form.getAttribute("action") || window.location.href;
        var options = {
            method: method,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        };

        if (method === "GET") {
            var params = new URLSearchParams(new FormData(form));
            url = url + (url.indexOf("?") === -1 ? "?" : "&") + params.toString();
        } else {
            options.body = new FormData(form);
            options.headers["X-CSRFToken"] = getCookie("csrftoken");
        }

        form.classList.add("is-loading");
        fetch(url, options)
            .then(function (response) {
                return response.text();
            })
            .then(function (html) {
                var alert = replaceAppBody(html);
                showToast(alert.message, alert.type);
                updateWorkerStatus();
            })
            .catch(function () {
                showToast("Amal bajarilmadi. Tarmoq yoki server xatosi.", "error");
            })
            .finally(function () {
                form.classList.remove("is-loading");
            });
    });

    updateWorkerStatus();
    window.setInterval(updateWorkerStatus, 5000);
})();
