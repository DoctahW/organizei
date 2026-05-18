document.addEventListener("DOMContentLoaded", function () {
  const wrapper = document.querySelector(".auth-wrapper");
  if (!wrapper) return;

  const loginPanel = document.getElementById("login-panel");
  const registerPanel = document.getElementById("register-panel");
  const activePanel = wrapper.dataset.activePanel || "login";

  function showPanel(panel) {
    loginPanel.classList.remove("auth-panel--active");
    registerPanel.classList.remove("auth-panel--active");

    if (panel === "register") {
      registerPanel.classList.add("auth-panel--active");
    } else {
      loginPanel.classList.add("auth-panel--active");
    }
  }

  // Toggle links
  wrapper.addEventListener("click", function (e) {
    const toggleRegister = e.target.closest(".js-toggle-register");
    const toggleLogin = e.target.closest(".js-toggle-login");

    if (toggleRegister) {
      e.preventDefault();
      showPanel("register");
    }

    if (toggleLogin) {
      e.preventDefault();
      showPanel("login");
    }
  });

  // Password visibility toggle
  wrapper.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-toggle-password]");
    if (!btn) return;

    const input = btn
      .closest(".auth-field__input-wrap")
      .querySelector("input");

    if (input.type === "password") {
      input.type = "text";
      btn.setAttribute("aria-label", "Ocultar senha");
    } else {
      input.type = "password";
      btn.setAttribute("aria-label", "Mostrar senha");
    }
  });
});
