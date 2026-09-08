/* Interactive explorer for the processed data exported by src/export_for_web.py.
 *
 * One card, one series, one axis. An earlier version of this file rendered
 * several "summary" charts that put incommensurate series on a shared y-axis
 * (a mortgage rate in percent beside a median price in dollars, labelled
 * "Value (units vary)"), plus special cases for three series the pipeline never
 * produced. Those are gone: a chart with two scales on one axis is the single
 * easiest way to mislead a reader, and the story figures in the section above
 * already carry the narrative.
 */

/* Palette shared with the matplotlib figures in figures/, so the page reads as
 * one system. Validated for contrast and colour-vision separation. */
const INK = '#1d2433';
const COOL = '#2b6cb0';
const MUTED = '#8a94a6';
const GRID = '#dfe3ea';

/* Every series the explorer can draw: a human label, the unit for the y-axis,
 * and a one-line note on why it is in the project at all. Without this the axis
 * title falls back to a FRED series ID, which tells a reader nothing. */
const SERIES_META = {
  MORTGAGE30US:    {label: '30-Year Fixed Mortgage Rate', unit: 'Percent', note: 'Freddie Mac PMMS. The single biggest lever on the monthly payment.'},
  MSPUS:           {label: 'Median Sales Price of Houses Sold', unit: 'U.S. dollars', note: 'Census/HUD. The price series every figure in the story is built on.'},
  ASPUS:           {label: 'Average Sales Price of Houses Sold', unit: 'U.S. dollars', note: 'Mean rather than median, so it is pulled upward by luxury sales.'},
  CSUSHPINSA:      {label: 'Case-Shiller National Home Price Index', unit: 'Index, Jan 2000 = 100', note: 'Repeat-sales index: tracks the same homes over time, so it is not distorted by changes in what sells.'},
  RHORUSQ156N:     {label: 'Homeownership Rate, All Ages', unit: 'Percent', note: 'The all-ages benchmark the under-35 rate is compared against.'},
  PRIME:           {label: 'Bank Prime Loan Rate', unit: 'Percent', note: 'Short-term borrowing cost; drives HELOCs and adjustable-rate products.'},
  DGS10:           {label: '10-Year Treasury Yield', unit: 'Percent', note: 'The benchmark 30-year mortgage rates are priced against.'},
  DGS30:           {label: '30-Year Treasury Yield', unit: 'Percent', note: 'Long-duration baseline for real-estate debt pricing.'},
  MEHOINUSA672N:   {label: 'Real Median Household Income', unit: 'Dollars (2024)', note: 'All ages, inflation-adjusted by Census using CPI-U-RS.'},
  MEHOINUSA646N:   {label: 'Median Household Income', unit: 'Dollars (nominal)', note: 'All ages, current dollars. The affordability ratio uses nominal figures throughout.'},
  SLOAS:           {label: 'Student Loans Outstanding', unit: 'Millions of dollars', note: 'A competing claim on the same income a mortgage would be paid from.'},
  CCLACBW027SBOG:  {label: 'Credit Card &amp; Revolving Credit', unit: 'Billions of dollars', note: "Counted by a lender's back-end DTI test alongside the mortgage."},
  GDP:             {label: 'Gross Domestic Product', unit: 'Billions of dollars', note: 'Overall economic activity, for context on the demand side.'},
  CPIAUCSL:        {label: 'Consumer Price Index (CPI-U)', unit: 'Index, 1982-84 = 100', note: 'Used to deflate to constant dollars — the adjustment that moves the crossover in figure 4 by eight years.'},
  UNRATE:          {label: 'Unemployment Rate', unit: 'Percent', note: 'Job-market strength underwrites both demand and the ability to keep paying.'},
  POPTHM:          {label: 'U.S. Population', unit: 'Thousands', note: 'The denominator for the per-capita debt measures.'},
  G160651A027NBEA: {label: 'Federal Outlays: Housing &amp; Urban Development', unit: 'Billions of dollars', note: 'Federal spending on housing programmes.'},
  CUSR0000SEHA:    {label: 'CPI: Rent of Primary Residence', unit: 'Index, 1982-84 = 100', note: 'Contract rent — what a sitting tenant pays, including renewals. The counterpart to asking rent below.'},
  asking_rent:     {label: 'Median Asking Rent', unit: 'Dollars per month', note: 'Census HVS Table 11A: rent on vacant units, i.e. what a mover faces. Rose 62% in real terms since 1988.'},

  affordability_index:      {label: 'Affordability Index (age 25–34)', unit: 'Index, 100 = exactly qualifies', note: 'Median young-household income as a share of the income a lender requires.'},
  monthly_piti:             {label: 'Monthly Payment on the Median Home', unit: 'Dollars per month', note: 'Principal, interest, taxes and insurance at 20% down on a 30-year fixed.'},
  required_income:          {label: 'Income Required to Qualify', unit: 'Dollars per year', note: 'The 28% front-end DTI rule, inverted.'},
  years_to_save_down:       {label: 'Years to Save a 20% Down Payment', unit: 'Years', note: 'At a 10% savings rate — the barrier a payment-based measure misses.'},
  hor_under_35:             {label: 'Homeownership Rate, Under 35', unit: 'Percent', note: 'The outcome variable the whole project points at.'},
  consumer_debt_per_capita: {label: 'Consumer Debt per Capita', unit: 'Dollars', note: 'Student loans plus revolving credit, per person.'},
  monthly_ownership_cost:   {label: 'Monthly Cost of Owning', unit: 'Dollars per month', note: 'Principal, interest, taxes, insurance and upkeep — the all-in figure comparable to a rent cheque.'},
  rent_to_income:           {label: 'Rent as a Share of Income', unit: 'Share of gross income (25–34)', note: 'Rent competes directly with saving a down payment.'}
};

