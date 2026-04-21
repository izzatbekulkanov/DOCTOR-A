(function () {
  "use strict";

  function formatUzbekPhone(value) {
    let digits = (value || "").replace(/\D/g, "");
    if (digits.startsWith("998")) {
      digits = digits.slice(3);
    }
    digits = digits.slice(0, 9);

    if (!digits.length) {
      return "";
    }

    let formatted = "+998";
    if (digits.length > 0) {
      formatted += " " + digits.slice(0, 2);
    }
    if (digits.length > 2) {
      formatted += " " + digits.slice(2, 5);
    }
    if (digits.length > 5) {
      formatted += " " + digits.slice(5, 7);
    }
    if (digits.length > 7) {
      formatted += " " + digits.slice(7, 9);
    }

    return formatted;
  }

  function normalizeEditorHtml(html) {
    const temp = document.createElement("div");
    temp.innerHTML = html || "";
    const text = (temp.textContent || temp.innerText || "").replace(/\u00a0/g, " ").trim();
    return text ? html.trim() : "";
  }

  function initPhoneMask() {
    const phoneInput = document.getElementById("contact_phone");
    if (!phoneInput) {
      return;
    }

    const syncPhoneValue = function () {
      phoneInput.value = formatUzbekPhone(phoneInput.value);
    };

    syncPhoneValue();
    phoneInput.addEventListener("input", syncPhoneValue);
    phoneInput.addEventListener("focus", function () {
      if (!phoneInput.value) {
        phoneInput.value = "+998 ";
      }
    });
    phoneInput.addEventListener("blur", function () {
      if (phoneInput.value.trim() === "+998") {
        phoneInput.value = "";
      }
    });
  }

  function initEditors(form) {
    if (!window.Quill) {
      return;
    }

    const editorToolbar = [
      ["bold", "italic", "underline", "strike"],
      ["blockquote", "code-block"],
      [{ header: 1 }, { header: 2 }],
      [{ list: "ordered" }, { list: "bullet" }],
      [{ script: "sub" }, { script: "super" }],
      [{ indent: "-1" }, { indent: "+1" }],
      [{ direction: "rtl" }],
      [{ size: ["small", false, "large", "huge"] }],
      [{ header: [1, 2, 3, 4, 5, 6, false] }],
      [{ color: [] }, { background: [] }],
      [{ align: [] }],
      ["clean"],
    ];

    document.querySelectorAll(".rich-editor-input").forEach(function (textarea) {
      const editorId = textarea.dataset.editor;
      const editorElement = document.getElementById(editorId);

      if (!editorElement) {
        return;
      }

      const quill = new Quill(editorElement, {
        theme: "snow",
        modules: {
          toolbar: editorToolbar,
        },
      });

      if (textarea.value.trim()) {
        quill.root.innerHTML = textarea.value;
      }

      const syncValue = function () {
        textarea.value = normalizeEditorHtml(quill.root.innerHTML);
      };

      syncValue();
      quill.on("text-change", syncValue);

      if (form) {
        form.addEventListener("submit", syncValue);
      }
    });
  }

  function revokePreviousUrl(input) {
    if (input.dataset.objectUrl) {
      URL.revokeObjectURL(input.dataset.objectUrl);
      delete input.dataset.objectUrl;
    }
  }

  function initFilePreviews() {
    document.querySelectorAll("[data-preview-target]").forEach(function (input) {
      const preview = document.getElementById(input.dataset.previewTarget);
      if (!preview) {
        return;
      }

      input.addEventListener("change", function () {
        const file = input.files && input.files[0];
        if (!file) {
          return;
        }

        revokePreviousUrl(input);
        const objectUrl = URL.createObjectURL(file);
        input.dataset.objectUrl = objectUrl;

        if (file.type.startsWith("image/")) {
          const image = document.createElement("img");
          image.src = objectUrl;
          image.alt = file.name;
          preview.replaceChildren(image);
          return;
        }

        if (file.type.startsWith("video/")) {
          const video = document.createElement("video");
          const source = document.createElement("source");
          video.controls = true;
          video.muted = true;
          video.preload = "metadata";
          source.src = objectUrl;
          source.type = file.type;
          video.appendChild(source);
          preview.replaceChildren(video);
          return;
        }

        const emptyPreview = document.createElement("div");
        const icon = document.createElement("i");
        const label = document.createElement("span");
        emptyPreview.className = "settings-empty-preview";
        icon.className = "ri-file-line";
        label.textContent = file.name;
        emptyPreview.append(icon, label);
        preview.replaceChildren(emptyPreview);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".settings-form");
    initPhoneMask();
    initEditors(form);
    initFilePreviews();
  });
})();
