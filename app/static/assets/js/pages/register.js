/**
 * Страница регистрации: валидация, маска телефона и создание пользователя.
 */
(function () {
  "use strict";

  const FIELDS = ["login", "password", "full_name", "phone", "email"];

  const form = document.getElementById("register-form");
  const alertBox = document.getElementById("register-alert");
  const submitButton = document.getElementById("register-submit");

  /**
   * Приводит ввод к формату 8(XXX)XXX-XX-XX.
   *
   * @param {string} raw - Введённые символы.
   * @returns {string} Отформатированный телефон.
   */
  function formatPhone(raw) {
    let digits = raw.replace(/\D/g, "");

    if (!digits.length) {
      return "";
    }

    if (digits[0] === "8") {
      digits = digits.slice(1);
    } else if (digits[0] === "7") {
      digits = digits.slice(1);
    } else if (digits.length > 10) {
      digits = digits.slice(-10);
    }

    digits = digits.slice(0, 10);

    let result = "8";
    if (digits.length) {
      result += "(" + digits.slice(0, 3);
    }
    if (digits.length >= 3) {
      result += ")" + digits.slice(3, 6);
    }
    if (digits.length >= 6) {
      result += "-" + digits.slice(6, 8);
    }
    if (digits.length >= 8) {
      result += "-" + digits.slice(8, 10);
    }
    return result;
  }

  /**
   * Проверяет всю форму регистрации.
   *
   * @returns {Object<string,string>} Ошибки по полям.
   */
  function validate() {
    return App.validateForm(form, FIELDS);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const errors = validate();
    if (Object.keys(errors).length) {
      App.showFormErrors(form, errors, alertBox, "Проверьте правильность заполнения полей");
      return;
    }

    await App.submitForm(form, submitButton, async function () {
      const payload = {
        login: form.elements.namedItem("login").value.trim(),
        password: form.elements.namedItem("password").value,
        full_name: form.elements.namedItem("full_name").value.trim(),
        phone: form.elements.namedItem("phone").value.trim(),
        email: form.elements.namedItem("email").value.trim(),
      };

      try {
        const user = await Api.post("/api/auth/register", payload);
        App.user = user;
        App.toast("Пользователь " + user.login + " успешно создан", "success");
        window.location.href = "/bookings.html";
      } catch (error) {
        const fieldErrors = Object.keys(error.errors).length
          ? error.errors
          : {};
        App.showFormErrors(form, fieldErrors, alertBox, error.message);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!form) {
      return;
    }

    form.addEventListener("submit", handleSubmit);

    // Маска ввода телефона.
    const phone = form.elements.namedItem("phone");
    phone.addEventListener("input", function () {
      const formatted = formatPhone(phone.value);
      if (formatted !== phone.value) {
        phone.value = formatted;
      }
    });
    phone.addEventListener("blur", function () {
      if (phone.value && !App.validators.phone(phone.value)) {
        phone.value = formatPhone(phone.value);
      }
    });

    // Ошибка поля снимается, как только пользователь исправил ввод.
    FIELDS.forEach(function (name) {
      const control = form.elements.namedItem(name);
      control.addEventListener("input", function () {
        const wrapper = control.closest(".field");
        if (!wrapper || !wrapper.classList.contains("has-error")) {
          return;
        }
        const message = App.validators[name]
          ? App.validators[name](control.value)
          : null;
        if (control.value.trim() && !message) {
          wrapper.classList.remove("has-error");
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

    // Уже вошедший пользователь не должен попадать на страницу регистрации.
    App.init().then(function (user) {
      if (user) {
        window.location.href =
          user.role === "admin" ? "/admin.html" : "/bookings.html";
      }
    });
  });
})();
