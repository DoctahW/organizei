// Investments — página de detalhe: modais e chart histórico
(function () {
  "use strict";

  // ── Modais ──────────────────────────────────────────────────────
  const modals = document.querySelectorAll("[data-modal]");
  const openers = document.querySelectorAll("[data-open-modal]");
  const closers = document.querySelectorAll("[data-close-modal]");

  function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.hidden = false;
    document.body.classList.add("modal-open");
  }

  function closeAll() {
    modals.forEach(function (m) {
      m.hidden = true;
    });
    document.body.classList.remove("modal-open");
  }

  openers.forEach(function (btn) {
    btn.addEventListener("click", function () {
      openModal(btn.dataset.openModal);
    });
  });
  closers.forEach(function (btn) {
    btn.addEventListener("click", closeAll);
  });
  modals.forEach(function (m) {
    m.addEventListener("click", function (e) {
      if (e.target === m) closeAll();
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAll();
  });

  // ── Histórico (SVG chart) ───────────────────────────────────────
  const svgEl = document.getElementById("historico-chart");
  const statusEl = document.getElementById("historico-status");
  const legendEl = document.getElementById("historico-legend");

  let loaded = false;

  function fmtBR(n) {
    return (
      "R$ " +
      Number(n).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  function loadHistorico() {
    if (loaded || !svgEl) return;
    statusEl.textContent = "Carregando…";
    fetch(window.INVESTMENT_HISTORY_URL, {
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        return r.ok ? r.json() : Promise.reject(r.statusText);
      })
      .then(function (data) {
        loaded = true;
        if (!data.points || data.points.length === 0) {
          statusEl.textContent = "Sem dados para exibir.";
          return;
        }
        statusEl.textContent = "";
        var pts = window.renderInvestmentChart(svgEl, data.points);
        renderLegend(data);
        window.initInvestmentCrosshair(pts, svgEl);
      })
      .catch(function (err) {
        statusEl.textContent = "Erro ao carregar histórico: " + err;
      });
  }

  function renderLegend(data) {
    var last = data.points[data.points.length - 1];
    var first = data.points[0];
    var variacaoAbs = last.valor - last.custo;
    var variacaoPct = last.custo > 0 ? (variacaoAbs / last.custo) * 100 : 0;
    var sinal = variacaoAbs >= 0 ? "+" : "";
    var variacaoColor = variacaoAbs >= 0 ? "#5cd089" : "#ef6e6e";

    legendEl.innerHTML = "";

    // Custo (muted line)
    var custoItem = document.createElement("span");
    custoItem.className = "legend-item";
    custoItem.innerHTML =
      '<span class="legend-swatch" style="background:rgba(255,255,255,0.35)"></span>' +
      '<span class="legend-label">Custo</span> ' +
      '<span class="legend-value">' + fmtBR(last.custo) + '</span>';
    legendEl.appendChild(custoItem);

    // Valor atual (green line)
    var valorItem = document.createElement("span");
    valorItem.className = "legend-item";
    valorItem.innerHTML =
      '<span class="legend-swatch" style="background:#5cd089"></span>' +
      '<span class="legend-label">Valor atual</span> ' +
      '<span class="legend-value">' + fmtBR(last.valor) + '</span>';
    legendEl.appendChild(valorItem);

    // Variação (colored)
    var variacaoItem = document.createElement("span");
    variacaoItem.className = "legend-item";
    variacaoItem.innerHTML =
      '<span class="legend-swatch" style="background:' + variacaoColor + '"></span>' +
      '<span class="legend-label">Variação</span> ' +
      '<span class="legend-value" style="color:' + variacaoColor + '">' +
      sinal + fmtBR(variacaoAbs) +
      '</span>';
    legendEl.appendChild(variacaoItem);

    // Note
    if (data.tipo === "esparso") {
      var note = document.createElement("p");
      note.className = "historico-note";
      note.textContent =
        "Sem cotação histórica disponível para este ativo — mostrando apenas pontos de movimentação.";
      legendEl.appendChild(note);
    }
  }

  loadHistorico();
})();
