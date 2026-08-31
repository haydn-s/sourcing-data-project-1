async function fetchJson(path) {
  const r = await fetch(path, {cache: 'no-store'});
  if (!r.ok) throw new Error(`fetch ${path}: ${r.status}`);
  return r.json();
}

function guessXColumn(columns) {
  const lc = columns.map(c => c.toLowerCase());
  for (const target of ['date', 'year', 'time']) {
    const idx = lc.findIndex(c => c.includes(target));
    if (idx >= 0) return columns[idx];
  }
  return columns[0];
}

function findKeysByKeywords(seriesMap, keywords){
  const keys = Object.keys(seriesMap || {});
  const found = [];
  const lower = keywords.map(k => k.toLowerCase());
  for (const k of keys){
    const kl = k.toLowerCase();
    for (const kw of lower){
      if (kl.includes(kw)){
        found.push(k);
        break;
      }
    }
  }
  return found;
}

function renderAgeTable(card, d, fieldName){
  // d: {x:[], y:[]}
  const wrap = card.querySelector('.age-table-wrap');
  const filterInput = card.querySelector('.age-filter');
  const rowsSelect = card.querySelector('.age-rows');
  if (!wrap) return;
  function buildTable(){
    const filter = (filterInput && filterInput.value || '').toLowerCase().trim();
    const rowsPer = Number(rowsSelect.value);
    // build rows array
    const rows = [];
    for (let i=0;i<d.x.length;i++){
      const x = d.x[i];
      const y = d.y[i];
      const yStr = (y==null)?'':String(y);
      const rowText = `${x} ${yStr}`.toLowerCase();
      if (filter && !rowText.includes(filter)) continue;
      rows.push({x,y});
    }
    // slice
    const display = (rowsPer>0) ? rows.slice(0, rowsPer) : rows;
    // render table
    wrap.innerHTML = '';
    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    const thead = document.createElement('thead');
    thead.innerHTML = `<tr><th style="text-align:left;padding:6px;border-bottom:1px solid #ddd;">Date</th><th style="text-align:right;padding:6px;border-bottom:1px solid #ddd;">Age</th></tr>`;
    table.appendChild(thead);
    const tb = document.createElement('tbody');
    for (const r of display){
      const tr = document.createElement('tr');
      tr.innerHTML = `<td style="padding:6px;border-bottom:1px solid #f2f2f2;">${r.x}</td><td style="padding:6px;border-bottom:1px solid #f2f2f2;text-align:right;">${r.y==null?'':r.y}</td>`;
      tb.appendChild(tr);
    }
    table.appendChild(tb);
    wrap.appendChild(table);
  }
  // attach handlers
  if (filterInput) filterInput.addEventListener('input', buildTable);
  if (rowsSelect) rowsSelect.addEventListener('change', buildTable);
  buildTable();
}

