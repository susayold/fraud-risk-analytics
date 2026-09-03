(function () {
  "use strict";
  const charts = new Map();
  const formatMetric = (metric) => {
    if (!metric || metric.status !== "AVAILABLE" || metric.value === null || metric.value === undefined) return metric?.status === "NOT_APPLICABLE" ? "DEFINITION" : "INPUT BLOCKED";
    if (metric.metric_id === "source_fraud_rate") return `${(Number(metric.value) * 100).toFixed(3)}%`;
    return Number(metric.value).toLocaleString("en-US", { maximumFractionDigits: 0 });
  };
  const labelStatus = (status) => status === "LOCKED" ? "LOCKED" : status === "IN_PROGRESS" ? "IN PROGRESS" : status.replaceAll("_", " ");
  const sourceLabel = (chart) => `SOURCE · Part ${chart.source_artifact.match(/part([2-8])/i)?.[1] || ""} · ${chart.source_artifact.split("/").pop()}`;
  const evidenceState = (card, chart) => {
    const canvas = card.querySelector(".chart-canvas");
    canvas.innerHTML = `<div class="chart-empty"><strong>${chart.badge || chart.status.replaceAll("_", " ")}</strong><p>${chart.reason || "Upstream governed evidence is required before this view can render."}</p></div>`;
    card.querySelector(".chart-status").textContent = chart.status.replaceAll("_", " ");
    card.querySelector(".chart-status").classList.add("blocked");
  };
  const seriesData = (chart) => chart.data.map((row) => row[chart.y_field]);
  const categories = (chart) => chart.data.map((row) => row[chart.x_field]);
  const chartOption = (chart) => {
    const isLine = chart.chart_type === "line";
    const isHorizontal = chart.chart_id === "P2" || chart.chart_id === "P4";
    const data = seriesData(chart);
    const labels = categories(chart);
    const option = { animationDuration: 650, animationEasing: "cubicOut", grid: { left: isHorizontal ? 98 : 44, right: 18, top: 18, bottom: isLine ? 42 : 34, containLabel: true }, tooltip: { trigger: "axis", backgroundColor: "#102536", borderColor: "rgba(175,214,231,.2)", textStyle: { color: "#e9f4f5" }, formatter: (items) => { const item = Array.isArray(items) ? items[0] : items; const row = chart.data[item.dataIndex] || {}; return `<b>${item.axisValueLabel || item.name}</b><br>${chart.y_field}: ${typeof item.value === "number" && chart.y_field.includes("rate") ? (item.value * 100).toFixed(3) + "%" : Number(item.value).toLocaleString()}${row.transactions ? `<br>support: ${Number(row.transactions).toLocaleString()}` : ""}${row.fraud_transactions ? `<br>fraud: ${Number(row.fraud_transactions).toLocaleString()}` : ""}`; } }, xAxis: { type: "category", data: labels, axisLabel: { color: "#9fb5bd", fontSize: 10, rotate: isLine ? 35 : 0, interval: isLine ? Math.max(0, Math.ceil(labels.length / 8) - 1) : 0 }, axisLine: { lineStyle: { color: "rgba(175,214,231,.2)" } }, axisTick: { show: false } }, yAxis: { type: "value", axisLabel: { color: "#9fb5bd", fontSize: 10, formatter: (value) => chart.y_field.includes("rate") ? `${(value * 100).toFixed(2)}%` : Number(value).toLocaleString() }, splitLine: { lineStyle: { color: "rgba(175,214,231,.08)" } } }, series: [{ type: isLine ? "line" : "bar", data, smooth: isLine, symbol: isLine ? "circle" : "none", symbolSize: 5, barMaxWidth: 28, itemStyle: { color: chart.chart_id === "D3" || chart.chart_id === "P4" ? "#7fc8ff" : "#65e6ad", borderRadius: isLine ? 0 : [5, 5, 0, 0] }, lineStyle: { color: "#65e6ad", width: 2 }, areaStyle: isLine ? { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(101,230,173,.3)" }, { offset: 1, color: "rgba(101,230,173,0)" }] } } : undefined }] };
    if (isHorizontal) { option.xAxis.type = "value"; option.xAxis.data = undefined; option.yAxis.type = "category"; option.yAxis.data = labels; option.yAxis.axisLabel = { color: "#9fb5bd", fontSize: 10 }; option.series[0] = { ...option.series[0], data: chart.data.map((row) => ({ value: row[chart.y_field], name: row[chart.x_field] })) }; }
    if (chart.chart_id === "D1") { option.xAxis.data = labels; option.yAxis.axisLabel.formatter = (v) => Number(v).toLocaleString(); }
    return option;
  };
  const renderChart = (card, chart) => {
    card.querySelector(".chart-source").textContent = sourceLabel(chart);
    const insight = card.querySelector(".chart-insight"); if (insight) insight.textContent = chart.insight || "";
    if (chart.status !== "AVAILABLE" || !chart.data?.length || typeof window.echarts === "undefined") { evidenceState(card, chart); return; }
    const chartInstance = window.echarts.init(card.querySelector(".chart-canvas"), null, { renderer: "canvas" }); chartInstance.setOption(chartOption(chart)); charts.set(chartInstance, card); card.querySelector(".chart-status").textContent = chart.claim_class; card.querySelector(".chart-alt").textContent = `${chart.title}. ${chart.insight}`;
  };
  Promise.all([fetch("assets/data/part9_summary.json").then((r) => r.json()), fetch("assets/data/part9_charts.json").then((r) => r.json()), fetch("assets/data/part9_status.json").then((r) => r.json())]).then(([summary, chartData, statuses]) => {
    document.querySelectorAll("[data-metric]").forEach((node) => { const metric = summary.metrics[node.dataset.metric]; node.textContent = formatMetric(metric); if (metric) { node.title = `${metric.claim_class} · Part ${metric.source_part} · ${metric.source_artifact}`; } });
    document.querySelectorAll("[data-status-layer]").forEach((node) => { const item = statuses.layers[node.dataset.statusLayer]; if (!item) return; node.textContent = labelStatus(item.status); node.classList.toggle("blocked", item.status === "INPUT_BLOCKED"); node.classList.toggle("progress", item.status === "IN_PROGRESS"); });
    const cards = document.querySelectorAll("[data-chart]"); const observer = new IntersectionObserver((entries, obs) => { entries.forEach((entry) => { if (!entry.isIntersecting) return; const card = entry.target; renderChart(card, chartData[card.dataset.chart]); obs.unobserve(card); }); }, { rootMargin: "180px 0px" }); cards.forEach((card) => observer.observe(card));
    document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => { document.body.classList.toggle("technical-mode", button.dataset.view === "technical"); document.querySelectorAll("[data-view]").forEach((b) => b.classList.toggle("active", b === button)); }));
  }).catch(() => { document.querySelectorAll("[data-metric]").forEach((node) => { node.textContent = "INPUT BLOCKED"; }); });
  document.querySelector(".nav-toggle")?.addEventListener("click", (event) => { const expanded = event.currentTarget.getAttribute("aria-expanded") === "true"; event.currentTarget.setAttribute("aria-expanded", String(!expanded)); document.querySelector(".p9-links")?.classList.toggle("open", !expanded); });
  window.addEventListener("resize", () => charts.forEach((_, chart) => chart.resize()));
})();
