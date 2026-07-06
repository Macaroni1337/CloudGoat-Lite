document.getElementById("api-host").textContent = window.location.hostname;

// If already logged in, skip straight to the dashboard.
if (getToken()) {
  window.location.href = "dashboard.html";
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const errorBanner = document.getElementById("error-banner");
  errorBanner.style.display = "none";

  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setSession(data.access_token, data.user);
    window.location.href = "dashboard.html";
  } catch (err) {
    errorBanner.textContent = err.message;
    errorBanner.style.display = "block";
  }
});
