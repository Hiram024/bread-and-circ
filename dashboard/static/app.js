const $ = id => document.getElementById(id);
const safe = v => String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const known = v => v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v));
const nfmt = v => known(v) ? Number(v).toLocaleString('es-MX') : 'Sin dato';
const pct = v => known(v) ? `${Number(v).toFixed(1)}%` : 'Sin dato';
const pp = v => known(v) ? `${Number(v)>0?'+':''}${Number(v).toFixed(2)} pp` : 'Sin dato';
const years = [2009,2012,2015,2018,2021,2024];
const election = y => [2012,2018,2024].includes(y) ? 'Presidencial' : 'Intermedia';
const baseLayout = {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'Inter, sans-serif',color:'#574c69',size:12},margin:{t:20,b:65,l:56,r:24},showlegend:true,legend:{orientation:'h',y:-.22,x:0},xaxis:{showgrid:false,zeroline:false},yaxis:{gridcolor:'#eee9f4',zeroline:false}};
let state = {profiles:[],national:[],draft:null,items:[],offset:0,total:0,request:0,controller:null};
async function json(url, opts={}) {
  const r=await fetch(url,opts);
  if(!r.ok) throw new Error(`No se pudieron cargar los datos (${r.status}). Intenta de nuevo.`);
  return r.json();
}
function plot(id,traces,layout={}) {return Plotly.newPlot(id,traces,{...baseLayout,...layout},{responsive:true,displayModeBar:false});}
function stat(value,label,description) {return `<div class="stat"><div class="kicker">${safe(label)}</div><div class="value">${safe(value)}</div><div class="desc">${safe(description)}</div></div>`;}
function setTab(tab) {
  document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('active',e.id===`tab-${tab}`));
  document.querySelectorAll('#nav button').forEach(e=>{e.classList.toggle('active',e.dataset.tab===tab);if(e.dataset.tab===tab)e.setAttribute('aria-current','page');else e.removeAttribute('aria-current');});
  const titles={resumen:['Panorama nacional','¿Qué ocurrió entre 2009 y 2024?'],perfiles:['Perfiles estadísticos','¿Qué distingue a los cuatro perfiles?'],explorar:['Explorador territorial','¿Dónde aparecen esos patrones?'],clasificar:['Clasificación de agregados','Clasifica nuevos registros compatibles sin reentrenar'],fichas:['Fichas educativas','Generación auditable y aprobación humana'],auditoria:['Cobertura y límites','¿Hasta dónde interpretar los resultados?']};
  $('pageTitle').textContent=titles[tab][0];$('pageIntro').textContent=titles[tab][1];
  if(tab==='explorar')loadObservations();
  if(tab==='auditoria')loadAudit();
  requestAnimationFrame(()=>document.querySelectorAll('.tab.active .js-plotly-plot').forEach(el=>Plotly.Plots.resize(el)));
}
function historyTraces(records, value) {
  return ['Presidencial','Intermedia'].map((type,i)=>{
    const rows=records.filter(x=>x.tipo===type);
    return {x:rows.map(x=>String(x.anio)),y:rows.map(x=>x[value]),type:'scatter',mode:'markers+lines',connectgaps:false,name:type,
      marker:{symbol:i?'diamond':'circle',color:i?'#996879':'#7651ac',size:10},line:{color:i?'#996879':'#7651ac',width:3,dash:i?'dot':'solid'},
      hovertemplate:'%{x}: %{y:.2f}%<extra>'+type+'</extra>'};
  });
}
function historyLayout() {return {xaxis:{type:'category',categoryorder:'array',categoryarray:years.map(String)},yaxis:{title:'Participación (%)',range:[0,100],gridcolor:'#eee9f4'}};}
function renderSummary(payload) {
  state.profiles=payload.perfiles;state.national=[...payload.historico].sort((a,b)=>a.anio-b.anio);const m=payload.meta;
  $('packageVersion').textContent=m.package_version;$('packageVersion').title=m.package_digest;
  $('modelBadge').textContent=`K-Means · k=${m.k}`;$('profileCountBadge').textContent=`${payload.perfiles.length} perfiles exploratorios`;
  $('modelExplanation').textContent=`Modelo del conjunto elegible: ${m.features.length} variables, escalador estándar y ${m.k} perfiles. La cobertura LN 2024 es ${pct(m.cobertura_LN_2024.porcentaje)}: ${nfmt(m.cobertura_LN_2024.numerador)} / ${nfmt(m.cobertura_LN_2024.denominador)} registros del agregado nacional procesado de cinco edades.`;
  $('kpis').innerHTML=stat(nfmt(m.total_unidades_panel),'Unidades del panel','Unión de municipio × edad en seis años')+stat(nfmt(m.total_unidades_modeladas),'Unidades elegibles','Subconjunto modelado del panel')+stat(nfmt(m.total_municipios_modelados),'Municipios representados','Al menos una edad elegible')+stat(pct(m.cobertura_LN_2024.porcentaje),'Cobertura LN 2024','Elegibles / nacional procesado de cinco edades');
  plot('nationalChart',historyTraces(state.national,'participacion_pct'),historyLayout());
  $('nationalRows').innerHTML=state.national.map(x=>`<tr><th scope="row">${x.anio} · ${safe(x.tipo)}</th><td>${nfmt(x.SV+x.NV)}</td><td>${nfmt(x.SV)}</td><td>${pct(x.participacion_pct)}</td><td>${pct(x.ns_pct)}</td></tr>`).join('');
  $('nationalInsights').innerHTML=['Intermedia','Presidencial'].map(type=>{
    const rows=state.national.filter(x=>x.tipo===type),first=rows[0],last=rows.at(-1);
    if(!first||!last||!known(first.participacion_pct)||!known(last.participacion_pct))return `<div><b>${safe(type)}</b><p>Sin datos suficientes para comparar los extremos.</p></div>`;
    const change=last.participacion_pct-first.participacion_pct;
    return `<div><b>${safe(type)}: ${pp(change)}</b><p>De ${pct(first.participacion_pct)} en ${first.anio} a ${pct(last.participacion_pct)} en ${last.anio}. Diferencia nacional entre elecciones del mismo tipo; no explica sus causas.</p></div>`;
  }).join('');
  plot('distributionChart',[{type:'bar',orientation:'h',y:payload.perfiles.map(p=>'Perfil '+p.perfil_id).reverse(),x:payload.perfiles.map(p=>p.n_unidades).reverse(),marker:{color:'#7651ac'},text:payload.perfiles.map(p=>nfmt(p.n_unidades)).reverse(),textposition:'outside',cliponaxis:false}],{showlegend:false,margin:{l:82,r:65,t:20,b:65},xaxis:{title:'Unidades elegibles',gridcolor:'#eee9f4'},yaxis:{showgrid:false}});
  $('profileCards').innerHTML=payload.perfiles.map(p=>`<div class="profile"><div class="pill">P${p.perfil_id}</div><h3>${safe(p.nombre)}</h3><div class="mainnumber">${pct(p.media_presidencial)}</div><div class="caption">Media presidencial · unidades sin ponderar</div><div class="twovalues"><span>${pct(p.media_intermedia)} intermedia</span><strong>${nfmt(p.n_unidades)} unidades</strong></div><p>${pct(p.porcentaje_unidades)} de las elegibles. Cambio presidencial: ${pp(p.cambio_presidencial_pp)}; intermedio: ${pp(p.cambio_intermedia_pp)}.</p><p class="chartNote">Patrón medio del grupo: no caracteriza a cada unidad o persona, ni certifica representatividad nacional.</p><button type="button" class="secondaryButton exploreProfile" data-profile="${p.perfil_id}">Explorar P${p.perfil_id}</button></div>`).join('');
  const profileBars=(fields,suffix)=>fields.map(([name,key,color])=>({type:'bar',name,x:payload.perfiles.map(p=>'P'+p.perfil_id),y:payload.perfiles.map(p=>p[key]),marker:{color},text:payload.perfiles.map(p=>suffix==='pp'?pp(p[key]):pct(p[key])),textposition:'auto',hovertemplate:'%{x}: %{y:.2f} '+suffix+'<extra>'+name+'</extra>'}));
  plot('profileChart',profileBars([['Presidencial','media_presidencial','#7651ac'],['Intermedia','media_intermedia','#996879']],'%'),{barmode:'group',yaxis:{range:[0,100],title:'Media entre unidades (%)',gridcolor:'#eee9f4'}});
  plot('changeChart',profileBars([['Presidencial 2024−2012','cambio_presidencial_pp','#7651ac'],['Intermedia 2021−2009','cambio_intermedia_pp','#996879']],'pp'),{barmode:'group',yaxis:{title:'Cambio medio (pp)',zeroline:true,zerolinecolor:'#71647d',gridcolor:'#eee9f4'}});
  $('profileComparison').innerHTML=payload.perfiles.map(p=>`<tr><th scope="row">P${p.perfil_id}: ${safe(p.nombre)}</th><td>${nfmt(p.n_unidades)}</td><td>${pct(p.porcentaje_unidades)}</td><td>${pct(p.media_presidencial)}</td><td>${pct(p.media_intermedia)}</td><td>${pp(p.cambio_presidencial_pp)}</td><td>${pp(p.cambio_intermedia_pp)}</td></tr>`).join('');
  $('profileFilter').innerHTML='<option value="">Todos los perfiles</option>'+payload.perfiles.map(p=>`<option value="${p.perfil_id}">P${p.perfil_id}: ${safe(p.nombre)}</option>`).join('');
  $('draftProfile').innerHTML=payload.perfiles.map(p=>`<option value="${p.perfil_id}">Perfil ${p.perfil_id} — ${safe(p.nombre)}</option>`).join('');
  document.querySelectorAll('.exploreProfile').forEach(button=>button.onclick=()=>{$('profileFilter').value=button.dataset.profile;state.offset=0;setTab('explorar');});
}
function clearObservationResults(message) {
  state.items=[];state.total=0;
  $('observationDetail').classList.add('hidden');$('selectionSummary').classList.add('hidden');
  $('obsCount').textContent='— unidades';$('pageRange').textContent=message;$('obsStatus').textContent=message;
  $('obsRows').replaceChildren();$('prevPage').disabled=true;$('nextPage').disabled=true;
}
function observationKey(row) {return `${row.EDOCVE}/${row.MPIOCVE}/${row.grupo_edad}`;}
async function loadObservations(reset=true) {
  clearTimeout(timer);
  if(reset)state.offset=0;
  state.controller?.abort();state.controller=new AbortController();const request=++state.request;
  clearObservationResults('Cargando coincidencias…');
  const url=new URL('/api/observations',location.origin);
  [['estado',$('stateFilter').value],['perfil',$('profileFilter').value],['edad',$('ageFilter').value],['q',$('municipioSearch').value],['offset',state.offset],['limit',100]].forEach(([k,v])=>{if(v!==''&&v!==undefined)url.searchParams.set(k,v);});
  try {
    const p=await json(url,{signal:state.controller.signal});
    if(request!==state.request)return;
    state.items=p.items;state.total=p.total;
    $('obsCount').textContent=nfmt(p.total)+' unidades';
    const range=p.total?`${nfmt(p.offset+1)}–${nfmt(p.offset+p.items.length)} de ${nfmt(p.total)}`:'0 de 0';
    $('pageRange').textContent=range;$('obsStatus').textContent=p.total?'Selecciona una clave para consultar sus seis elecciones.':'Sin coincidencias para estos filtros.';
    $('obsRows').innerHTML=p.items.map(x=>`<tr><td><button type="button" class="rowDetail" data-key="${safe(observationKey(x))}" aria-label="Ver ${safe(x.clave_municipal)}, ${safe(x.MPIONOM)}, edad ${safe(x.grupo_edad)}">${safe(x.clave_municipal)}</button></td><td>${safe(x.MPIONOM)}</td><td>${safe(x.EDONOM)}</td><td>${safe(x.grupo_edad)}</td><td>P${x.perfil_id}</td><td>${pct(x.media_presidencial)}</td><td>${pct(x.media_intermedia)}</td></tr>`).join('')||'<tr><td colspan="7">Sin observaciones</td></tr>';
    $('prevPage').disabled=p.offset===0;$('nextPage').disabled=p.offset+p.items.length>=p.total;
    const a=p.analytics;
    $('selectionSummary').innerHTML=`<b>Todas las coincidencias (${nfmt(a.unidades)} unidades; ${nfmt(a.municipios)} municipios)</b><p>Media presidencial: ${pct(a.medias.media_presidencial)} · Intermedia: ${pct(a.medias.media_intermedia)} · Cambios: ${pp(a.medias.cambio_presidencial_pp)} / ${pp(a.medias.cambio_intermedia_pp)} (presidencial / intermedia).</p><p>Medias simples entre todas las unidades filtradas, no solo las 100 de esta página. LN 2024 sumada: ${nfmt(a.lista_nominal_2024)}; no es población nacional.</p><p>${a.perfil_conteos.map(p=>`P${p.perfil_id}: ${nfmt(p.unidades)} unidades`).join(' · ')||'Sin unidades para resumir.'}</p>`;
    $('selectionSummary').innerHTML+=`<details><summary>Medias históricas de todas las coincidencias</summary><div class="tableWrap" tabindex="0" role="region" aria-label="Medias históricas de la selección completa"><table><caption>Medias simples entre unidades con tasa disponible; sin ponderación poblacional</caption><thead><tr><th>Año / tipo</th><th>Media %</th><th>Unidades con tasa</th></tr></thead><tbody>${a.historico.map(x=>`<tr><th scope="row">${x.anio} · ${safe(x.tipo)}</th><td>${pct(x.media_tasa_pct)}</td><td>${nfmt(x.unidades_con_tasa)}</td></tr>`).join('')}</tbody></table></div></details>`;
    $('selectionSummary').classList.remove('hidden');
    document.querySelectorAll('.rowDetail').forEach(button=>button.onclick=()=>showDetail(button.dataset.key));
  } catch(error) {
    if(request!==state.request||error.name==='AbortError')return;
    clearObservationResults('Error: '+error.message+' Cambia un filtro o vuelve a entrar al explorador para reintentar.');
  }
}
function showDetail(key) {
  const row=state.items.find(x=>observationKey(x)===key);if(!row)return;
  $('detailTitle').textContent=`${row.clave_municipal} · ${row.MPIONOM} · ${row.grupo_edad} años`;
  $('detailContext').textContent=`${row.EDONOM} · P${row.perfil_id}: ${row.perfil_nombre}. LN 2024: ${nfmt(row.LN_2024)}; máximo NS en seis años: ${pct(row.max_ns_pct)}. Cambios presidencial / intermedia: ${pp(row.cambio_presidencial_pp)} / ${pp(row.cambio_intermedia_pp)}.`;
  const rows=years.map(anio=>({anio,tipo:election(anio),tasa:row[`tasa_${anio}`],observados:row[`observados_${anio}`]}));
  $('detailRows').innerHTML=rows.map(x=>`<tr><th scope="row">${x.anio}</th><td>${x.tipo}</td><td>${pct(x.tasa)}</td><td>${nfmt(x.observados)}</td></tr>`).join('');
  $('observationDetail').classList.remove('hidden');plot('detailChart',historyTraces(rows,'tasa'),historyLayout());$('observationDetail').focus();
}
let timer;
function scheduledSearch() {
  clearTimeout(timer);state.controller?.abort();++state.request;state.offset=0;
  clearObservationResults('Preparando nueva búsqueda…');timer=setTimeout(()=>loadObservations(),250);
}
const identityLabels={estable_por_nombre_y_clave:'Nombre y clave estables',incompleto_en_serie:'Municipio ausente en alguna elección',revisar_identidad_nominal:'Variantes de nombre que requieren revisión'};
async function loadAudit() {
  $('auditStatus').textContent='Comprobando cobertura y evidencia B2…';$('coverageContent').classList.add('hidden');
  $('territoryStatus').textContent='Cargando identidad nominal…';$('auditCards').replaceChildren();$('auditRows').replaceChildren();
  try {
    const d=await json('/api/analysis-audit');
    $('coverageCards').innerHTML=stat(nfmt(d.panel),'Panel','Unidades municipio × edad')+stat(nfmt(d.elegibles),'Elegibles','Mismos filtros B2 y B4')+stat(nfmt(d.excluidas_unicas),'Excluidas únicas','Cada unidad contada una vez');
    const coverageLabels={unidades_panel:'Unidades elegibles / panel',municipios_panel:'Municipios representados / panel',LN_2024_panel:'LN 2024 elegible / panel',LN_2024_nacional_procesado:'LN 2024 elegible / nacional procesado',municipios_2024:'Municipios representados / agregado 2024'};
    const coverageUniverses={unidades_panel:'Unión de municipio × edad de los seis CSV anuales',municipios_panel:'Unión de claves municipales de los seis CSV anuales',LN_2024_panel:'Lista nominal 2024 de las unidades del panel',LN_2024_nacional_procesado:'Lista nominal nacional procesada 2024: cinco edades',municipios_2024:'Municipios presentes en el agregado procesado 2024'};
    $('coverageRows').innerHTML=d.cobertura.map(x=>`<tr><th scope="row">${safe(coverageLabels[x.medida]||x.medida)}</th><td>${nfmt(x.numerador)}</td><td>${nfmt(x.denominador)}</td><td>${pct(x.porcentaje)}</td><td>${safe(coverageUniverses[x.medida]||x.universo)}</td></tr>`).join('');
    const causes=Object.fromEntries(d.causas.map(x=>[x.codigo,x.motivo]));
    $('exclusionRows').innerHTML=d.causas.map(x=>`<tr><th scope="row">${safe(x.motivo)}</th><td>${nfmt(x.unidades)}</td></tr>`).join('');
    $('overlapRows').innerHTML=d.combinaciones_excluidas.map(x=>`<tr><th scope="row">${safe(x.causas.map(c=>causes[c]).join(' + '))}</th><td>${nfmt(x.unidades)}</td></tr>`).join('');
    $('selectionRows').innerHTML=[...d.seleccion_edad,...d.seleccion_entidad].map(x=>`<tr><th scope="row">${safe(x.grupo_edad||x.EDONOM)}</th><td>${nfmt(x.unidades)}</td><td>${nfmt(x.incluidas)}</td><td>${nfmt(x.excluidas)}</td><td>${pct(x.incluidas_pct_del_grupo)}</td></tr>`).join('');
    $('auditStatus').textContent='Fuentes B2 y unidades cotejadas con el paquete activo. Sin filtros del explorador.';$('coverageContent').classList.remove('hidden');
  } catch(error) {$('auditStatus').textContent='Cobertura no disponible: '+error.message;}
  try {
    const d=await json('/api/territory-audit');
    $('auditCards').innerHTML=Object.entries(d.estados).map(([k,v])=>stat(nfmt(v),identityLabels[k]||k.replaceAll('_',' '),'Claves municipales, no unidades por edad')).join('');
    $('auditRows').innerHTML=d.examples.map(x=>`<tr><td>${safe(x.clave_municipal)}</td><td>${safe(x.MPIONOM)}</td><td>${safe(identityLabels[x.estatus_administrativo]||x.estatus_administrativo.replaceAll('_',' '))}</td><td>${safe(x.nombres)}</td></tr>`).join('');
    $('territoryStatus').textContent=`Universo: ${nfmt(d.total)} claves municipales del panel. Estable significa coincidencia nominal, no equivalencia cartográfica.`;
  } catch(error) {$('territoryStatus').textContent=error.message;}
}
async function sendCsv(){const f=$('csvFile').files[0];if(!f){$('csvFeedback').textContent='Selecciona un CSV primero';return}const form=new FormData();form.append('file',f);$('csvFeedback').textContent='Validando e infiriendo...';try{let r=await fetch('/api/classify',{method:'POST',body:form});if(!r.ok){let e=await r.json();throw new Error(typeof e.detail==='string'?e.detail:JSON.stringify(e))}let b=await r.blob();let u=URL.createObjectURL(b);let a=document.createElement('a');a.href=u;a.download='clasificacion_agregada.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);$('csvFeedback').textContent='Clasificación realizada. Se descargó el CSV. El modelo no ha sido reentrenado.'}catch(e){$('csvFeedback').textContent=`Error de validación: ${e.message}`}}
function invalidateDraft(){state.draft=null;$('reviewArea').classList.add('hidden');$('reviewCheck').checked=false;$('approvalStatus').textContent='';$('draftArea').textContent='Genera un borrador para el perfil seleccionado antes de revisarlo.'}
async function createDraft(){const pid=Number($('draftProfile').value);invalidateDraft();try{const p=await json('/api/draft/'+pid);if(Number($('draftProfile').value)!==pid)return;state.draft=p;const d=p.draft;const fields=[['Descripción estadística','resumen'],['Evolución electoral','evolucion'],['Texto educativo neutral','contenido_educativo'],['Metodología','metodologia'],['Limitaciones','limitaciones']];$('draftArea').innerHTML=`<div class="help"><b>Validación automática:</b> ${p.validation.passed?'Aprobada':'No aprobada'} · ${p.agent_steps.join(' → ')}<br>Versión: ${safe(p.package_version)} · Contenido: ${safe(p.draft_digest.slice(0,12))}</div><h3>${safe(d.titulo)}: ${safe(d.subtitulo)}</h3>`+fields.map(([h,k])=>`<h4>${h}</h4><p>${safe(d[k])}</p>`).join('')+`<p><b>Fuente:</b> ${safe(d.fuente)}</p>`;$('reviewArea').classList.remove('hidden')}catch(e){$('draftArea').textContent=e.message}}
async function approve(){try{if(!state.draft||state.draft.perfil_id!==Number($('draftProfile').value))throw new Error('Genera y revisa el borrador del perfil seleccionado');const payload={profile_id:state.draft.perfil_id,reviewer:$('reviewer').value.trim(),confirmed:$('reviewCheck').checked,package_version:state.draft.package_version,package_digest:state.draft.package_digest,draft_digest:state.draft.draft_digest};const r=await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(typeof result.detail==='string'?result.detail:'Verifica nombre y aprobación');$('approvalStatus').innerHTML=`Ficha aprobada localmente para ${safe(result.package_version)}. <a class="downloadLink" href="${safe(result.download_url)}">↓ Descargar PDF revisado</a>`}catch(e){$('approvalStatus').textContent='No se aprobó: '+e.message}}

async function initialize() {
  document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
  document.querySelector('#nav button.active').setAttribute('aria-current','page');
  ['stateFilter','profileFilter','ageFilter'].forEach(id=>$(id).onchange=()=>loadObservations());
  $('municipioSearch').oninput=scheduledSearch;
  $('clearFilters').onclick=()=>{['stateFilter','profileFilter','ageFilter','municipioSearch'].forEach(id=>$(id).value='');loadObservations();};
  $('prevPage').onclick=()=>{state.offset=Math.max(0,state.offset-100);loadObservations(false);};
  $('nextPage').onclick=()=>{state.offset+=100;loadObservations(false);};
  $('csvFile').onchange=e=>$('uploadLabel').textContent=e.target.files[0]?.name||'Seleccionar archivo CSV';
  $('sendCsv').onclick=sendCsv;$('draftButton').onclick=createDraft;$('approveButton').onclick=approve;$('draftProfile').onchange=invalidateDraft;
  try {
    const [summary,states]=await Promise.all([json('/api/summary'),json('/api/states')]);
    renderSummary(summary);
    $('stateFilter').innerHTML+=states.map(s=>`<option value="${s.EDOCVE}">${safe(s.EDONOM)}</option>`).join('');
  } catch(error) {$('kpis').textContent='Error cargando datos: '+error.message;}
}
initialize();