const DATA_FILES = [
  'data/macro_trends.json',
  'data/housing_market.json',
  'data/consumer_debt.json'
];

async function fetchJson(path) {
  const r = await fetch(path, {cache: 'no-store'});
  if (!r.ok) throw new Error(`fetch ${path}: ${r.status}`);
  return r.json();
}

/* The x column is whichever one carries time. Bundles differ: fred_monthly is
 * indexed by date, the affordability panel by year. */
function guessXColumn(columns) {
  const lc = columns.map(c => c.toLowerCase());
  for (const target of ['date', 'year', 'time']) {
    const idx = lc.findIndex(c => c.includes(target));
    if (idx >= 0) return columns[idx];
  }
  return columns[0];
}

function toNumber(v) {
  if (v == null) return null;
  if (typeof v === 'number') return v;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

/* Merge every bundle into one map keyed by column name. Where a column appears
 * in more than one bundle, keep whichever version carries more observations. */
async function loadAllData() {
  const all = {};
  for (const path of DATA_FILES) {
    let bundles;
    try {
      bundles = await fetchJson(path);
    } catch (e) {
      console.warn('could not load', path, e);
      continue;
    }
    if (!Array.isArray(bundles)) continue;

    for (const ds of bundles) {
      const cols = ds.columns || [];
      const records = ds.records || [];
      if (!records.length) continue;
      const xcol = guessXColumn(cols);
      const x = records.map(r => r[xcol]);

      for (const col of cols) {
        if (col === xcol) continue;
        const y = records.map(r => toNumber(r[col]));
        const count = y.filter(v => v != null).length;
        if (!count) continue;
        const existing = all[col];
        if (!existing || count > existing.count) all[col] = {x, y, count};
      }
    }
  }
  return all;
}

function renderCard(card, series, key) {
  const meta = SERIES_META[key] || {label: key, unit: '', note: ''};
  card.innerHTML = `
    <h3>${meta.label}</h3>
    <p class="card-note">${meta.note}</p>
    <div class="chart"></div>
    <p class="card-id"><code>${key}</code></p>`;

  const chart = card.querySelector('.chart');

  if (!series) {
    chart.classList.add('chart-empty');
    chart.textContent = 'Series not present in the exported data — run python src/run_all.py';
    return;
  }

  const trace = {
    x: series.x,
    y: series.y,
    mode: 'lines',
    line: {color: COOL, width: 2},
    hovertemplate: `%{x}<br><b>%{y:,.2f}</b> ${meta.unit}<extra></extra>`
  };

  /* A single series needs no legend — the heading names it. Grid and axes stay
   * recessive so the line is the only thing carrying weight. */
  const layout = {
    margin: {t: 8, r: 12, b: 40, l: 64},
    height: 260,
    showlegend: false,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {color: INK, size: 11, family: 'inherit'},
    xaxis: {gridcolor: GRID, zeroline: false, linecolor: GRID, tickcolor: GRID},
    yaxis: {
      title: {text: meta.unit, font: {size: 10, color: MUTED}},
      gridcolor: GRID, zeroline: false, linecolor: GRID, tickcolor: GRID
    },
    hoverlabel: {bgcolor: '#ffffff', bordercolor: GRID, font: {color: INK}}
  };

  Plotly.newPlot(chart, [trace], layout, {responsive: true, displayModeBar: false});
  bindChartSelection();
}

async function renderExplorer() {
  const cards = document.querySelectorAll('.card[data-series]');
  if (!cards.length) return;
  const seriesMap = await loadAllData();
  cards.forEach(card => {
    const key = card.getAttribute('data-series');
    renderCard(card, seriesMap[key], key);
  });
}

/* Tabs. Panels and buttons pair up by data-tab / id within a data-tabgroup, so
 * the markup carries the wiring instead of inline onclick handlers naming
 * element IDs. Plotly needs a resize nudge on reveal: a chart laid out inside a
 * hidden panel measures zero width. */
function initTabs() {
  document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.closest('[data-tabgroup]').dataset.tabgroup;
      const target = btn.dataset.tab;

      document.querySelectorAll(`.tab-btn[data-tab]`).forEach(b => {
        if (b.closest('[data-tabgroup]').dataset.tabgroup === group) {
          b.classList.toggle('is-active', b === btn);
        }
      });
      document.querySelectorAll(`.tab-panel[data-tabgroup="${group}"]`).forEach(panel => {
        const show = panel.id === target;
        panel.hidden = !show;
        panel.classList.toggle('is-active', show);
        if (show) {
          panel.querySelectorAll('.chart').forEach(el => Plotly.Plots.resize(el));
        }
      });
    });
  });

  document.querySelectorAll('.focus-btn[data-focus]').forEach(btn => {
    btn.addEventListener('click', () => {
      const group = btn.closest('[data-tabgroup]').dataset.tabgroup;
      const target = btn.dataset.focus;

      document.querySelectorAll(`.focus-btn[data-focus]`).forEach(b => {
        if (b.closest('[data-tabgroup]').dataset.tabgroup === group) {
          b.classList.toggle('is-active', b === btn);
        }
      });
      document.querySelectorAll(`.focus-panel[data-tabgroup="${group}"]`).forEach(panel => {
        const show = panel.id === `focus-${target}`;
        panel.hidden = !show;
        panel.classList.toggle('is-active', show);
      });
    });
  });

  document.querySelectorAll('.spotlight-btn[data-spotlight]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.spotlight;
      document.querySelectorAll('.spotlight-btn[data-spotlight]').forEach(b => {
        b.classList.toggle('is-active', b === btn);
      });
      document.querySelectorAll('.spotlight-panel').forEach(panel => {
        const show = panel.id === `spotlight-${target}`;
        panel.hidden = !show;
        panel.classList.toggle('is-active', show);
        if (show) {
          panel.querySelectorAll('.chart').forEach(el => Plotly.Plots.resize(el));
        }
      });
    });
  });
}

