(() => {
  const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
  const RELOGIN_MIN_MS = 30 * 1000;
  const RELOGIN_MAX_MS = 90 * 1000;
  const USERNAME_POOL = ["ana_dev", "carlos", "sql_fan", "db_guest", "nadia", "theo_data", "guest"];
  const DEVICE_POOL = ["web", "mobile", "tablet"];
  const CLIENT_POOL = ["chrome", "firefox", "safari"];
  const LOCALE_POOL = ["pt-BR", "en-US", "es"];
  let token = localStorage.getItem("lab-auth-token") || "";

  window.authFetch = (url, options = {}) => {
    const headers = new Headers(options.headers || {});
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return fetch(url, { ...options, headers, credentials: "same-origin" });
  };

  const storeToken = (nextToken) => {
    token = nextToken || "";
    if (token) {
      localStorage.setItem("lab-auth-token", token);
    } else {
      localStorage.removeItem("lab-auth-token");
    }
  };

  const requestToken = async (url, body) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "same-origin",
    });
    if (!response.ok) {
      return;
    }
    const payload = await response.json();
    storeToken(payload.token);
  };

  const randomChoice = (values) => values[Math.floor(Math.random() * values.length)];
  const randomInterval = () => (
    RELOGIN_MIN_MS + Math.floor(Math.random() * (RELOGIN_MAX_MS - RELOGIN_MIN_MS + 1))
  );
  const randomUsername = () => `${randomChoice(USERNAME_POOL)}_${Math.random().toString(16).slice(2, 8)}`;

  const login = () => {
    const body = { username: randomUsername(), auto: true };
    const variation = Math.floor(Math.random() * 3);

    if (variation === 1) {
      body.device = randomChoice(DEVICE_POOL);
      body.locale = randomChoice(LOCALE_POOL);
    }
    if (variation === 2) {
      body.device = randomChoice(DEVICE_POOL);
      body.client = randomChoice(CLIENT_POOL);
      body.locale = randomChoice(LOCALE_POOL);
    }

    return requestToken("/api/auth/login", body);
  };

  const refresh = () => requestToken("/api/auth/refresh", { token });
  const scheduleRelogin = () => {
    window.setTimeout(() => {
      login().catch(() => {});
      scheduleRelogin();
    }, randomInterval());
  };

  document.addEventListener("DOMContentLoaded", () => {
    login().catch(() => {});
    scheduleRelogin();
    window.setInterval(() => {
      refresh().catch(() => {});
    }, REFRESH_INTERVAL_MS);
  });
})();
