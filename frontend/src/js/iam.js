const content = renderShell("iam");
const currentUser = getUser();

content.innerHTML = `
  <h1 class="page-title">Access Control (IAM)</h1>
  <p class="page-subtitle">Users, app registrations and role assignments for this subscription.</p>

  <div class="panel">
    <div class="panel-header">Users</div>
    <div class="panel-body">
      <table>
        <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Resource group</th></tr></thead>
        <tbody id="users-body"><tr><td colspan="4">Loading...</td></tr></tbody>
      </table>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">App registrations</div>
    <div class="panel-body">
      <table>
        <thead><tr><th>Name</th><th>Client ID</th><th>Role</th><th>Scope</th><th></th></tr></thead>
        <tbody id="apps-body"><tr><td colspan="5">Loading...</td></tr></tbody>
      </table>
      <div id="logo-forms"></div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">Role assignments</div>
    <div class="panel-body">
      <table>
        <thead><tr><th>Principal</th><th>Type</th><th>Role</th><th>Scope</th></tr></thead>
        <tbody id="assignments-body"><tr><td colspan="4">Loading...</td></tr></tbody>
      </table>
    </div>
  </div>

  <div class="panel" id="assign-role-panel" style="display:none">
    <div class="panel-header">Assign role</div>
    <div class="panel-body">
      <div class="inline-form">
        <input type="text" id="assign-principal-type" placeholder="user or service_principal" />
        <input type="number" id="assign-principal-id" placeholder="Principal ID" />
        <input type="text" id="assign-role" placeholder="Reader / Contributor / Owner" />
        <input type="text" id="assign-scope" placeholder="Scope, e.g. subscription" />
        <button class="btn" id="assign-btn">Assign</button>
      </div>
      <div class="result-box" id="assign-result" style="display:none"></div>
    </div>
  </div>
`;

let usersById = {};
let appsById = {};

async function loadUsers() {
  const body = document.getElementById("users-body");
  const users = await apiFetch("/api/iam/users");
  users.forEach((u) => (usersById[u.id] = u));
  body.innerHTML = users
    .map(
      (u) => `
      <tr>
        <td>${u.display_name}</td>
        <td>${u.email}</td>
        <td><span class="role-badge ${u.role}">${u.role}</span></td>
        <td>${u.resource_group}</td>
      </tr>`
    )
    .join("");
}

async function loadApps() {
  const body = document.getElementById("apps-body");
  const forms = document.getElementById("logo-forms");
  const apps = await apiFetch("/api/iam/app-registrations");
  apps.forEach((a) => (appsById[a.id] = a));
  body.innerHTML = apps
    .map(
      (a) => `
      <tr>
        <td>${a.name}</td>
        <td><code>${a.client_id}</code></td>
        <td><span class="role-badge ${a.role}">${a.role}</span></td>
        <td>${a.scope}</td>
        <td><a href="#" class="logo-toggle" data-app="${a.id}">Update logo</a></td>
      </tr>`
    )
    .join("");

  forms.innerHTML = apps
    .map(
      (a) => `
      <div class="panel logo-form" data-app-panel="${a.id}" style="display:none; margin-top:12px;">
        <div class="panel-header">Update branding logo - ${a.name}</div>
        <div class="panel-body">
          <p class="muted" style="margin-top:0">Import a logo image from a URL. The server fetches this URL on your behalf.</p>
          <div class="inline-form">
            <input type="text" id="logo-url-${a.id}" placeholder="https://example.com/logo.png" style="flex:1" />
            <button class="btn logo-fetch-btn" data-app="${a.id}">Fetch</button>
          </div>
          <div class="result-box" id="logo-result-${a.id}" style="display:none"></div>
        </div>
      </div>`
    )
    .join("");

  document.querySelectorAll(".logo-toggle").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const panel = document.querySelector(`[data-app-panel="${link.dataset.app}"]`);
      panel.style.display = panel.style.display === "none" ? "block" : "none";
    });
  });

  document.querySelectorAll(".logo-fetch-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const appId = btn.dataset.app;
      const url = document.getElementById(`logo-url-${appId}`).value;
      const resultBox = document.getElementById(`logo-result-${appId}`);
      resultBox.style.display = "block";
      resultBox.textContent = "Fetching...";
      try {
        const result = await apiFetch(`/api/iam/app-registrations/${appId}/logo`, {
          method: "POST",
          body: JSON.stringify({ url }),
        });
        resultBox.textContent = JSON.stringify(result, null, 2);
      } catch (err) {
        resultBox.textContent = `Error: ${err.message}`;
      }
    });
  });
}

async function loadAssignments() {
  const body = document.getElementById("assignments-body");
  const assignments = await apiFetch("/api/iam/role-assignments");
  body.innerHTML = assignments
    .map((a) => {
      const principal =
        a.principal_type === "user" ? usersById[a.principal_id] : appsById[a.principal_id];
      const name = principal ? principal.display_name || principal.name : `#${a.principal_id}`;
      return `
        <tr>
          <td>${name}</td>
          <td>${a.principal_type}</td>
          <td><span class="role-badge ${a.role}">${a.role}</span></td>
          <td>${a.scope}</td>
        </tr>`;
    })
    .join("");
}

async function loadAll() {
  await loadUsers();
  await loadApps();
  await loadAssignments();
}

// The "Assign role" form is only shown to users whose current role is Owner
// - this is a UI convenience, not a security boundary. The backend endpoint
// itself performs no such check (see VULNERABILITIES.md V7): anyone with a
// valid token can call POST /api/iam/role-assignments directly.
if (currentUser && currentUser.role === "Owner") {
  document.getElementById("assign-role-panel").style.display = "block";
}

document.getElementById("assign-btn").addEventListener("click", async () => {
  const resultBox = document.getElementById("assign-result");
  resultBox.style.display = "block";
  const body = {
    principal_type: document.getElementById("assign-principal-type").value.trim(),
    principal_id: Number(document.getElementById("assign-principal-id").value),
    role: document.getElementById("assign-role").value.trim(),
    scope: document.getElementById("assign-scope").value.trim(),
  };
  try {
    const result = await apiFetch("/api/iam/role-assignments", {
      method: "POST",
      body: JSON.stringify(body),
    });
    resultBox.textContent = JSON.stringify(result, null, 2);
    loadAll();
  } catch (err) {
    resultBox.textContent = `Error: ${err.message}`;
  }
});

loadAll();
