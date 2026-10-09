/**
 * Форма формирования заявки: каталог помещений, валидация и отправка.
 */
(function () {
  "use strict";

  const CUSTOM_OPTION = "custom";

  const form = document.getElementById("booking-form");
  const alertBox = document.getElementById("booking-alert");
  const submitButton = document.getElementById("booking-submit");
  const roomSelect = document.getElementById("room_id");
  const customField = document.getElementById("custom-room-field");
  const dateInput = document.getElementById("event_date");

  /**
   * Заполняет выпадающий список помещений данными каталога.
   */
  async function loadRooms() {
    try {
      const rooms = await Api.get("/api/rooms");
      rooms.forEach(function (room) {
        const option = document.createElement("option");
        option.value = String(room.id);
        option.textContent =
          room.name + " (" + (App.KIND_LABELS[room.kind] || room.kind_label) + ")";
        roomSelect.appendChild(option);
      });
    } catch (error) {
      App.toast("Не удалось загрузить каталог помещений", "error");
    }

    const customOption = document.createElement("option");
    customOption.value = CUSTOM_OPTION;
    customOption.textContent = "Другое помещение (ввести название)";
    roomSelect.appendChild(customOption);

    // Предварительный выбор помещения, если пришли из каталога.
    const params = new URLSearchParams(window.location.search);
    const preset = params.get("room");
    if (preset && roomSelect.querySelector('option[value="' + preset + '"]')) {
      roomSelect.value = preset;
    }
  }

  /**
   * Показывает или скрывает поле произвольного названия помещения.
   */
  function toggleCustomRoomField() {
    const isCustom = roomSelect.value === CUSTOM_OPTION;
    customField.hidden = !isCustom;
    if (isCustom) {
      document.getElementById("room_name").focus();
    } else {
      document.getElementById("room_name").value = "";
      customField.classList.remove("has-error");
    }
  }

  /**
   * Устанавливает допустимый диапазон дат (сегодня и позже).
   */
  function setupDateLimits() {
    const today = new Date();
    const iso = [
      today.getFullYear(),
      String(today.getMonth() + 1).padStart(2, "0"),
      String(today.getDate()).padStart(2, "0"),
    ].join("-");
    dateInput.min = iso;
    if (!dateInput.value) {
      dateInput.value = iso;
    }
  }

  /**
   * Проверяет форму заявки.
   *
   * @returns {Object<string,string>} Ошибки по полям.
   */
  function validate() {
    const errors = {};
    const selectedRoom = roomSelect.value;
    const customRoom = document.getElementById("room_name").value;
    const payment = document.getElementById("payment_method").value;

    if (!selectedRoom) {
      errors.room_id = "Выберите помещение из списка";
    } else if (selectedRoom === CUSTOM_OPTION && !customRoom.trim()) {
      errors.room_name = "Введите название помещения";
    }

    if (!dateInput.value) {
      errors.event_date = "Укажите дату начала конференции";
    } else if (dateInput.min && dateInput.value < dateInput.min) {
      errors.event_date = "Дата начала конференции не может быть в прошлом";
    }

    if (!payment) {
      errors.payment_method = "Выберите способ оплаты из списка";
    }

    return errors;
  }

  /**
   * Проверяет произвольное название помещения.
   *
   * @param {string} value - Название.
   * @returns {string|null} Сообщение об ошибке.
   */
  function validateCustomRoom(value) {
    return /^[A-Za-zА-Яа-яЁё0-9\s\-«»"'(),.]{2,120}$/.test(value.trim())
      ? null
      : "Укажите название помещения: буквы, цифры, пробелы и знаки препинания";
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const errors = validate();

    // Дополнительно проверяем название произвольного помещения.
    const roomNameInput = document.getElementById("room_name");
    if (roomSelect.value === CUSTOM_OPTION && roomNameInput.value.trim()) {
      const message = validateCustomRoom(roomNameInput.value);
      if (message) {
        errors.room_name = message;
      }
    }

    if (Object.keys(errors).length) {
      App.showFormErrors(form, errors, alertBox, "Проверьте правильность заполнения полей");
      return;
    }

    const payload = {
      room_id:
        roomSelect.value === CUSTOM_OPTION ? null : Number(roomSelect.value),
      room_name:
        roomSelect.value === CUSTOM_OPTION ? roomNameInput.value.trim() : null,
      event_date: dateInput.value,
      start_time: document.getElementById("start_time").value || null,
      payment_method: document.getElementById("payment_method").value,
    };

    await App.submitForm(form, submitButton, async function () {
      try {
        const booking = await Api.post("/api/bookings", payload);
        App.toast(
          "Заявка № " + booking.id + " отправлена администратору",
          "success"
        );
        window.location.href = "/bookings.html";
      } catch (error) {
        App.showFormErrors(form, error.errors, alertBox, error.message);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", async function () {
    if (!form) {
      return;
    }

    try {
      const user = await App.requireAuth();
      if (user.role === "admin") {
        window.location.href = "/admin.html";
        return;
      }
    } catch (error) {
      return;
    }

    setupDateLimits();
    await loadRooms();
    toggleCustomRoomField();

    roomSelect.addEventListener("change", toggleCustomRoomField);
    form.addEventListener("submit", handleSubmit);

    // Ошибка поля снимается после исправления ввода.
    App.qsa(".input, .select", form).forEach(function (control) {
      control.addEventListener("input", function () {
        const wrapper = control.closest(".field");
        if (wrapper && wrapper.classList.contains("has-error") && control.value) {
          wrapper.classList.remove("has-error");
        }
      });
    });
  });
})();
