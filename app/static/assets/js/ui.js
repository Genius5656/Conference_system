/**
 * Общие UI-компоненты портала: шапка, уведомления, формы, утилиты.
 *
 * Модуль отвечает за отображение состояния авторизации, валидацию на стороне
 * интерфейса (в соответствии с заданием), анимации и пользовательский feedback.
 */
(function (global) {
  "use strict";

  /** Статусы заявок и их отображение в интерфейсе. */
  const STATUS_LABELS = {
    new: "Новая",
    assigned: "Мероприятие назначено",
    completed: "Завершено",
  };

  /** Допустимые переходы между статусами (дублируют правила бэкенда). */
  const STATUS_TRANSITIONS = {
    new: ["assigned", "completed"],
    assigned: ["completed", "new"],
    completed: [],
  };

  /** Способы оплаты заявки. */
  const PAYMENT_LABELS = {
    onsite: "При очном посещении",
    sbp: "Перевод по системе СБП",
  };

  /** Типы помещений. */
  const KIND_LABELS = {
    auditorium: "Аудитория",
    coworking: "Коворкинг",
    cinema: "Кинозал",
  };

  /**
   * Возвращает первый элемент по селектору.
   *
   * @param {string} selector - CSS-селектор.
   * @param {Element} [root] - Корневой элемент поиска.
   * @returns {Element|null} Найденный элемент.
   */
  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }

  /**
   * Возвращает список элементов по селектору.
   *
   * @param {string} selector - CSS-селектор.
   * @param {Element} [root] - Корневой элемент поиска.
   * @returns {Element[]} Найденные элементы.
   */
  function qsa(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  /**
   * Экранирует спецсимволы HTML.
   *
   * @param {string} value - Исходная строка.
   * @returns {string} Безопасная строка.
   */
  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /**
   * Форматирует дату в формате «20 мая 2027 г.».
   *
   * @param {string} value - Дата ISO.
   * @returns {string} Отформатированная дата.
   */
  function formatDate(value) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  /**
   * Форматирует дату и время.
   *
   * @param {string} value - Дата и время ISO.
   * @returns {string} Отформатированная строка.
   */
  function formatDateTime(value) {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return (
      date.toLocaleDateString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }) +
      " " +
      date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })
    );
  }

  /**
   * Форматирует время «ЧЧ:ММ:СС» в «ЧЧ:ММ».
   *
   * @param {string} value - Время.
   * @returns {string} Отформатированное время.
   */
  function formatTime(value) {
    if (!value) {
      return "—";
    }
    return String(value).slice(0, 5);
  }

  /**
   * Возвращает HTML-блок со звёздами оценки.
   *
   * @param {number} rating - Оценка от 1 до 5.
   * @returns {string} HTML-разметка.
   */
  function renderStars(rating) {
    const value = Number(rating) || 0;
    let html = '<span class="stars" aria-label="Оценка ' + value + ' из 5">';
    for (let index = 1; index <= 5; index += 1) {
      html += index <= value ? "★" : "☆";
    }
    return html + "</span>";
  }

  /**
   * Показывает всплывающее уведомление.
   *
   * @param {string} message - Текст сообщения.
   * @param {string} [type] - Тип: success | error | info.
   * @param {number} [duration] - Время показа в мс.
   */
  function toast(message, type, duration) {
    let root = qs("#toast-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "toast-root";
      root.className = "toast-root";
      root.setAttribute("role", "status");
      document.body.appendChild(root);
    }

    const element = document.createElement("div");
    element.className = "toast toast--" + (type || "info");
    element.innerHTML =
      '<span class="toast__text">' +
      escapeHtml(message) +
      '</span><button class="toast__close" type="button" aria-label="Закрыть">&times;</button>';

    const remove = function () {
      if (!element.parentNode) {
        return;
      }
      element.classList.add("is-leaving");
      setTimeout(function () {
        if (element.parentNode) {
          element.parentNode.removeChild(element);
        }
      }, 220);
    };

    element.querySelector(".toast__close").addEventListener("click", remove);
    root.appendChild(element);
    setTimeout(remove, duration || 4200);
  }

  /**
   * Показывает ошибки полей на форме.
   *
   * @param {HTMLFormElement} form - Форма.
   * @param {Object<string,string>} errors - Ошибки по полям.
   * @param {HTMLElement} [alertBox] - Блок общей ошибки формы.
   * @param {string} [message] - Общее сообщение об ошибке.
   */
  function showFormErrors(form, errors, alertBox, message) {
    clearFormErrors(form, alertBox);

    Object.keys(errors || {}).forEach(function (field) {
      const control = form.elements.namedItem(field);
      const wrapper = control ? control.closest(".field") : null;
      const target = wrapper || qs('[data-field="' + field + '"]', form);
      if (target) {
        const errorNode = qs(".field__error", target);
        if (errorNode) {
          errorNode.textContent = errors[field];
        }
        target.classList.add("has-error");
        if (control && control.focus) {
          control.focus({ preventScroll: true });
        }
      }
    });

    if (alertBox && message) {
      alertBox.textContent = message;
      alertBox.classList.add("is-visible");
    }
  }

  /**
   * Сбрасывает отображение ошибок формы.
   *
   * @param {HTMLFormElement} form - Форма.
   * @param {HTMLElement} [alertBox] - Блок общей ошибки формы.
   */
  function clearFormErrors(form, alertBox) {
    qsa(".field.has-error", form).forEach(function (field) {
      field.classList.remove("has-error");
    });
    if (alertBox) {
      alertBox.classList.remove("is-visible");
      alertBox.textContent = "";
    }
  }

  /**
   * Включает индикатор загрузки на кнопке.
   *
   * @param {HTMLButtonElement} button - Кнопка.
   * @param {boolean} loading - Состояние загрузки.
   */
  function setLoading(button, loading) {
    if (!button) {
      return;
    }
    button.disabled = loading;
    button.classList.toggle("is-loading", loading);
  }

  /**
   * Выполняет обработчик отправки формы с блокировкой кнопки.
   *
   * @param {HTMLFormElement} form - Форма.
   * @param {HTMLButtonElement} button - Кнопка отправки.
   * @param {Function} handler - Асинхронный обработчик.
   */
  async function submitForm(form, button, handler) {
    clearFormErrors(form, qs(".form-alert", form));
    setLoading(button, true);
    try {
      await handler();
    } finally {
      setLoading(button, false);
    }
  }

  /**
   * Проверяет обязательное поле и возвращает текст ошибки.
   *
   * @param {HTMLInputElement} input - Поле ввода.
   * @param {string} message - Сообщение об ошибке.
   * @returns {string|null} Сообщение или null.
   */
  function required(input, message) {
    return input.value.trim() ? null : message;
  }

  /** Валидаторы полей регистрации (совпадают с бэкендом). */
  const validators = {
    login: function (value) {
      return /^[A-Za-z0-9]{6,32}$/.test(value.trim())
        ? null
        : "Логин должен содержать только латинские буквы и цифры и быть не короче 6 символов";
    },
    password: function (value) {
      return value.length >= 8 && value.length <= 72
        ? null
        : "Пароль должен содержать от 8 до 72 символов";
    },
    full_name: function (value) {
      const normalized = value.trim().replace(/\s+/g, " ");
      return /^[А-Яа-яЁё]+(?: [А-Яа-яЁё]+)*$/.test(normalized)
        ? null
        : "ФИО может содержать только символы кириллицы и пробелы";
    },
    phone: function (value) {
      return /^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/.test(value.trim())
        ? null
        : "Телефон должен соответствовать формату 8(XXX)XXX-XX-XX";
    },
    email: function (value) {
      return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(value.trim())
        ? null
        : "Введите корректный адрес электронной почты";
    },
  };

  /**
   * Проверяет форму по набору правил.
   *
   * @param {HTMLFormElement} form - Форма.
   * @param {string[]} fields - Имена проверяемых полей.
   * @returns {Object<string,string>} Ошибки по полям.
   */
  function validateForm(form, fields) {
    const errors = {};
    fields.forEach(function (name) {
      const control = form.elements.namedItem(name);
      if (!control) {
        return;
      }
      const check = required(control, "Поле обязательно для заполнения");
      const message = check || (validators[name] ? validators[name](control.value) : null);
      if (message) {
        errors[name] = message;
      }
    });
    return errors;
  }

  /**
   * Отрисовывает состояние авторизации в шапке сайта.
   *
   * @param {Object|null} user - Текущий пользователь.
   */
  function renderAuthState(user) {
    qsa("[data-auth]").forEach(function (element) {
      const scope = element.getAttribute("data-auth");
      let visible = false;
      if (scope === "guest") {
        visible = !user;
      } else if (scope === "user") {
        visible = Boolean(user);
      } else if (scope === "admin") {
        visible = Boolean(user && user.role === "admin");
      }
      element.hidden = !visible;
    });

    const userNode = qs("#nav-user");
    if (userNode) {
      userNode.textContent = user
        ? user.login + (user.role === "admin" ? " · администратор" : "")
        : "";
    }
  }

  /**
   * Инициализирует мобильное меню и подсветку активного пункта.
   */
  function initNavigation() {
    const burger = qs("#burger-btn");
    const nav = qs("#main-nav");

    if (burger && nav) {
      burger.addEventListener("click", function () {
        const open = nav.classList.toggle("is-open");
        burger.setAttribute("aria-expanded", String(open));
      });

      qsa("a", nav).forEach(function (link) {
        link.addEventListener("click", function () {
          nav.classList.remove("is-open");
          burger.setAttribute("aria-expanded", "false");
        });
      });
    }

    const current = window.location.pathname.split("/").pop() || "index.html";
    qsa(".nav__link").forEach(function (link) {
      const target = (link.getAttribute("href") || "").split("/").pop();
      if (target === current) {
        link.classList.add("is-active");
      }
    });

    const header = qs("#site-header");
    if (header) {
      const updateShadow = function () {
        header.classList.toggle("is-scrolled", window.scrollY > 8);
      };
      updateShadow();
      window.addEventListener("scroll", updateShadow, { passive: true });
    }
  }

  /**
   * Подключает анимацию появления блоков при прокрутке.
   */
  function initRevealAnimations() {
    const nodes = qsa(".reveal");
    if (!nodes.length) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (node) {
        node.classList.add("is-visible");
      });
      return;
    }

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    nodes.forEach(function (node) {
      observer.observe(node);
    });

    // Страховка: если наблюдатель по какой-то причине не сработал
    // (например, страница захватывается целиком), контент всё равно
    // становится видимым через короткое время.
    window.setTimeout(function () {
      qsa(".reveal:not(.is-visible)").forEach(function (node) {
        node.classList.add("is-visible");
        observer.unobserve(node);
      });
    }, 2500);
  }

  /**
   * Выполняет выход пользователя из системы.
   *
   * @returns {Promise<void>} Завершение выхода.
   */
  async function logout() {
    try {
      await Api.post("/api/auth/logout", {});
    } catch (error) {
      // Игнорируем: кука удаляется на стороне сервера в любом случае.
    }
    window.location.href = "/index.html";
  }

  const App = {
    user: null,
    STATUS_LABELS: STATUS_LABELS,
    STATUS_TRANSITIONS: STATUS_TRANSITIONS,
    PAYMENT_LABELS: PAYMENT_LABELS,
    KIND_LABELS: KIND_LABELS,
    validators: validators,
    qs: qs,
    qsa: qsa,
    escapeHtml: escapeHtml,
    formatDate: formatDate,
    formatDateTime: formatDateTime,
    formatTime: formatTime,
    renderStars: renderStars,
    toast: toast,
    showFormErrors: showFormErrors,
    clearFormErrors: clearFormErrors,
    setLoading: setLoading,
    submitForm: submitForm,
    validateForm: validateForm,
    logout: logout,

    /**
     * Запрашивает текущего пользователя и готовит шапку сайта.
     *
     * @returns {Promise<Object|null>} Пользователь либо null.
     */
    init: function () {
      if (this._ready) {
        return this._ready;
      }

      const self = this;
      this._ready = Api.me()
        .catch(function () {
          return null;
        })
        .then(function (user) {
          self.user = user;
          renderAuthState(user);
          document.dispatchEvent(
            new CustomEvent("app:auth-ready", { detail: { user: user } })
          );
          return user;
        });
      return this._ready;
    },

    /**
     * Гарантирует авторизацию: при отсутствии сессии перенаправляет на вход.
     *
     * @param {string} [role] - Требуемая роль (user | admin).
     * @returns {Promise<Object>} Пользователь.
     */
    requireAuth: async function (role) {
      const user = await this.init();
      if (!user) {
        const next = encodeURIComponent(
          window.location.pathname + window.location.search
        );
        window.location.href = "/login.html?next=" + next;
        throw new Error("unauthorized");
      }
      if (role === "admin" && user.role !== "admin") {
        window.location.href = "/index.html";
        throw new Error("forbidden");
      }
      return user;
    },
  };

  global.App = App;

  document.addEventListener("DOMContentLoaded", function () {
    initNavigation();
    initRevealAnimations();

    qsa('[data-action="logout"]').forEach(function (button) {
      button.addEventListener("click", function () {
        logout();
      });
    });

    App.init();
  });
})(window);
