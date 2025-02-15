document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  var at = document.documentElement.getAttribute("data-layout");
  if (at === "vertical") {
    var isSidebar = document.getElementsByClassName("side-mini-panel");

    if (isSidebar.length > 0) {
      var url = window.location.href;
      var path = url.replace(
        window.location.protocol + "//" + window.location.host + "/",
        ""
      );

      function findMatchingElement() {
        var currentUrl = window.location.href;
        var anchors = document.querySelectorAll("#sidebarnav a");

        for (var i = 0; i < anchors.length; i++) {
          if (anchors[i].href === currentUrl) {
            return anchors[i];
          }
        }
        return null;
      }

      var elements = findMatchingElement();

      if (elements) {
        elements.classList.add("active");
      }

      document.querySelectorAll("#sidebarnav a").forEach(function (link) {
        link.addEventListener("click", function (e) {
          const isActive = this.classList.contains("active");
          const parentUl = this.closest("ul");

          if (!isActive) {
            if (parentUl) {
              parentUl.querySelectorAll("ul").forEach(function (submenu) {
                submenu.classList.remove("in");
              });
              parentUl.querySelectorAll("a").forEach(function (navLink) {
                navLink.classList.remove("active");
              });
            }

            const submenu = this.nextElementSibling;
            if (submenu) {
              submenu.classList.add("in");
            }
            this.classList.add("active");
          } else {
            this.classList.remove("active");
            if (parentUl) {
              parentUl.classList.remove("active");
            }
            const submenu = this.nextElementSibling;
            if (submenu) {
              submenu.classList.remove("in");
            }
          }
        });
      });

      document
        .querySelectorAll("#sidebarnav > li > a.has-arrow")
        .forEach(function (link) {
          link.addEventListener("click", function (e) {
            e.preventDefault();
          });
        });

      if (elements) {
        var closestNav = elements.closest("nav[class^=sidebar-nav]");
        if (closestNav) {
          var menuid = closestNav.id || "menu-right-mini-1";
          var menu = menuid[menuid.length - 1];

          var menuRightMini = document.getElementById("menu-right-mini-" + menu);
          if (menuRightMini) menuRightMini.classList.add("d-block");

          var miniMenu = document.getElementById("mini-" + menu);
          if (miniMenu) miniMenu.classList.add("selected");
        }
      }

      document
        .querySelectorAll("ul#sidebarnav ul li a.active")
        .forEach(function (link) {
          var closestUl = link.closest("ul");
          if (closestUl) {
            closestUl.classList.add("in");
            if (closestUl.parentElement) {
              closestUl.parentElement.classList.add("selected");
            }
          }
        });

      document
        .querySelectorAll(".mini-nav .mini-nav-item")
        .forEach(function (item) {
          item.addEventListener("click", function () {
            var id = this.id;

            document
              .querySelectorAll(".mini-nav .mini-nav-item")
              .forEach(function (navItem) {
                navItem.classList.remove("selected");
              });

            this.classList.add("selected");

            document
              .querySelectorAll(".sidebarmenu nav")
              .forEach(function (nav) {
                nav.classList.remove("d-block");
              });

            var menuRight = document.getElementById("menu-right-" + id);
            if (menuRight) menuRight.classList.add("d-block");

            document.body.setAttribute("data-sidebartype", "full");
          });
        });
    }
  }
});

var currentURL =
  window.location !== window.parent.location
    ? document.referrer
    : document.location.href;

var link = document.getElementById("get-url");

if (link) {
  if (currentURL.includes("/main/index.html")) {
    link.setAttribute("href", "../main/index.html");
  } else if (currentURL.includes("/index.html")) {
    link.setAttribute("href", "./index.html");
  } else {
    link.setAttribute("href", "./");
  }
}
