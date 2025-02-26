function contactForm() {
    var r;
    window.verifyRecaptchaCallback = function (t) {
        $("input[data-recaptcha]").val(t).trigger("change")
    };
    window.expiredRecaptchaCallback = function () {
        $("input[data-recaptcha]").val("").trigger("change")
    };

    $(".dzForm").on("submit", function (t) {
        t.preventDefault();
        $(".dzFormMsg").html('<div class="gen alert dz-alert alert-success">Yuborildi</div>');
        var t = $(this).attr("action"),
            a = $(this).serialize(),
            e = $("input[reCaptchaEnable]").val() == "1";

        $.ajax({
            method: "POST",
            url: t,
            data: a,
            dataType: "json",
            success: function (t) {
                if (t.status == 1) {
                    r = '<div class="gen alert dz-alert alert-success">' + t.msg + "</div>";
                } else {
                    r = '<div class="err alert dz-alert alert-danger">' + t.msg + "</div>";
                }

                $(".dzFormMsg").html(r);

                setTimeout(function () {
                    $(".dzFormMsg .alert").fadeOut(1000, function () {
                        $(this).remove();
                    });
                }, 5000);

                $(".dzForm")[0].reset();

                if (e) grecaptcha.reset();
            }
        });
    });

    $(document).on("submit", ".dzSubscribe", function (t) {
        t.preventDefault();
        var a = $(this),
            t = a.attr("action"),
            e = a.serialize();

        a.addClass("dz-ajax-overlay");

        $.ajax({
            method: "POST",
            url: t,
            data: e,
            dataType: "json",
            success: function (t) {
                a.removeClass("dz-ajax-overlay");

                if (t.status == 1) {
                    r = '<div class="gen alert dz-alert alert-success">' + t.msg + "</div>";
                } else {
                    r = '<div class="err alert dz-alert alert-danger">' + t.msg + "</div>";
                }

                $(".dzSubscribeMsg").html(r);

                setTimeout(function () {
                    $(".dzSubscribeMsg .alert").fadeOut(1000, function () {
                        $(this).remove();
                    });
                }, 5000);

                $(".dzSubscribe")[0].reset();
            }
        });
    });

    $(".dz-load-more").on("click", function (t) {
        t.preventDefault();
        var t = $(this).attr("rel");

        $.ajax({
            method: "POST",
            url: t,
            dataType: "html",
            success: function (t) {
                $(".loadmore-content").append(t);
            }
        });
    });
}

jQuery(document).ready(function () {
    contactForm();
});
