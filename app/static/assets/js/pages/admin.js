/**
 * Панель администратора: статистика, фильтры, карточки заявок и смена статусов.
 */
(function () {
  "use strict";

  const PAGE_SIZE = 12;

  const listRoot = document.getElementById("admin-list");
  const filtersForm = document.getElementById("filters-form");
  const alertBox = document.getElementById("admin-alert");
  const pagination = document.getElementById("pagination");
  const pageInfo = document.getElementById("page-info");
  const prevButton = document.getElementById("page-prev");
  const nextButton = document.getElementById("page-next");

  const state = {
    page: 1,
    total: 0,
    filters: {
      status: "all",
      login: "",
      room: "",
      date_from: "",
      date_to: "",
    },
  };

  /**
   * Загружает сводную статистику портала.
   */
  async function loadStats() {
    try {
      const stats = await Api.get("/api/admin/stats");
      App.qsa("[data-stat]").forEach(function (node) {
        const key = node.getAttribute("data-stat");
        node.textContent = Object.prototype.hasOwnProperty.call(stats, key)
          ? String(stats[key])
          : "—";
      });
    } catch (error) {
      App.toast("Не удалось загрузить статистику", "error");
    }
  }

  /**
   * Формирует блок с отзывом о мероприятии.
   *
   * @param {Object} review - Отзыв.
   * @returns {string} HTML-разметка.
   */
  function renderReview(review) {
    if (!review) {
      return "";
    }

    return (
      '<div class="review" style="margin-top: 14px">' +
      '<div class="review__head"><strong>Отзыв участника</strong>' +
      App.renderStars(review.rating) +
      "</div>" +
      '<p class="review__text">' +
      App.escapeHtml(review.comment || "Без комментария") +
      "</p>" +
      '<span class="text-muted">Опубликован ' +
      App.formatDateTime(review.created_at) +
      "</span></div>"
    );
  }

  /**
   * Формирует список доступных переходов статуса.
   *
   * @param {string} current - Текущий статус.
   * @returns {string} HTML-разметка опций.
   */
  function renderStatusOptions(current) {
    const allowed = App.STATUS_TRANSITIONS[current] || [];
    if (!allowed.length) {
      return "";
    }

    return allowed
      .map(function (status) {
        return (
          '<option value="' +
          status +
          '">' +
          App.STATUS_LABELS[status] +
          "</option>"
        );
      })
      .join("");
  }

  /**
   * Создаёт карточку заявки для администратора.
   *
   * @param {Object} booking - Заявка.
   * @returns {HTMLElement} Элемент карточки.
   */
  function renderBookingCard(booking) {
    const article = document.createElement("article");
    article.className = "card card--hover reveal";
    article.setAttribute("data-booking-id", String(booking.id));

    const applicant = booking.applicant || {};
    const transitions = renderStatusOptions(booking.status);

    article.innerHTML =
      '<div class="card__header">' +
      '<div class="booking-card__title">' +
      "<strong>Заявка № " +
      booking.id +
      "</strong>" +
      '<span class="text-muted">Подана ' +
      App.formatDateTime(booking.created_at) +
      "</span>" +
      "</div>" +
      '<span class="badge badge--' +
      booking.status +
      '">' +
      App.escapeHtml(booking.status_label) +
      "</span>" +
      "</div>" +
      '<div class="card__body">' +
      '<div class="applicant">' +
      "<span>Заявитель<strong>" +
      App.escapeHtml(applicant.full_name || "—") +
      "</strong></span>" +
      "<span>Логин<strong>" +
      App.escapeHtml(applicant.login || "—") +
      "</strong></span>" +
      "<span>Телефон<strong>" +
      App.escapeHtml(applicant.phone || "—") +
      "</strong></span>" +
      "<span>Электронная почта<strong>" +
      App.escapeHtml(applicant.email || "—") +
      "</strong></span>" +
      "</div>" +
      '<dl class="admin-card__grid">' +
      '<div class="detail"><dt>Помещение</dt><dd>' +
      App.escapeHtml(booking.room_name) +
      (booking.room_kind_label
        ? ' <span class="text-muted">' + App.escapeHtml(booking.room_kind_label) + "</span>"
        : "") +
      "</dd></div>" +
      '<div class="detail"><dt>Дата и время</dt><dd>' +
      App.formatDate(booking.event_date) +
      ", " +
      App.formatTime(booking.start_time) +
      "</dd></div>" +
      '<div class="detail"><dt>Способ оплаты</dt><dd>' +
      App.escapeHtml(booking.payment_method_label) +
      "</dd></div>" +
      '<div class="detail"><dt>Номер телефона заяввителя</dt><dd>' +
      App.escapeHtml(applicant.phone || "—") +
      "</dd></div>" +
      "</dl>" +
      renderReview(booking.review) +
      "</div>" +
      (transitions
        ? '<div class="card__footer">' +
          '<div class="status-control">' +
          '<label class="visually-hidden" for="status_' +
          booking.id +
          '">Новый статус заявки</label>' +
          '<select class="select" id="status_' +
          booking.id +
          '" data-status-select="' +
          booking.id +
          '">' +
          '<option value="">— выбрать новый статус —</option>' +
          transitions +
          "</select>" +
          '<button class="btn btn--primary btn--sm" type="button" data-status-save="' +
          booking.id +
          '" disabled>Сохранить статус</button>' +
          "</div></div>"
        : '<div class="card__footer"><span class="text-muted">Финальный статус — заявка закрыта.</span></div>');

    return article;
  }

  /**
   * Привязывает обработчики смены статуса к карточкам.
   */
  function bindStatusControls() {
    App.qsa("[data-status-select]", listRoot).forEach(function (select) {
      select.addEventListener("change", function () {
        const id = select.getAttribute("data-status-select");
        const saveButton = listRoot.querySelector('[data-status-save="' + id + '"]');
        saveButton.disabled = !select.value;
      });
    });

    App.qsa("[data-status-save]", listRoot).forEach(function (button) {
      button.addEventListener("click", async function () {
        const id = button.getAttribute("data-status-save");
        const select = listRoot.querySelector('[data-status-select="' + id + '"]');
        if (!select.value) {
          return;
        }

        App.setLoading(button, true);
        try {
          await Api.patch("/api/admin/bookings/" + id, { status: select.value });
          App.toast(
            "Статус заявки № " + id + " изменён: " + App.STATUS_LABELS[select.value],
            "success"
          );
          await Promise.all([loadBookings(), loadStats()]);
        } catch (error) {
          App.showFormErrors(filtersForm, error.errors, alertBox, error.message);
          App.toast(error.message, "error");
        } finally {
          App.setLoading(button, false);
        }
      });
    });
  }

  /**
   * Обновляет блок пагинации.
   */
  function renderPagination() {
    const pages = Math.max(Math.ceil(state.total / PAGE_SIZE), 1);
    pagination.hidden = state.total <= PAGE_SIZE;

    pageInfo.textContent =
      "Страница " + state.page + " из " + pages + " · заявок: " + state.total;
    prevButton.disabled = state.page <= 1;
    nextButton.disabled = state.page >= pages;
  }

  /**
   * Загружает заявки с учётом фильтров и текущей страницы.
   */
  async function loadBookings() {
    if (!listRoot) {
      return;
    }

    try {
      const data = await Api.get("/api/admin/bookings", {
        status: state.filters.status,
        login: state.filters.login,
        room: state.filters.room,
        date_from: state.filters.date_from,
        date_to: state.filters.date_to,
        page: state.page,
        page_size: PAGE_SIZE,
      });

      state.total = data.meta.total;

      if (!data.items.length) {
        listRoot.innerHTML =
          '<div class="empty-state" style="grid-column: 1 / -1">' +
          "<h3>Заявки не найдены</h3>" +
          "<p>Измените параметры фильтрации и повторите попытку.</p></div>";
        pagination.hidden = true;
        return;
      }

      listRoot.innerHTML = "";
      data.items.forEach(function (booking) {
        listRoot.appendChild(renderBookingCard(booking));
      });

      App.qsa(".reveal", listRoot).forEach(function (node) {
        node.classList.add("is-visible");
      });
      bindStatusControls();
      renderPagination();
    } catch (error) {
      listRoot.innerHTML =
        '<div class="empty-state" style="grid-column: 1 / -1">' +
        "<h3>Не удалось загрузить заявки</h3><p>" +
        App.escapeHtml(error.message) +
        "</p></div>";
      pagination.hidden = true;
      if (alertBox) {
        alertBox.textContent = error.message;
        alertBox.classList.add("is-visible");
      }
    }
  }

  /**
   * Считывает значения фильтров из формы.
   */
  function readFilters() {
    state.filters.status = filtersForm.elements.namedItem("status").value || "all";
    state.filters.login = filtersForm.elements.namedItem("login").value.trim();
    state.filters.room = filtersForm.elements.namedItem("room").value.trim();
    state.filters.date_from = filtersForm.elements.namedItem("date_from").value;
    state.filters.date_to = filtersForm.elements.namedItem("date_to").value;
  }

  document.addEventListener("DOMContentLoaded", async function () {
    if (!listRoot) {
      return;
    }

    try {
      await App.requireAuth("admin");
    } catch (error) {
      return;
    }

    filtersForm.addEventListener("submit", function (event) {
      event.preventDefault();
      readFilters();

      if (
        state.filters.date_from &&
        state.filters.date_to &&
        state.filters.date_from > state.filters.date_to
      ) {
        App.showFormErrors(
          filtersForm,
          { date_from: "Дата «от» не может быть позже даты «до»" },
          alertBox,
          "Проверьте правильность заполнения полей"
        );
        return;
      }

      state.page = 1;
      App.clearFormErrors(filtersForm, alertBox);
      loadBookings();
    });

    document.getElementById("filters-reset").addEventListener("click", function () {
      filtersForm.reset();
      filtersForm.elements.namedItem("status").value = "all";
      readFilters();
      state.page = 1;
      App.clearFormErrors(filtersForm, alertBox);
      loadBookings();
    });

    prevButton.addEventListener("click", function () {
      if (state.page > 1) {
        state.page -= 1;
        loadBookings();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });

    nextButton.addEventListener("click", function () {
      const pages = Math.max(Math.ceil(state.total / PAGE_SIZE), 1);
      if (state.page < pages) {
        state.page += 1;
        loadBookings();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    });

    readFilters();
    await Promise.all([loadStats(), loadBookings()]);
  });
})();
