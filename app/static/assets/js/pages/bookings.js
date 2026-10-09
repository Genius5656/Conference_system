/**
 * Личный кабинет: профиль пользователя, список заявок и форма отзыва.
 */
(function () {
  "use strict";

  const listRoot = document.getElementById("bookings-list");
  const summaryRoot = document.getElementById("summary-chips");

  /**
   * Заполняет блок профиля пользователя.
   *
   * @param {Object} user - Данные пользователя.
   */
  function renderProfile(user) {
    const mapping = {
      "profile-name": user.full_name,
      "profile-login": user.login,
      "profile-phone": user.phone,
      "profile-email": user.email,
    };

    Object.keys(mapping).forEach(function (id) {
      const node = document.getElementById(id);
      if (node) {
        node.textContent = mapping[id];
      }
    });

    const role = document.getElementById("profile-role");
    if (role) {
      role.textContent = user.role_label;
    }
  }

  /**
   * Обновляет сводные счётчики по заявкам.
   *
   * @param {Object[]} bookings - Заявки пользователя.
   */
  function renderSummary(bookings) {
    if (!summaryRoot) {
      return;
    }

    const counts = { total: bookings.length, new: 0, assigned: 0, completed: 0 };
    bookings.forEach(function (booking) {
      counts[booking.status] = (counts[booking.status] || 0) + 1;
    });

    summaryRoot.innerHTML =
      '<span class="chip">Всего заявок: <strong>' +
      counts.total +
      "</strong></span>" +
      '<span class="chip">Новые: <strong>' +
      (counts.new || 0) +
      "</strong></span>" +
      '<span class="chip">Назначены: <strong>' +
      (counts.assigned || 0) +
      "</strong></span>" +
      '<span class="chip">Завершены: <strong>' +
      (counts.completed || 0) +
      "</strong></span>";
  }

  /**
   * Формирует блок отзыва или кнопку его создания.
   *
   * @param {Object} booking - Заявка.
   * @returns {string} HTML-разметка.
   */
  function renderReviewSection(booking) {
    if (booking.review) {
      return (
        '<div class="review">' +
        '<div class="review__head">' +
        "<strong>Ваш отзыв</strong>" +
        App.renderStars(booking.review.rating) +
        "</div>" +
        '<p class="review__text">' +
        App.escapeHtml(booking.review.comment || "Без комментария") +
        "</p>" +
        '<span class="text-muted">Опубликован ' +
        App.formatDateTime(booking.review.created_at) +
        "</span>" +
        "</div>"
      );
    }

    if (booking.can_review) {
      return (
        '<div class="review-form-wrap">' +
        '<button class="btn btn--outline btn--sm" type="button" data-review-toggle="' +
        booking.id +
        '">Оставить отзыв</button>' +
        '<form class="form review-form" data-review-form="' +
        booking.id +
        '" hidden style="margin-top: 14px">' +
        '<div class="field">' +
        '<span class="field__label">Оценка мероприятия<span class="required">*</span></span>' +
        '<div class="rating-picker">' +
        [5, 4, 3, 2, 1]
          .map(function (value) {
            return (
              '<input type="radio" name="rating_' +
              booking.id +
              '" id="rating_' +
              booking.id +
              "_" +
              value +
              '" value="' +
              value +
              '">' +
              '<label for="rating_' +
              booking.id +
              "_" +
              value +
              '" title="' +
              value +
              ' из 5">★</label>'
            );
          })
          .join("") +
        "</div>" +
        '<p class="field__error" data-error-for="rating"></p>' +
        "</div>" +
        '<div class="field">' +
        '<label class="field__label" for="comment_' +
        booking.id +
        '">Комментарий</label>' +
        '<textarea class="textarea" id="comment_' +
        booking.id +
        '" name="comment" maxlength="1000" placeholder="Расскажите о качестве мероприятия"></textarea>' +
        "</div>" +
        '<div class="form-alert" data-review-alert role="alert"></div>' +
        '<div class="status-control">' +
        '<button class="btn btn--primary btn--sm" type="submit">Отправить отзыв</button>' +
        '<button class="btn btn--ghost btn--sm" type="button" data-review-cancel="' +
        booking.id +
        '">Отмена</button>' +
        "</div>" +
        "</form>" +
        "</div>"
      );
    }

    return (
      '<p class="text-muted">Отзыв станет доступен после завершения мероприятия.</p>'
    );
  }

  /**
   * Создаёт карточку заявки.
   *
   * @param {Object} booking - Заявка.
   * @returns {HTMLElement} Элемент карточки.
   */
  function renderBookingCard(booking) {
    const article = document.createElement("article");
    article.className = "booking-card card reveal";
    article.setAttribute("data-booking-id", String(booking.id));

    const roomMeta = booking.room_kind_label
      ? '<span class="text-muted">' + App.escapeHtml(booking.room_kind_label) + "</span>"
      : "";

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
      '<dl class="booking-card__details">' +
      '<div class="detail"><dt>Помещение</dt><dd>' +
      App.escapeHtml(booking.room_name) +
      " " +
      roomMeta +
      "</dd></div>" +
      '<div class="detail"><dt>Дата конференции</dt><dd>' +
      App.formatDate(booking.event_date) +
      "</dd></div>" +
      '<div class="detail"><dt>Время начала</dt><dd>' +
      App.formatTime(booking.start_time) +
      "</dd></div>" +
      '<div class="detail"><dt>Способ оплаты</dt><dd>' +
      App.escapeHtml(booking.payment_method_label) +
      "</dd></div>" +
      "</dl>" +
      '<div style="margin-top: 18px">' +
      renderReviewSection(booking) +
      "</div>" +
      "</div>";

    return article;
  }

  /**
   * Привязывает обработчики к формам отзывов.
   */
  function bindReviewActions() {
    App.qsa("[data-review-toggle]", listRoot).forEach(function (button) {
      button.addEventListener("click", function () {
        const id = button.getAttribute("data-review-toggle");
        const form = listRoot.querySelector('[data-review-form="' + id + '"]');
        button.hidden = true;
        form.hidden = false;
        const rating = form.querySelector('input[type="radio"]');
        if (rating) {
          rating.focus();
        }
      });
    });

    App.qsa("[data-review-cancel]", listRoot).forEach(function (button) {
      button.addEventListener("click", function () {
        const id = button.getAttribute("data-review-cancel");
        const form = listRoot.querySelector('[data-review-form="' + id + '"]');
        const toggle = listRoot.querySelector('[data-review-toggle="' + id + '"]');
        form.hidden = true;
        App.clearFormErrors(form);
        toggle.hidden = false;
      });
    });

    App.qsa("[data-review-form]", listRoot).forEach(function (form) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const bookingId = form.getAttribute("data-review-form");
        const alertBox = form.querySelector("[data-review-alert]");
        const selected = form.querySelector('input[type="radio"]:checked');
        const ratingWrapper = form.querySelector(".rating-picker").closest(".field");
        const ratingError = ratingWrapper.querySelector(".field__error");

        App.clearFormErrors(form, alertBox);
        ratingWrapper.classList.remove("has-error");

        if (!selected) {
          ratingError.textContent = "Выберите оценку мероприятия";
          ratingWrapper.classList.add("has-error");
          return;
        }

        const submitButton = form.querySelector('button[type="submit"]');
        await App.submitForm(form, submitButton, async function () {
          try {
            await Api.post("/api/bookings/" + bookingId + "/reviews", {
              rating: Number(selected.value),
              comment: form.elements.namedItem("comment").value,
            });
            App.toast("Спасибо! Ваш отзыв опубликован", "success");
            await loadBookings();
          } catch (error) {
            App.showFormErrors(form, error.errors, alertBox, error.message);
          }
        });
      });
    });
  }

  /**
   * Загружает и отрисовывает заявки пользователя.
   */
  async function loadBookings() {
    if (!listRoot) {
      return;
    }

    try {
      const bookings = await Api.get("/api/bookings");
      renderSummary(bookings);

      if (!bookings.length) {
        listRoot.innerHTML =
          '<div class="empty-state">' +
          "<h3>Заявок пока нет</h3>" +
          "<p>Сформируйте первую заявку на бронирование помещения.</p>" +
          '<a class="btn btn--primary" href="/booking-new.html">Создать заявку</a>' +
          "</div>";
        return;
      }

      listRoot.innerHTML = "";
      bookings.forEach(function (booking) {
        listRoot.appendChild(renderBookingCard(booking));
      });

      App.qsa(".reveal", listRoot).forEach(function (node) {
        node.classList.add("is-visible");
      });
      bindReviewActions();
    } catch (error) {
      listRoot.innerHTML =
        '<div class="empty-state"><h3>Не удалось загрузить заявки</h3>' +
        "<p>" +
        App.escapeHtml(error.message) +
        "</p></div>";
    }
  }

  document.addEventListener("DOMContentLoaded", async function () {
    if (!listRoot) {
      return;
    }

    try {
      const user = await App.requireAuth();
      renderProfile(user);
      await loadBookings();
    } catch (error) {
      // Перенаправление уже выполнено в requireAuth.
    }
  });
})();
