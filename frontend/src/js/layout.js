const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", href: "dashboard.html", icon: "&#9634;" },
  { key: "storage", label: "Storage", href: "storage.html", icon: "&#9707;" },
  { key: "keyvault", label: "Key Vault", href: "keyvault.html", icon: "&#128273;" },
  { key: "iam", label: "Access Control (IAM)", href: "iam.html", icon: "&#128100;" },
];

function renderShell(activeKey) {
  requireAuth();
  const user = getUser();

  document.body.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <span class="logo-mark">IC</span>
          <span>Initech Cloud</span>
        </div>
        <nav>
          ${NAV_ITEMS.map(
            (item) => `<a href="${item.href}" class="${item.key === activeKey ? "active" : ""}">${item.label}</a>`
          ).join("")}
        </nav>
      </aside>
      <div class="main">
        <div class="topbar">
          <div class="search-hint">Subscription: <strong>Initech Cloud - Production</strong></div>
          <div class="user-info">
            <span>${user ? user.display_name : ""}</span>
            <span class="role-badge ${user ? user.role : ""}">${user ? user.role : ""}</span>
            <button class="btn btn-secondary" id="logout-btn">Sign out</button>
          </div>
        </div>
        <div class="content" id="content"></div>
      </div>
    </div>
  `;

  document.getElementById("logout-btn").addEventListener("click", logout);
  return document.getElementById("content");
}
