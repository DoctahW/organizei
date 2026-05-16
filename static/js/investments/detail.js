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
    const last = data.points[data.points.length - 1];
    const first = data.points[0];
    const variacaoAbs = last.valor - last.custo;
    const variacaoPct = last.custo > 0 ? (variacaoAbs / last.custo) * 100 : 0;
    const sinal = variacaoAbs >= 0 ? "+" : "";
    legendEl.innerHTML = "";

    const item = function (cor, label, valor) {
      const span = document.createElement("span");
      span.className = "legend-item";
      span.innerHTML =
        '<span class="legend-swatch" style="background:' +
        cor +
        '"></span>' +
        "<strong>" +
        label +
        ":</strong> " +
        valor;
      return span;
    };

    legendEl.appendChild(
      item("rgba(255,255,255,0.5)", "Custo (aplicado)", fmtBR(last.custo)),
    );
    legendEl.appendChild(item("#2ecc71", "Valor atual", fmtBR(last.valor)));
    const variacaoEl = item(
      variacaoAbs >= 0 ? "#2ecc71" : "#e74c3c",
      "Variação",
      sinal + fmtBR(variacaoAbs) + " (" + sinal + variacaoPct.toFixed(2) + "%)",
    );
    legendEl.appendChild(variacaoEl);

    if (data.tipo === "esparso") {
      const note = document.createElement("p");
      note.className = "historico-note";
      note.textContent =
        "Sem cotação histórica disponível para este ativo — mostrando apenas pontos de movimentação.";
      legendEl.appendChild(note);
    } else {
      const note = document.createElement("p");
      note.className = "historico-note";
      note.textContent =
        "Série baseada no PU oficial de venda do Tesouro Direto desde " +
        new Date(first.date).toLocaleDateString("pt-BR") +
        ".";
      legendEl.appendChild(note);
    }
  }

  loadHistorico();
})();
