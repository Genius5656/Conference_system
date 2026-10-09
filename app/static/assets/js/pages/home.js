/**
 * Главная страница портала: каталог помещений.
 */
(function () {
  "use strict";

  /**
   * Создаёт карточку помещения.
   *
   * @param {Object} room - Данные помещения.
   * @param {number} index - Порядковый номер для анимации.
   * @returns {HTMLElement} Элемент карточки.
   */
  function renderRoomCard(room, index) {
    const card = document.createElement("article");
    card.className = "room-card card card--hover reveal";
    card.style.setProperty("--delay", (index % 3) * 0.08 + "s");

    const kindLabel = App.KIND_LABELS[room.kind] || room.kind_label || "";
    const delay = (index % 3) * 0.08;

    card.innerHTML =
      '<div class="room-card__media">' +
      '<img src="' +
      App.escapeHtml(room.image_url) +
      '" alt="' +
      App.escapeHtml(room.name) +
      '" width="1200" height="750" loading="lazy">' +
      '<span class="room-card__kind">' +
      App.escapeHtml(kindLabel) +
      "</span>" +
      "</div>" +
      '<div class="room-card__body">' +
      '<h3 class="room-card__title">' +
      App.escapeHtml(room.name) +
      "</h3>" +
      '<p class="room-card__text">' +
      App.escapeHtml(room.description) +
      "</p>" +
      '<div class="room-card__meta">' +
      '<span class="room-card__capacity">до ' +
      room.capacity +
      " чел.</span>" +
      '<a href="/booking-new.html?room=' +
      room.id +
      '">Выбрать →</a>' +
      "</div>" +
      "</div>";

    card.style.setProperty("--delay", delay + "s");
    return card;
  }

  /**
   * Загружает каталог помещений.
   */
  async function loadRooms() {
    const grid = App.qs("#rooms-grid");
    if (!grid) {
      return;
    }

    try {
      const rooms = await Api.get("/api/rooms");
      if (!rooms.length) {
        grid.innerHTML =
          '<div class="empty-state"><h3>Помещения пока не добавлены</h3>' +
          "<p>Каталог будет наполнен администратором портала.</p></div>";
        return;
      }

      grid.innerHTML = "";
      rooms.forEach(function (room, index) {
        grid.appendChild(renderRoomCard(room, index));
      });

      const factRooms = App.qs("#fact-rooms");
      if (factRooms) {
        factRooms.textContent = String(rooms.length);
      }

      // Показываем карточки сразу после отрисовки.
      window.requestAnimationFrame(function () {
        App.qsa(".reveal", grid).forEach(function (node) {
          node.classList.add("is-visible");
        });
      });
    } catch (error) {
      grid.innerHTML =
        '<div class="empty-state"><h3>Не удалось загрузить каталог</h3>' +
        "<p>" +
        App.escapeHtml(error.message) +
        "</p></div>";
    }
  }

  document.addEventListener("DOMContentLoaded", loadRooms);
})();
