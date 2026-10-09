/**
 * Страница авторизации: валидация формы и вход в систему.
 */
(function () {
  "use strict";

  const form = document.getElementById("login-form");
  const alertBox = document.getElementById("login-alert");
  const submitButton = document.getElementById("login-submit");

  /**
   * Проверяет поля формы входа.
   *
   * @returns {Object<string,string>} Ошибки по полям.
   */
  function validate() {
    const errors = {};
    const login = form.elements.namedItem("login");
    const password = form.elements.namedItem("password");

    if (!login.value.trim()) {
      errors.login = "Поле обязательно для заполнения";
    }

    if (!password.value) {
      errors.password = "Поле обязательно для заполнения";
    }

    return errors;
  }

  /**
   * Определяет адрес, на который нужно вернуть пользователя после входа.
   *
   * @returns {string} Адрес для перенаправления.
   */
  function resolveRedirect() {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");

    if (next && next.startsWith("/") && !next.startsWith("//")) {
      return next;
    }

    if (App.user && App.user.role === "admin") {
      return "/admin.html";
    }
    return "/bookings.html";
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const errors = validate();
    if (Object.keys(errors).length) {
      App.showFormErrors(form, errors, alertBox, "Проверьте правильность заполнения полей");
      return;
    }

    await App.submitForm(form, submitButton, async function () {
      try {
        const user = await Api.post("/api/auth/login", {
          login: form.elements.namedItem("login").value.trim(),
          password: form.elements.namedItem("password").value,
        });

        App.user = user;
        App.toast("Добро пожаловать, " + user.full_name + "!", "success");
        window.location.href = resolveRedirect();
      } catch (error) {
        const fieldErrors = Object.keys(error.errors).length
          ? error.errors
          : { login: error.message, password: error.message };
        App.showFormErrors(form, fieldErrors, alertBox, error.message);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!form) {
      return;
    }

    form.addEventListener("submit", handleSubmit);

    // Живая валидация после первого исправления ошибки.
    ["login", "password"].forEach(function (name) {
      const control = form.elements.namedItem(name);
      control.addEventListener("input", function () {
        const wrapper = control.closest(".field");
        if (wrapper && wrapper.classList.contains("has-error")) {
          const message = App.validators[name]
            ? App.validators[name](control.value)
            : null;
          if (control.value.trim() && !message) {
            wrapper.classList.remove("has-error");
          }
        }
      });
    });

    // Показ/скрытие пароля.
    App.qsa("[data-toggle-password]").forEach(function (button) {
      button.addEventListener("click", function () {
        const input = document.getElementById(button.getAttribute("data-toggle-password"));
        const visible = input.type === "text";
        input.type = visible ? "password" : "text";
        button.textContent = visible ? "Показать" : "Скрыть";
      });
    });

    // Если пользователь уже вошёл — сразу перенаправляем.
    App.init().then(function (user) {
      if (user) {
        window.location.href = resolveRedirect();
      }
    });
  });
})();
