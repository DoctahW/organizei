// Investments — Chart component (SVG histórico)
// Exposes: window.renderInvestmentChart, window.initInvestmentCrosshair
(function () {
  "use strict";

  var W = 1000, H = 320;
  var PAD_L = 70, PAD_R = 24, PAD_T = 20, PAD_B = 44;
  var CW = W - PAD_L - PAD_R;
  var CH = H - PAD_T - PAD_B;

  function fmtBR(n) {
    return (
      "R$ " +
      Number(n).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  function fmtBRSimple(n) {
    return Number(n).toLocaleString("pt-BR", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  }

  // ── Catmull-Rom spline ────────────────────────────────────────
  function smoothPath(pts, tension) {
    tension = tension === undefined ? 0.22 : tension;
    if (pts.length === 0) return "";
    if (pts.length === 1) return "M " + pts[0].x + "," + pts[0].y;
    var d = "M " + pts[0].x.toFixed(2) + "," + pts[0].y.toFixed(2);
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[Math.max(i - 1, 0)];
      var p1 = pts[i];
      var p2 = pts[i + 1];
      var p3 = pts[Math.min(i + 2, pts.length - 1)];
      var c1x = p1.x + (p2.x - p0.x) * tension;
      var c1y = p1.y + (p2.y - p0.y) * tension;
      var c2x = p2.x - (p3.x - p1.x) * tension;
      var c2y = p2.y - (p3.y - p1.y) * tension;
      d +=
        " C " +
        c1x.toFixed(2) + "," + c1y.toFixed(2) + " " +
        c2x.toFixed(2) + "," + c2y.toFixed(2) + " " +
        p2.x.toFixed(2) + "," + p2.y.toFixed(2);
    }
    return d;
  }

  // ── Build SVG coordinate points from series data ──────────────
  function buildPoints(series, yMin, yMax) {
    if (series.length === 0) return [];
    var n = series.length;
    return series.map(function (d, i) {
      return {
        x: PAD_L + (n === 1 ? CW / 2 : (i / (n - 1)) * CW),
        y: PAD_T + (1 - (d.value - yMin) / (yMax - yMin)) * CH,
        date: d.date,
        value: d.value,
      };
    });
  }

  // ── Render chart into SVG element ─────────────────────────────
  // points: array of { date, valor, custo }
  // Returns ptsValor array for crosshair init.
  function renderInvestmentChart(svgEl, points) {
    svgEl.innerHTML = "";

    var seriesValor = points.map(function (p) { return { date: p.date, value: p.valor }; });
    var seriesCusto = points.map(function (p) { return { date: p.date, value: p.custo }; });

    var allValues = seriesValor
      .map(function (d) { return d.value; })
      .concat(seriesCusto.map(function (d) { return d.value; }));
    var rawMin = Math.min.apply(null, allValues);
    var rawMax = Math.max.apply(null, allValues);
    var range = rawMax - rawMin || 1;
    var yMin = Math.floor((rawMin - range * 0.35) / 100) * 100;
    var yMax = Math.ceil((rawMax + range * 0.35) / 100) * 100;

    var ptsValor = buildPoints(seriesValor, yMin, yMax);
    var ptsCusto = buildPoints(seriesCusto, yMin, yMax);

    if (ptsValor.length === 0) return [];

    var trendColor = "var(--color-primary)";
    var areaColor = "#ffd633";

    svgEl.style.setProperty("--trend-color", "#ffd633");

    var linePath = smoothPath(ptsValor);
    var baseY = PAD_T + CH;
    var areaPath =
      linePath +
      " L " + ptsValor[ptsValor.length - 1].x.toFixed(2) + "," + baseY.toFixed(2) +
      " L " + ptsValor[0].x.toFixed(2) + "," + baseY.toFixed(2) + " Z";
    var custoPath = smoothPath(ptsCusto);

    var gridSvg = "", labelsSvg = "";
    var gridSteps = 4;
    for (var i = 0; i <= gridSteps; i++) {
      var gy = PAD_T + (i / gridSteps) * CH;
      var gv = yMax - (i / gridSteps) * (yMax - yMin);
      gridSvg +=
        '<line class="historico-grid-line" x1="' + PAD_L +
        '" y1="' + gy.toFixed(1) +
        '" x2="' + (W - PAD_R) +
        '" y2="' + gy.toFixed(1) + '"/>';
      labelsSvg +=
        '<text class="historico-axis-text" x="' + (PAD_L - 10) +
        '" y="' + (gy + 4).toFixed(1) +
        '" text-anchor="end">' + fmtBRSimple(gv) + "</text>";
    }

    var xLabelsSvg = "";
    var labelStep = Math.max(1, Math.ceil(ptsValor.length / 6));
    ptsValor.forEach(function (p, idx) {
      if (idx % labelStep === 0 || idx === ptsValor.length - 1) {
        var d = new Date(p.date);
        var label =
          ("0" + d.getDate()).slice(-2) + "/" +
          ("0" + (d.getMonth() + 1)).slice(-2);
        xLabelsSvg +=
          '<text class="historico-axis-text" x="' + p.x.toFixed(1) +
          '" y="' + (baseY + 20).toFixed(1) +
          '" text-anchor="middle">' + label + "</text>";
      }
    });

    var last = ptsValor[ptsValor.length - 1];

    svgEl.innerHTML =
      "<defs>" +
      '<linearGradient id="histAreaGrad" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + areaColor + '" stop-opacity=".35"/>' +
      '<stop offset=".5" stop-color="' + areaColor + '" stop-opacity=".1"/>' +
      '<stop offset="1" stop-color="' + areaColor + '" stop-opacity="0"/>' +
      "</linearGradient>" +
      "</defs>" +
      gridSvg + labelsSvg + xLabelsSvg +
      '<path class="historico-area" d="' + areaPath + '" fill="url(#histAreaGrad)"/>' +
      '<path d="' + custoPath + '" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>' +
      '<path class="historico-line-glow" d="' + linePath + '" stroke="' + trendColor + '"/>' +
      '<path class="historico-line" id="histLineMain" d="' + linePath + '" stroke="' + trendColor + '"/>' +
      '<circle class="historico-dot-pulse" cx="' + last.x.toFixed(2) + '" cy="' + last.y.toFixed(2) + '" r="5"/>' +
      '<circle class="historico-dot" cx="' + last.x.toFixed(2) + '" cy="' + last.y.toFixed(2) + '" r="4.5"/>';

    requestAnimationFrame(function () {
      var path = document.getElementById("histLineMain");
      if (path && path.getTotalLength) {
        path.style.setProperty("--hist-len", path.getTotalLength());
      }
    });

    return ptsValor;
  }

  // ── Crosshair interaction ─────────────────────────────────────
  function initInvestmentCrosshair(ptsValor, svgEl) {
    var wrap = document.querySelector(".historico-chart-wrap");
    var crosshair = document.querySelector(".historico-crosshair");
    var hoverDot = document.querySelector(".historico-hover-dot");
    var tooltip = document.querySelector(".historico-tooltip");
    if (!wrap || !crosshair || !hoverDot || !tooltip) return;

    var ttDate = tooltip.querySelector(".hist-tt-date");
    var ttValue = tooltip.querySelector(".hist-tt-value");

    function onMove(clientX) {
      if (ptsValor.length === 0) return;
      var svgRect = svgEl.getBoundingClientRect();
      var xPx = clientX - svgRect.left;
      var vbX = (xPx / svgRect.width) * W;

      var nearest = ptsValor[0], minD = Infinity;
      ptsValor.forEach(function (p) {
        var d = Math.abs(p.x - vbX);
        if (d < minD) { minD = d; nearest = p; }
      });

      var pxX = (nearest.x / W) * svgRect.width;
      var pxY = (nearest.y / H) * svgRect.height;

      var wrapRect = wrap.getBoundingClientRect();
      var offsetX = svgRect.left - wrapRect.left;
      var offsetY = svgRect.top - wrapRect.top;

      crosshair.style.left = (offsetX + pxX) + "px";
      hoverDot.style.left = (offsetX + pxX) + "px";
      hoverDot.style.top = (offsetY + pxY) + "px";
      tooltip.style.left = (offsetX + pxX) + "px";
      tooltip.style.top = (offsetY + pxY) + "px";

      if (ttDate) ttDate.textContent = nearest.date;
      if (ttValue) ttValue.textContent = fmtBR(nearest.value);
      wrap.classList.add("active");
    }

    wrap.addEventListener("mousemove", function (e) { onMove(e.clientX); });
    wrap.addEventListener("mouseleave", function () { wrap.classList.remove("active"); });
    wrap.addEventListener("touchmove", function (e) {
      e.preventDefault();
      onMove(e.touches[0].clientX);
    }, { passive: false });
    wrap.addEventListener("touchend", function () { wrap.classList.remove("active"); });
  }

  // ── Expose globally ───────────────────────────────────────────
  window.renderInvestmentChart = renderInvestmentChart;
  window.initInvestmentCrosshair = initInvestmentCrosshair;
})();
