const content = renderShell("keyvault");

content.innerHTML = `
  <h1 class="page-title">Key Vaults</h1>
  <p class="page-subtitle">Secrets are intended to be readable by Owner-role principals only.</p>

  <div class="panel">
    <div class="panel-header" id="vault-header">Secrets</div>
    <div class="panel-body">
      <table>
        <thead><tr><th>Name</th><th>Value</th></tr></thead>
        <tbody id="secrets-body"><tr><td colspan="2">Loading...</td></tr></tbody>
      </table>
    </div>
  </div>
`;

async function loadVault() {
  const header = document.getElementById("vault-header");
  const body = document.getElementById("secrets-body");
  try {
    const vaults = await apiFetch("/api/keyvault/vaults");
    const vault = vaults[0];
    if (!vault) {
      body.innerHTML = `<tr><td colspan="2">No key vaults.</td></tr>`;
      return;
    }
    header.textContent = `Secrets - ${vault.name}`;
    const secrets = await apiFetch(`/api/keyvault/${vault.id}/secrets`);
    body.innerHTML = secrets
      .map((s) => `<tr><td>${s.name}</td><td>${s.value}</td></tr>`)
      .join("") || `<tr><td colspan="2">No secrets.</td></tr>`;
  } catch (err) {
    body.innerHTML = `<tr><td colspan="2">Failed to load: ${err.message}</td></tr>`;
  }
}

loadVault();