function toNumber(v){
  if (v == null) return null;
  if (typeof v === 'number') return v;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function renderSeriesInCard(card, seriesData, seriesName){
  const plotDiv = document.createElement('div');
  plotDiv.className = 'plot';
  card.appendChild(plotDiv);
  const trace = {
    x: seriesData.x,
    y: seriesData.y,
    name: seriesName,
    mode: 'lines+markers'
  };
  const titleText = (card.querySelector('h3') || {}).textContent || seriesName;
  const layout = {margin:{t:40}, title:{text: titleText}, legend:{orientation:'h'}, xaxis:{title:'Date'}, yaxis:{title: seriesName}};
  Plotly.newPlot(plotDiv, [trace], layout);
}

async function loadAllData(){
  const paths = ['data/macro_trends.json','data/housing_market.json','data/consumer_debt.json'];
  const all = {};
  for (const p of paths){
    try{
      const arr = await fetchJson(p);
      if (!Array.isArray(arr)) continue;
      for (const ds of arr){
        const cols = ds.columns || [];
        const records = ds.records || [];
        if (records.length === 0) continue;
        const xcol = guessXColumn(cols);
        const xvals = records.map(r => r[xcol]);
        for (const col of cols){
          if (col === xcol) continue;
          const yvals = records.map(r => toNumber(r[col]));
          // prefer longer series when overwriting
          const existing = all[col];
          if (!existing || (yvals.filter(v=>v!=null).length > existing.y.filter(v=>v!=null).length)){
            all[col] = {x: xvals, y: yvals};
          }
        }
      }
    }catch(e){
      console.warn('failed loading', p, e);
    }
  }
  return all;
}

async function refreshAll(){
  const seriesMap = await loadAllData();

  // For each card that declares a data-series attribute, attempt to render that series
  document.querySelectorAll('.card[data-series]').forEach(card => {
    const seriesName = card.getAttribute('data-series');
    let seriesData = seriesMap[seriesName];
    // fallback: case-insensitive or substring matches
    if (!seriesData) {
      const keyLower = seriesName.toLowerCase();
      const foundKey = Object.keys(seriesMap).find(k => k.toLowerCase() === keyLower) ||
        Object.keys(seriesMap).find(k => k.toLowerCase().includes(keyLower)) ||
        Object.keys(seriesMap).find(k => keyLower.includes(k.toLowerCase()));
      if (foundKey) seriesData = seriesMap[foundKey];
    }
    // special rendering for Figure 5: ages at home purchase
    if (!seriesData && seriesName && seriesName.startsWith('FIG5')){
      // look for homeownership age grouped percentages
      const needed = ['hor_under_35','hor_35_44','hor_45_54','hor_55_64','hor_65_plus','hor_all'];
      const found = {};
      for (const k of Object.keys(seriesMap)){
        const kl = k.toLowerCase();
        for (const need of needed){
          if (kl.includes(need)) found[need] = k;
        }
      }
      const groups = ['hor_under_35','hor_35_44','hor_45_54','hor_55_64','hor_65_plus'];
      const missing = groups.every(g => found[g]);
      if (missing){
        const d0 = seriesMap[found[groups[0]]];
        const allX = d0.x || [];
        // default sample interval control: show every Nth record
        const sampleControlId = 'fig5-sample-interval';
        // remove existing plot divs
        card.querySelectorAll('.plot').forEach(n=>n.remove());
        const controlWrap = card.querySelector('.fig5-controls') || document.createElement('div');
        controlWrap.className = 'fig5-controls';
        controlWrap.style.marginTop = '0.5rem';
        controlWrap.innerHTML = `Show every <select id="${sampleControlId}"><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option><option value="4">4</option><option value="6">6</option></select> time points`;
        // ensure control is appended once
        if (!card.querySelector('.fig5-controls')) card.appendChild(controlWrap);
        const plotDiv = document.createElement('div');
        plotDiv.className = 'plot';
        plotDiv.style.minHeight = '260px';
        card.appendChild(plotDiv);

        function renderGrouped(sample){
          const idxs = [];
          for (let i=0;i<allX.length;i+=sample) idxs.push(i);
          const x = idxs.map(i=>allX[i]);
          const traces = [];
          const colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd'];
          for (let gi=0; gi<groups.length; gi++){
            const gkey = found[groups[gi]];
            const series = seriesMap[gkey];
            const y = idxs.map(i => series.y[i]);
            traces.push({x, y, name: groups[gi].replace('hor_','').replace(/_/g,'-'), type:'bar', marker:{color:colors[gi]}});
          }
          const layout = {margin:{t:20}, barmode:'group', legend:{orientation:'h'}, xaxis:{title:'Date'}, yaxis:{title:'Percent homeowners'}};
          Plotly.newPlot(plotDiv, traces, layout, {responsive:true});
        }

        const sel = document.getElementById(sampleControlId);
        if (sel) sel.addEventListener('change', ()=> renderGrouped(Number(sel.value)));
        // initial render
        const initial = (document.getElementById(sampleControlId) && Number(document.getElementById(sampleControlId).value)) || 3;
        renderGrouped(initial);
        return;
      }
    }
    // special handling for placeholder figure cards
    if (!seriesData && seriesName && seriesName.startsWith('FIG5')){
      // Figure 5: try to find a series that looks like age/homeownership
      const keys = findKeysByKeywords(seriesMap, ['age','home','ownership','purchase']);
      if (keys.length) seriesData = seriesMap[keys[0]];
    }
    // Figure 6: debt & downpayment - render multiple matching series in one card
    if (!seriesData && seriesName && seriesName.startsWith('FIG6')){
      const debtKeys = findKeysByKeywords(seriesMap, ['debt','loan','credit','balance','savings','downpay','downpayment','payment','afford']);
      if (debtKeys.length){
        // remove existing plot divs
        card.querySelectorAll('.plot').forEach(n=>n.remove());
        const plotDiv = document.createElement('div');
        plotDiv.className = 'plot';
        card.appendChild(plotDiv);
        const traces = debtKeys.map(k=>({x: seriesMap[k].x, y: seriesMap[k].y, name: k, mode:'lines'}));
        const layout = {margin:{t:40}, title:{text: (card.querySelector('h3')||{}).textContent || 'Debt & Savings'}, xaxis:{title:'Date'}, yaxis:{title:'Value (units vary)'}};
        Plotly.newPlot(plotDiv, traces, layout);
        return; // done with this card
      }
    }
    // remove existing plot divs
    card.querySelectorAll('.plot').forEach(n=>n.remove());
    if (!seriesData){
      const msg = document.createElement('div');
      msg.className = 'plot';
      msg.textContent = 'series not found in exported data';
      card.appendChild(msg);
      return;
    }
    renderSeriesInCard(card, seriesData, seriesName);
  });
  // render end-of-page summary figures
  try{
    await renderSummaryFigures(seriesMap);
  }catch(e){
    console.warn('failed rendering summary figures', e);
  }
}

// Render three summary figures in the final section
async function renderSummaryFigures(seriesMap){
  const containerId = 'summary-figures';
  let container = document.getElementById(containerId);
  if (!container){
    const sec = document.createElement('section');
    sec.className = 'fp-section';
    sec.innerHTML = `<div class="content-wrap"><div class="category"><h2>Summary Figures</h2><div id="${containerId}" class="datasets"></div></div></div>`;
    // insert after the debt section so summaries appear earlier
    const debtSection = document.getElementById('debt');
    if (debtSection && debtSection.parentNode){
      debtSection.parentNode.insertBefore(sec, debtSection.nextSibling);
    } else {
      document.querySelector('main').appendChild(sec);
    }
    container = document.getElementById(containerId);
  }
  container.innerHTML = '';

  const figures = [
    {title: 'Mortgage Rates vs Prices', series: ['MORTGAGE30US','MSPUS'], keywords: ['mortgage','msp','asp','price','mspus','mortgage30']},
    {title: 'Inflation & Income', series: ['CPIAUCSL','MEHOINUSA672N'], keywords: ['cpi','inflation','income','median income','mehoin']},
    {title: 'Debt & Credit', series: ['SLOAS','CCLACBW027SBOG'], keywords: ['student','loan','credit','debt','sloas','cc']},
  ];

  for (const f of figures){
    const card = document.createElement('div');
    card.className = 'card';
    const h = document.createElement('h3');
    h.textContent = f.title;
    card.appendChild(h);
    const plot = document.createElement('div');
    plot.className = 'plot';
    container.appendChild(card);
    card.appendChild(plot);

    let traces = [];
    for (const s of f.series){
      const d = seriesMap[s];
      if (!d) continue;
      traces.push({x:d.x, y:d.y, name:s, mode:'lines'});
    }
    // fallback: try keyword matching if explicit codes missing
    if (traces.length === 0 && f.keywords){
      const keys = findKeysByKeywords(seriesMap, f.keywords);
      // take up to 3 matches
      for (const k of keys.slice(0,3)){
        const d = seriesMap[k];
        if (!d) continue;
        traces.push({x:d.x, y:d.y, name:k, mode:'lines'});
      }
    }
    if (traces.length===0){
      plot.textContent = 'no data available';
    } else {
      const layout = {margin:{t:40}, title:{text: f.title}, xaxis:{title:'Date'}, yaxis:{title:'Value (units vary)'}};
      Plotly.newPlot(plot, traces, layout);
    }
  }
}

document.getElementById('refresh').addEventListener('click', refreshAll);

window.addEventListener('load', refreshAll);

// show/hide details when Info button is clicked
document.addEventListener('click', (e)=>{
  const btn = e.target.closest('.info-btn');
  if (!btn) return;
  const card = btn.closest('.card');
  if (!card) return;
  card.classList.toggle('show');
});

// ethics card toggles
document.addEventListener('click', (e)=>{
  const b = e.target.closest('.ethics-btn');
  if (!b) return;
  const card = b.closest('.ethic-card');
  if (!card) return;
  const more = card.querySelector('.ethics-more');
  if (!more) return;
  more.style.display = (more.style.display === 'none') ? 'block' : 'none';
});

// If the page is opened via file://, inform the user that fetch() will fail
window.addEventListener('load', ()=>{
  if (location.protocol === 'file:'){
    const w = document.getElementById('server-warning');
    if (w) w.style.display = 'block';
  }
});
