/**
 * Клиентский HTTP-клиент API портала «Конференции.РФ».
 *
 * Модуль инкапсулирует работу с fetch, единообразно преобразует ошибки
 * сервера в объект ApiError и не даст страницам знать о деталях транспорта.
 */
(function (global) {
  "use strict";

  /** Ошибка запроса к API. */
  class ApiError extends Error {
    /**
     * @param {string} message - Человекочитаемое сообщение.
     * @param {number} status - HTTP-код ответа (0 — сетевая ошибка).
     * @param {Object<string,string>} errors - Ошибки по полям формы.
     * @param {string} code - Машинный код ошибки.
     */
    constructor(message, status, errors, code) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.errors = errors || {};
      this.code = code || "error";
    }

    /** Ошибка валидации полей формы. */
    get isValidationError() {
      return this.status === 422 || Object.keys(this.errors).length > 0;
    }
  }

  /**
   * Строит URL с набором параметров запроса.
   *
   * @param {string} path - Путь API.
   * @param {Object} [query] - Параметры запроса (значения null игнорируются).
   * @returns {string} Полный URL.
   */
  function buildUrl(path, query) {
    if (!query) {
      return path;
    }
    const params = new URLSearchParams();
    Object.keys(query).forEach(function (key) {
      const value = query[key];
      if (value !== undefined && value !== null && value !== "") {
        params.append(key, value);
      }
    });
    const queryString = params.toString();
    return queryString ? path + "?" + queryString : path;
  }

  /**
   * Выполняет запрос к API.
   *
   * @param {string} path - Путь API.
   * @param {Object} [options] - Параметры запроса.
   * @param {string} [options.method] - HTTP-метод.
   * @param {Object} [options.body] - Тело запроса (будет сериализовано в JSON).
   * @param {Object} [options.query] - Параметры строки запроса.
   * @returns {Promise<any>} Декодированный JSON-ответ.
   * @throws {ApiError} При ошибке запроса или ошибке сервера.
   */
  async function request(path, options) {
    const settings = options || {};
    const init = {
      method: settings.method || "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    };

    if (settings.body !== undefined && settings.body !== null) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(settings.body);
    }

    let response;
    try {
      response = await fetch(buildUrl(path, settings.query), init);
    } catch (networkError) {
      throw new ApiError(
        "Не удалось связаться с сервером. Проверьте подключение.",
        0,
        {},
        "network_error"
      );
    }

    const raw = await response.text();
    let payload = null;
    if (raw) {
      try {
        payload = JSON.parse(raw);
      } catch (parseError) {
        payload = null;
      }
    }

    if (!response.ok) {
      throw new ApiError(
        (payload && payload.message) || "Ошибка запроса к серверу",
        response.status,
        (payload && payload.errors) || {},
        (payload && payload.code) || "error"
      );
    }

    return payload;
  }

  const Api = {
    ApiError: ApiError,

    request: request,

    /**
     * GET-запрос.
     *
     * @param {string} path - Путь API.
     * @param {Object} [query] - Параметры запроса.
     * @returns {Promise<any>} Ответ сервера.
     */
    get: function (path, query) {
      return request(path, { method: "GET", query: query });
    },

    /**
     * POST-запрос.
     *
     * @param {string} path - Путь API.
     * @param {Object} body - Тело запроса.
     * @returns {Promise<any>} Ответ сервера.
     */
    post: function (path, body) {
      return request(path, { method: "POST", body: body });
    },

    /**
     * PATCH-запрос.
     *
     * @param {string} path - Путь API.
     * @param {Object} body - Тело запроса.
     * @returns {Promise<any>} Ответ сервера.
     */
    patch: function (path, body) {
      return request(path, { method: "PATCH", body: body });
    },

    /**
     * Возвращает текущего пользователя или null, если сессии нет.
     *
     * @returns {Promise<Object|null>} Пользователь либо null.
     */
    me: async function () {
      try {
        return await request("/api/auth/me");
      } catch (error) {
        if (error.status === 401 || error.status === 403) {
          return null;
        }
        throw error;
      }
    },

    /**
     * Проверяет, доступна ли страница без входа в систему.
     *
     * @param {number} status - HTTP-статус ошибки.
     * @returns {boolean} true, если требуется вход.
     */
    isUnauthorized: function (status) {
      return status === 401;
    },
  };

  global.Api = Api;
})(window);
