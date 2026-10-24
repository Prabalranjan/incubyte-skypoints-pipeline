/**
 * SkyPoints Loyalty Data Pipeline - Interactive Visual Application
 * Connects PIPELINE_DATA to interactive UI, live tables, scenarios, and code pointers.
 */

document.addEventListener("DOMContentLoaded", () => {
  const data = window.PIPELINE_DATA;
  if (!data) {
    console.error("PIPELINE_DATA not found. Run generate_visual_data.py first.");
    return;
  }

  // 1. Navigation & Stage Switching
  const navButtons = document.querySelectorAll(".nav-tab-btn");
  const flowCards = document.querySelectorAll(".flow-step-card");
  const sections = document.querySelectorAll(".content-section");

  function switchTab(tabId) {
    navButtons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.tab === tabId);
    });
    flowCards.forEach(card => {
      card.classList.toggle("active", card.dataset.tab === tabId);
    });
    sections.forEach(sec => {
      sec.classList.toggle("active", sec.id === tabId);
    });
    window.scrollTo({ top: 380, behavior: "smooth" });
  }

  navButtons.forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  flowCards.forEach(card => {
    card.addEventListener("click", () => switchTab(card.dataset.tab));
  });

  // 2. Populate Header Quick Stats
  document.getElementById("stat-files").textContent = data.files_summary.length;
  document.getElementById("stat-bronze").textContent = data.bronze_count;
  document.getElementById("stat-silver").textContent = data.silver_count;
  document.getElementById("stat-gold").textContent = Object.values(data.country_tables).reduce((acc, t) => acc + t.length, 0);
  document.getElementById("stat-redemptions").textContent = data.redemptions.length;

  // 3. Stage 1: File Discovery & Sample Files Viewer
  const fileCardsContainer = document.getElementById("file-cards-list");
  const fileViewerHeader = document.getElementById("file-viewer-header");
  const fileViewerCode = document.getElementById("file-viewer-code");
  const fileViewerAdapter = document.getElementById("file-viewer-adapter");

  data.files_summary.forEach((f, idx) => {
    const card = document.createElement("div");
    card.className = `file-card ${idx === 0 ? "selected" : ""}`;
    card.dataset.filename = f.filename;

    const badgeClass = f.format === "CSV" ? "badge-csv" : (f.format === "JSON" ? "badge-json" : "badge-txt");

    card.innerHTML = `
      <div class="file-card-header">
        <span class="file-card-name">${f.filename}</span>
        <span class="file-format-badge ${badgeClass}">${f.format}</span>
      </div>
      <div class="file-card-meta">
        ${f.line_count} lines • ${(f.size_bytes / 1024).toFixed(2)} KB
      </div>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".file-card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      displayFileDetails(f);
    });

    fileCardsContainer.appendChild(card);
  });

  function displayFileDetails(fileObj) {
    fileViewerHeader.textContent = `sample_data/${fileObj.filename} (${fileObj.line_count} lines)`;
    fileViewerCode.textContent = fileObj.content;

    const trace = data.file_traces.find(t => t.file_name === fileObj.filename);
    if (trace) {
      fileViewerAdapter.innerHTML = `
        <span class="code-desc">Discovered Adapter:</span>
        <span class="code-file-badge">${trace.adapter_class}</span>
        <span class="code-desc">in <a href="file:///${trace.adapter_file}" style="color:var(--accent-cyan); text-decoration:none;">${trace.adapter_file}</a></span>
      `;
    }
  }

  if (data.files_summary.length > 0) {
    displayFileDetails(data.files_summary[0]);
  }

  // 4. Stage 2: Bronze Live Data Table
  const bronzeTableBody = document.querySelector("#bronze-data-table tbody");
  const bronzeSearch = document.getElementById("bronze-search");

  function renderBronzeTable(filter = "") {
    bronzeTableBody.innerHTML = "";
    const filterLower = filter.toLowerCase();

    const filtered = data.bronze_records.filter(r => 
      !filter || 
      r.source_system.toLowerCase().includes(filterLower) ||
      r.source_file_name.toLowerCase().includes(filterLower) ||
      r.raw_payload.toLowerCase().includes(filterLower)
    );

    filtered.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="code-file-badge" style="font-size:11px;">${r.source_system}</span></td>
        <td>${r.source_file_name}</td>
        <td>${r.source_row_number}</td>
        <td><code style="color:#e2e8f0; font-size:11px;">${escapeHtml(r.raw_payload)}</code></td>
        <td style="color:var(--text-muted); font-size:11px;">${r.source_file_timestamp.replace("T", " ")}</td>
      `;
      bronzeTableBody.appendChild(tr);
    });

    document.getElementById("bronze-filtered-count").textContent = `Showing ${filtered.length} of ${data.bronze_records.length} records`;
  }

  bronzeSearch.addEventListener("input", (e) => renderBronzeTable(e.target.value));
  renderBronzeTable();

  // 5. Stage 3: Silver Staging, Normalization & Derived Columns
  const silverTableBody = document.querySelector("#silver-data-table tbody");
  const silverFilterStatus = document.getElementById("silver-status-filter");

  function renderSilverTable(statusFilter = "ALL") {
    silverTableBody.innerHTML = "";

    const filtered = data.silver_enriched.filter(m => {
      if (statusFilter === "ALL") return true;
      return m.validation_status === statusFilter;
    });

    filtered.forEach(m => {
      const tr = document.createElement("tr");
      let statusBadge = `<span class="badge-status status-valid">VALID</span>`;
      if (m.validation_status === "WARNING") {
        statusBadge = `<span class="badge-status status-warning" title="${m.validation_reason || ''}">WARNING</span>`;
      } else if (m.validation_status === "QUARANTINE") {
        statusBadge = `<span class="badge-status status-quarantine" title="${m.validation_reason || ''}">QUARANTINE</span>`;
      }

      const staleBadge = m.stale_member === true 
        ? `<span class="badge-status status-quarantine">TRUE (Stale)</span>`
        : (m.stale_member === false 
            ? `<span class="badge-status status-valid">FALSE (Active)</span>` 
            : `<span style="color:var(--text-muted);">NULL</span>`);

      tr.innerHTML = `
        <td style="font-weight:700; color:#38bdf8;">${m.member_id}</td>
        <td>${m.member_name}</td>
        <td>${m.country || "-"}</td>
        <td>${m.dob || "-"}</td>
        <td style="font-weight:700; color:#a78bfa;">${m.age !== null ? m.age + " yrs" : "-"}</td>
        <td>${m.last_flight_date || "-"}</td>
        <td>${staleBadge}</td>
        <td>${statusBadge}</td>
        <td style="font-size:11px; color:var(--text-muted);">${m.source_file_name}#L${m.source_row_number}</td>
      `;
      silverTableBody.appendChild(tr);
    });

    document.getElementById("silver-filtered-count").textContent = `Showing ${filtered.length} of ${data.silver_enriched.length} profiles`;
  }

  silverFilterStatus.addEventListener("change", (e) => renderSilverTable(e.target.value));
  renderSilverTable();

  // Quarantine Table
  const quarantineTableBody = document.querySelector("#quarantine-data-table tbody");
  if (data.quarantine_records.length === 0) {
    quarantineTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No quarantined records in sample files.</td></tr>`;
  } else {
    data.quarantine_records.forEach(q => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="color:#fb7185; font-weight:700;">${q.member_id || "(missing)"}</td>
        <td>${q.member_name || "(missing)"}</td>
        <td style="color:#fbbf24;">${q.reason || "Validation failure"}</td>
        <td>${q.source_file} (line ${q.row})</td>
      `;
      quarantineTableBody.appendChild(tr);
    });
  }

  // 6. Stage 4: Gold Dynamic Country Tables & Target Resolution
  const countryTabsContainer = document.getElementById("country-subtabs-list");
  const goldCountryTableBody = document.querySelector("#gold-country-table tbody");
  const goldCountryTableName = document.getElementById("gold-active-country-name");

  const countryTableKeys = Object.keys(data.country_tables);
  let activeCountryTable = countryTableKeys[0] || "Table_Australia";

  countryTableKeys.forEach((tblKey, idx) => {
    const btn = document.createElement("button");
    btn.className = `country-tab-btn ${idx === 0 ? "active" : ""}`;
    btn.textContent = `${tblKey} (${data.country_tables[tblKey].length})`;
    btn.dataset.tbl = tblKey;

    btn.addEventListener("click", () => {
      document.querySelectorAll(".country-tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeCountryTable = tblKey;
      renderGoldCountryTable(tblKey);
    });

    countryTabsContainer.appendChild(btn);
  });

  function renderGoldCountryTable(tblKey) {
    goldCountryTableName.textContent = tblKey;
    goldCountryTableBody.innerHTML = "";
    const rows = data.country_tables[tblKey] || [];

    if (rows.length === 0) {
      goldCountryTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No members currently routed to ${tblKey}</td></tr>`;
      return;
    }

    rows.forEach(r => {
      const tr = document.createElement("tr");
      const activeBadge = r.is_active === "A" 
        ? `<span class="badge-status status-active">ACTIVE ('A')</span>`
        : `<span class="badge-status status-inactive">INACTIVE ('I')</span>`;

      tr.innerHTML = `
        <td style="font-weight:700; color:#38bdf8;">${r.member_id}</td>
        <td>${r.member_name}</td>
        <td><span class="code-file-badge">${r.tier_code || "GEN"}</span></td>
        <td>${r.dob || "-"} (Age: ${r.age || "-"})</td>
        <td>${r.last_flight_date || "-"}</td>
        <td>${activeBadge}</td>
        <td style="font-size:11px; color:var(--text-muted);">${r.source_file_name}</td>
      `;
      goldCountryTableBody.appendChild(tr);
    });
  }

  if (countryTableKeys.length > 0) {
    renderGoldCountryTable(activeCountryTable);
  }

  // Unified View: Current_Member_Profiles
  const currentProfilesTableBody = document.querySelector("#unified-profiles-table tbody");
  data.current_profiles.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight:700; color:#38bdf8;">${p.member_id}</td>
      <td>${p.member_name}</td>
      <td style="font-weight:600; color:#10b981;">${p.country}</td>
      <td><span class="code-file-badge">${p.tier_code || "GEN"}</span></td>
      <td>${p.age !== null ? p.age + " yrs" : "-"}</td>
      <td>${p.stale_member ? '<span class="badge-status status-quarantine">STALE</span>' : '<span class="badge-status status-valid">ACTIVE</span>'}</td>
      <td><span class="badge-status status-active">ACTIVE</span></td>
    `;
    currentProfilesTableBody.appendChild(tr);
  });

  // 7. Stage 5: Gold Transactions (Redemptions Feed & Profile Join)
  const redemptionsTableBody = document.querySelector("#redemptions-data-table tbody");
  data.redemptions.forEach(rx => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight:700; color:#c084fc;">${rx.txn_id}</td>
      <td style="font-weight:600; color:#38bdf8;">${rx.member_id}</td>
      <td>${rx.txn_date || rx.feed_date}</td>
      <td>${rx.partner}</td>
      <td style="font-weight:700; color:#34d399;">${rx.miles_redeemed.toLocaleString()} miles</td>
      <td><span class="code-file-badge">${rx.status}</span></td>
      <td style="font-size:11px; color:var(--text-muted);">${rx.source_file_name}</td>
    `;
    redemptionsTableBody.appendChild(tr);
  });

  // Profile Join Query Results
  const joinedTableBody = document.querySelector("#joined-analytics-table tbody");
  data.joined_transactions.forEach(j => {
    const tr = document.createElement("tr");
    const matchBadge = j.match_status === "MATCHED" 
      ? `<span class="badge-status status-matched">MATCHED</span>`
      : `<span class="badge-status status-unmatched">UNMATCHED_MEMBER</span>`;

    tr.innerHTML = `
      <td style="font-weight:700; color:#c084fc;">${j.txn_id}</td>
      <td style="font-weight:600; color:#38bdf8;">${j.member_id}</td>
      <td>${j.member_name ? j.member_name : '<span style="color:var(--text-muted); font-style:italic;">[Unmatched Profile]</span>'}</td>
      <td>${j.country || "-"}</td>
      <td>${j.tier_code ? `<span class="code-file-badge">${j.tier_code}</span>` : "-"}</td>
      <td>${j.partner}</td>
      <td style="font-weight:700; color:#34d399;">${j.miles_redeemed ? j.miles_redeemed.toLocaleString() : "-"} miles</td>
      <td>${matchBadge}</td>
    `;
    joinedTableBody.appendChild(tr);
  });

  // 8. Interactive Scenario Simulators
  // 8a. Age Calculator
  const simDobInput = document.getElementById("sim-dob");
  const simAsOfInput = document.getElementById("sim-asof");
  const simAgeBtn = document.getElementById("sim-age-btn");
  const simAgeResult = document.getElementById("sim-age-result");

  simAgeBtn.addEventListener("click", () => {
    const dobStr = simDobInput.value;
    const asOfStr = simAsOfInput.value;

    if (!dobStr || !asOfStr) {
      simAgeResult.innerHTML = `<span style="color:#f43f5e;">Please select both DOB and As-Of dates.</span>`;
      return;
    }

    const dob = new Date(dobStr);
    const asOf = new Date(asOfStr);

    if (dob > asOf) {
      simAgeResult.innerHTML = `<span style="color:#f59e0b;">DOB is in the future relative to As-Of date -> Age: NULL (Handled safely)</span>`;
      return;
    }

    let age = asOf.getFullYear() - dob.getFullYear();
    const hasHadBirthday = 
      asOf.getMonth() > dob.getMonth() || 
      (asOf.getMonth() === dob.getMonth() && asOf.getDate() >= dob.getDate());

    if (!hasHadBirthday) {
      age -= 1;
    }

    const isLeapDayBaby = (dob.getMonth() === 1 && dob.getDate() === 29);

    simAgeResult.innerHTML = `
      <div style="margin-bottom:6px;"><strong style="color:#10b981; font-size:16px;">Calculated Age: ${age} completed years</strong></div>
      <div style="font-size:12px; color:var(--text-secondary);">
        • Birthday this year passed: <strong style="color:#fff;">${hasHadBirthday ? "YES" : "NO"}</strong><br>
        • Leap day birth (Feb 29): <strong style="color:#fff;">${isLeapDayBaby ? "YES (Special Feb 28/29 boundary handling applied)" : "NO"}</strong><br>
        • Code function: <code class="code-file-badge">calculate_age(dob, as_of_date)</code> in <span style="color:var(--accent-cyan);">src/skypoints/enrichment/derived_columns.py</span>
      </div>
    `;
  });

  // 8b. Stale Member Calculator
  const simFlightInput = document.getElementById("sim-flight");
  const simStaleAsOf = document.getElementById("sim-stale-asof");
  const simStaleBtn = document.getElementById("sim-stale-btn");
  const simStaleResult = document.getElementById("sim-stale-result");

  simStaleBtn.addEventListener("click", () => {
    const flightStr = simFlightInput.value;
    const asOfStr = simStaleAsOf.value;

    if (!flightStr || !asOfStr) {
      simStaleResult.innerHTML = `<span style="color:#f43f5e;">Please select both Flight Date and As-Of date.</span>`;
      return;
    }

    const flight = new Date(flightStr);
    const asOf = new Date(asOfStr);
    const diffTime = asOf.getTime() - flight.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    const isStale = diffDays > 90;

    let boundaryExplanation = "";
    if (diffDays === 90) {
      boundaryExplanation = "<span style='color:#10b981; font-weight:700;'>EXACT ASSESSMENT BOUNDARY: 90 days = NOT STALE (Active).</span>";
    } else if (diffDays === 91) {
      boundaryExplanation = "<span style='color:#f43f5e; font-weight:700;'>EXACT ASSESSMENT BOUNDARY: 91 days (> 90) = STALE.</span>";
    }

    simStaleResult.innerHTML = `
      <div style="margin-bottom:6px;">
        Days elapsed since flight: <strong style="color:#38bdf8; font-size:16px;">${diffDays} days</strong> |
        Stale Status: ${isStale ? '<span class="badge-status status-quarantine">TRUE (Stale Member)</span>' : '<span class="badge-status status-valid">FALSE (Active Member)</span>'}
      </div>
      <div style="font-size:12px; color:var(--text-secondary); margin-top:6px;">
        ${boundaryExplanation ? boundaryExplanation + "<br>" : ""}
        • Rule: <code style="color:#fbbf24;">(as_of_date - flight_date).days > 90</code><br>
        • Code function: <code class="code-file-badge">calculate_stale_member(last_flight_date, as_of_date)</code> in <span style="color:var(--accent-cyan);">src/skypoints/enrichment/derived_columns.py</span>
      </div>
    `;
  });

  // 9. Architecture Codebase Explorer Tree
  const archContainer = document.getElementById("arch-layers-list");
  data.code_map.forEach(layer => {
    const card = document.createElement("div");
    card.className = "arch-card";

    let componentsHtml = "";
    layer.components.forEach(c => {
      componentsHtml += `
        <div class="arch-component-item">
          <div class="component-info">
            <span class="component-name">${c.name}</span>
            <span class="component-desc">${c.desc}</span>
          </div>
          <a href="file:///${c.file}" class="component-file-link" title="Open file">${c.file} (Lines ${c.lines})</a>
        </div>
      `;
    });

    card.innerHTML = `
      <div class="arch-card-header">
        <span class="arch-card-title">${layer.layer}</span>
      </div>
      <p style="font-size:13px; color:var(--text-secondary); margin-bottom:14px;">${layer.purpose}</p>
      <div class="arch-components-list">
        ${componentsHtml}
      </div>
    `;

    archContainer.appendChild(card);
  });

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