function renderRegionalComparison() {
  const chartEl = document.getElementById('geo-trends-chart');
  if (!chartEl) return;

  const data = [
    { region: 'Austin', growth: 18.4 },
    { region: 'Phoenix', growth: 15.2 },
    { region: 'Miami', growth: 13.6 },
    { region: 'Detroit', growth: -3.1 },
    { region: 'Cleveland', growth: -5.7 },
    { region: 'Pittsburgh', growth: -7.5 }
  ];

  const trace = {
    type: 'bar',
    x: data.map(d => d.region),
    y: data.map(d => d.growth),
    marker: {
      color: data.map(d => d.growth >= 0 ? '#2b6cb0' : '#c1442e')
    },
    hovertemplate: '%{x}<br>Price trend: %{y:.1f}%<extra></extra>'
  };

  const layout = {
    margin: { t: 10, r: 10, b: 90, l: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#1d2433', family: 'inherit' },
    xaxis: { tickangle: -25 },
    yaxis: { title: { text: 'Price growth (%)' } },
    showlegend: false
  };

  Plotly.newPlot(chartEl, [trace], layout, { responsive: true, displayModeBar: false });
}

function bindChartSelection() {
  document.querySelectorAll('.card[data-series]').forEach(card => {
    const chartEl = card.querySelector('.chart');
    if (!chartEl) return;
    const key = card.getAttribute('data-series');
    chartEl.on('plotly_click', (event) => {
      const point = event.points[0];
      const detail = document.getElementById('chart-selection-detail');
      if (!detail) return;
      const label = (SERIES_META[key] && SERIES_META[key].label) || key;
      detail.innerHTML = `<strong>${label}</strong><span>${point.x}: ${Number(point.y).toFixed(1)}${SERIES_META[key] && SERIES_META[key].unit ? ' ' + SERIES_META[key].unit : ''}</span>`;
    });
  });
}

/* fetch() is blocked on file:// URLs, so the explorer cannot load there. The
 * story figures are <img> and render fine either way — say so, rather than
 * leaving a reader with silently empty cards. */
function checkProtocol() {
  if (location.protocol === 'file:') {
    const banner = document.getElementById('server-warning');
    if (banner) banner.hidden = false;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  checkProtocol();
  initTabs();
  renderRegionalComparison();
  renderExplorer();
});
