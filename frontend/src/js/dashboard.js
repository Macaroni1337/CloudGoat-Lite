const content = renderShell("dashboard");

content.innerHTML = `
  <h1 class="page-title">Resources</h1>
  <p class="page-subtitle">Resources in your assigned resource group.</p>

  <div class="panel">
    <div class="panel-header">My Resources</div>
    <div class="panel-body">
      <div class="cards-grid" id="resource-cards">Loading...</div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">Go to resource by ID</div>
    <div class="panel-body">
      <p class="muted" style="margin-top:0">
        Jump directly to a resource if you already know its ID.
      </p>
      <div class="inline-form">
        <input type="number" id="resource-id-input" placeholder="Resource ID, e.g. 5" min="1" />
        <button class="btn" id="lookup-btn">Look up</button>
      </div>
      <div class="result-box" id="lookup-result" style="display:none"></div>
    </div>
  </div>
`;

async function loadMyResources() {
  const container = document.getElementById("resource-cards");
  try {
    const resources = await apiFetch("/api/resources");
    if (resources.length === 0) {
      container.innerHTML = `<p class="muted">No resources in your resource group.</p>`;
      return;
    }
    container.innerHTML = resources
      .map(
        (r) => `
        <div class="resource-card">
          <div class="r-name">${r.name}</div>
          <div class="r-type">${r.type}</div>
          <div class="r-meta">RG: ${r.resource_group}<br/>Region: ${r.region}<br/>ID: ${r.id}</div>
        </div>`
      )
      .join("");
  } catch (err) {
    container.innerHTML = `<p class="muted">Failed to load resources: ${err.message}</p>`;
  }
}

document.getElementById("lookup-btn").addEventListener("click", async () => {
  const id = document.getElementById("resource-id-input").value;
  const resultBox = document.getElementById("lookup-result");
  resultBox.style.display = "block";
  if (!id) {
    resultBox.textContent = "Enter a resource ID first.";
    return;
  }
  try {
    const resource = await apiFetch(`/api/resources/${id}`);
    resultBox.textContent = JSON.stringify(resource, null, 2);
  } catch (err) {
    resultBox.textContent = `Error: ${err.message}`;
  }
});

loadMyResources();
