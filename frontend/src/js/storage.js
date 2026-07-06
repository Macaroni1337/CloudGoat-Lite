const content = renderShell("storage");

content.innerHTML = `
  <h1 class="page-title">Storage Accounts</h1>
  <p class="page-subtitle">Storage accounts, containers and objects.</p>

  <div class="panel">
    <div class="panel-header">Containers</div>
    <div class="panel-body">
      <table id="containers-table">
        <thead>
          <tr><th>Container</th><th>Access level</th><th></th></tr>
        </thead>
        <tbody id="containers-body"><tr><td colspan="3">Loading...</td></tr></tbody>
      </table>
    </div>
  </div>

  <div class="panel" id="objects-panel" style="display:none">
    <div class="panel-header" id="objects-header">Objects</div>
    <div class="panel-body">
      <table>
        <thead><tr><th>Name</th><th>Content type</th><th></th></tr></thead>
        <tbody id="objects-body"></tbody>
      </table>
      <div class="result-box" id="object-content" style="display:none"></div>
    </div>
  </div>
`;

async function loadContainers() {
  const body = document.getElementById("containers-body");
  try {
    const accounts = await apiFetch("/api/storage/accounts");
    let rows = [];
    for (const account of accounts) {
      const containers = await apiFetch(`/api/storage/accounts/${account.id}/containers`);
      for (const c of containers) {
        rows.push(`
          <tr>
            <td>${account.name} / ${c.name}</td>
            <td><span class="badge ${c.public ? "public" : "private"}">${c.public ? "Public read access" : "Private"}</span></td>
            <td><a href="#" data-container="${c.id}" data-name="${c.name}" class="browse-link">Browse objects</a></td>
          </tr>`);
      }
    }
    body.innerHTML = rows.join("") || `<tr><td colspan="3">No containers.</td></tr>`;
    document.querySelectorAll(".browse-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        loadObjects(link.dataset.container, link.dataset.name);
      });
    });
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3">Failed to load: ${err.message}</td></tr>`;
  }
}

async function loadObjects(containerId, containerName) {
  const panel = document.getElementById("objects-panel");
  const header = document.getElementById("objects-header");
  const body = document.getElementById("objects-body");
  const contentBox = document.getElementById("object-content");
  panel.style.display = "block";
  header.textContent = `Objects in ${containerName}`;
  contentBox.style.display = "none";
  body.innerHTML = `<tr><td colspan="3">Loading...</td></tr>`;

  try {
    const objects = await apiFetch(`/api/storage/containers/${containerId}/objects`);
    body.innerHTML = objects
      .map(
        (o) => `
        <tr>
          <td>${o.name}</td>
          <td>${o.content_type}</td>
          <td><a href="#" data-object="${o.id}" class="view-link">View</a></td>
        </tr>`
      )
      .join("") || `<tr><td colspan="3">No objects.</td></tr>`;

    document.querySelectorAll(".view-link").forEach((link) => {
      link.addEventListener("click", async (e) => {
        e.preventDefault();
        contentBox.style.display = "block";
        contentBox.textContent = "Loading...";
        try {
          const obj = await apiFetch(`/api/storage/objects/${link.dataset.object}`);
          contentBox.textContent = obj.content;
        } catch (err) {
          contentBox.textContent = `Error: ${err.message}`;
        }
      });
    });
  } catch (err) {
    body.innerHTML = `<tr><td colspan="3">Failed to load: ${err.message}</td></tr>`;
  }
}

loadContainers();
