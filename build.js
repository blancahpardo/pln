const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = __dirname;
const REPO = 'blancahpardo/pln';
const TEACHER_PASSWORD = 'profe_27';
const STUDENT_PASSWORD = 'caracola';

function sha256(text) {
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex');
}
function b64(str) {
  return Buffer.from(str, 'utf8').toString('base64');
}
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---- Palette (reused verbatim from the TEE site template, per la usuaria) ----
const CSS_BASE = `
:root {
  --azul: #003B5C;
  --azul-d: #00283F;
  --amar: #F4C542;
  --gris: #34484F;
  --claro: #F3F3F4;
  --humo: #9FB1BA;
  --verde: #2E7D32;
  --rojo: #B00020;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, Helvetica, sans-serif; color: var(--gris); background:#fff; }
a { color: inherit; }
`;

const CSS_INDEX = `
${CSS_BASE}
body { background: var(--azul); min-height:100vh; display:flex; flex-direction:column; }
#gate { position:fixed; inset:0; background:var(--azul); display:flex; align-items:center; justify-content:center; padding:24px; z-index:999; }
#gate .box { max-width:380px; width:100%; text-align:center; }
#gate .kicker { color:var(--amar); font-size:12px; font-weight:bold; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:10px; }
#gate h1 { color:#fff; font-size:26px; margin:0 0 10px; }
#gate p { color:var(--humo); font-size:14px; margin:0 0 26px; }
#gate input { width:100%; padding:13px 16px; border-radius:8px; border:none; font-size:15px; font-family:Arial,Helvetica,sans-serif; margin-bottom:14px; outline:2px solid transparent; }
#gate input:focus { outline:2px solid var(--amar); }
#gate button.submit { width:100%; padding:13px 16px; border-radius:8px; border:none; background:var(--amar); color:var(--azul-d); font-size:15px; font-weight:bold; font-family:Arial,Helvetica,sans-serif; cursor:pointer; }
#gate button.submit:hover { filter:brightness(1.06); }
#gate .error { color:#FFB3B3; font-size:13px; margin-top:12px; min-height:18px; }
#page { display:none; min-height:100vh; flex:1; flex-direction:column; }
header { padding: 60px 6vw 20px; text-align:center; }
header .kicker { color: var(--amar); font-size:12px; font-weight:bold; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:10px; }
header h1 { color:#fff; font-size:clamp(26px,4.2vw,40px); margin:0 0 6px; }
header .author { color: var(--amar); font-size:14px; font-weight:bold; margin:0 0 12px; }
header p { color: var(--humo); font-size:14px; margin:0; }
main { flex:1; max-width:1000px; width:100%; margin:0 auto; padding:40px 6vw 60px; display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:22px; align-content:start; }
.tema-btn { display:flex; flex-direction:column; align-items:flex-start; gap:8px; background:#fff; border:none; border-radius:14px; padding:28px 24px; text-decoration:none; box-shadow:0 4px 16px rgba(0,0,0,.18); transition:transform .15s ease; }
.tema-btn:hover { transform:translateY(-3px); }
.tema-num { font-size:13px; font-weight:bold; color:var(--amar); background:var(--azul); padding:4px 12px; border-radius:20px; letter-spacing:1px; }
.tema-title { font-size:19px; font-weight:bold; color:var(--azul); margin-top:4px; }
.tema-btn { position:relative; }
.tema-btn .teacher-hint { position:absolute; top:12px; right:14px; font-size:10px; font-weight:bold; padding:2px 8px; border-radius:10px; }
.tema-btn .teacher-hint.on { background:#DFF3E0; color:var(--verde); }
.tema-btn .teacher-hint.off { background:#FBEAEC; color:var(--rojo); }
footer { text-align:center; padding:20px 6vw 34px; font-size:11px; color:var(--humo); font-style:italic; }
.teacher-link { display:block; margin:0 auto 18px; background:none; border:none; color:var(--humo); font-size:12px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; text-decoration:underline; }
.teacher-link:hover { color:#fff; }
.teacher-wrap { max-width:1000px; width:100%; margin:0 auto; padding:0 6vw; }
.teacher-banner { background:var(--azul-d); color:#fff; border-radius:12px; padding:18px 22px; margin:0 0 10px; }
.teacher-banner strong { color: var(--amar); }
.teacher-banner p { font-size:13px; margin:6px 0 0; color:var(--humo); }
.teacher-token-row { display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }
.teacher-token-row input { flex:1; min-width:220px; padding:9px 12px; border-radius:8px; border:none; font-size:13px; font-family:Arial,Helvetica,sans-serif; }
.teacher-token-row button { background:var(--amar); color:var(--azul-d); border:none; border-radius:8px; padding:9px 16px; font-size:13px; font-weight:bold; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.teacher-status { font-size:12px; margin-top:10px; min-height:16px; }
.teacher-toggle-list { list-style:none; padding:0; margin:16px 0 0; display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; }
.teacher-toggle-list li { background:rgba(255,255,255,.08); border-radius:8px; padding:10px 14px; display:flex; align-items:center; gap:10px; font-size:13px; }
.teacher-toggle-list input { width:18px; height:18px; }
`;

const CSS_TOPIC = `
${CSS_BASE}
#gate { position:fixed; inset:0; background:var(--azul); display:flex; align-items:center; justify-content:center; padding:24px; z-index:999; }
#gate .box { max-width:380px; width:100%; text-align:center; }
#gate .kicker { color:var(--amar); font-size:12px; font-weight:bold; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:10px; }
#gate h1 { color:#fff; font-size:26px; margin:0 0 10px; }
#gate p { color:var(--humo); font-size:14px; margin:0 0 26px; }
#gate input { width:100%; padding:13px 16px; border-radius:8px; border:none; font-size:15px; font-family:Arial,Helvetica,sans-serif; margin-bottom:14px; outline:2px solid transparent; }
#gate input:focus { outline:2px solid var(--amar); }
#gate button.submit { width:100%; padding:13px 16px; border-radius:8px; border:none; background:var(--amar); color:var(--azul-d); font-size:15px; font-weight:bold; font-family:Arial,Helvetica,sans-serif; cursor:pointer; }
#gate button.submit:hover { filter:brightness(1.06); }
#gate .error { color:#FFB3B3; font-size:13px; margin-top:12px; min-height:18px; }
#page { display:none; }
main { max-width:980px; margin:0 auto; padding:48px 6vw 60px; }
.kicker { color:var(--amar); font-size:12px; font-weight:bold; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:8px; }
.view > h1 { color:var(--azul); font-size:32px; margin:0 0 34px; }
.hub-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; margin-bottom:30px; }
.hub-btn { display:flex; flex-direction:column; align-items:flex-start; gap:6px; background:var(--claro); border:none; border-radius:12px; padding:26px 22px; cursor:pointer; text-align:left; box-shadow:0 2px 10px rgba(159,177,186,.28); font-family:Arial,Helvetica,sans-serif; position:relative; }
.hub-btn:hover { background:#E9ECEE; }
.hub-icon { font-size:30px; margin-bottom:4px; }
.hub-label { font-size:17px; font-weight:bold; color:var(--azul); }
.hub-desc { font-size:12.5px; color:var(--humo); }
.back-home { font-size:13px; color:var(--humo); text-decoration:none; }
.back-home:hover { color:var(--azul); }
.sub-view h2 { color:var(--azul); font-size:24px; margin:18px 0 4px; }
.sub-view .section-note { font-size:13px; color:var(--humo); margin:0 0 24px; }
.back-btn { background:none; border:1.5px solid var(--azul); color:var(--azul); font-size:13px; font-weight:bold; padding:6px 14px; border-radius:20px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.back-btn:hover { background:var(--azul); color:#fff; }
.dl-big { display:inline-block; background:var(--amar); color:var(--azul-d); font-weight:bold; font-size:14px; text-decoration:none; padding:10px 20px; border-radius:20px; margin-bottom:18px; }
.pdf-frame { width:100%; height:78vh; border:none; border-radius:8px; box-shadow:0 2px 10px rgba(159,177,186,.28); }
.img-frame { display:block; width:100%; height:auto; border-radius:8px; box-shadow:0 2px 10px rgba(159,177,186,.28); }
.ref-intro { color:var(--azul); font-size:16px; margin:0 0 16px; }
.ref-item { font-size:13.5px; color:var(--gris); line-height:1.6; margin:0 0 16px; padding-left:28px; text-indent:-28px; }
.ref-item a { color:var(--azul); word-break:break-all; }
.ref-item em { font-style:italic; }
.notice { font-size:12px; color:var(--humo); font-style:italic; margin-top:10px; }
/* quiz */
.quiz-start { background:var(--claro); border-radius:12px; padding:26px; }
.quiz-start p { font-size:14px; margin:0 0 18px; }
.quiz-btn { background:var(--azul); color:#fff; border:none; border-radius:20px; padding:11px 22px; font-size:14px; font-weight:bold; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.quiz-btn:hover { filter:brightness(1.15); }
.quiz-progress { font-size:12px; color:var(--humo); margin-bottom:6px; }
.quiz-q { background:var(--claro); border-radius:12px; padding:24px; margin-bottom:18px; }
.quiz-q h3 { color:var(--azul); font-size:17px; margin:0 0 18px; }
.quiz-opt { display:block; width:100%; text-align:left; background:#fff; border:1.5px solid var(--humo); border-radius:8px; padding:12px 16px; margin-bottom:10px; font-size:14px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; color:var(--gris); }
.quiz-opt:hover { border-color:var(--azul); }
.quiz-opt.correct { border-color:var(--verde); background:#EAF6EB; font-weight:bold; }
.quiz-opt.incorrect { border-color:var(--rojo); background:#FBEAEC; }
.quiz-opt[disabled] { cursor:default; }
.quiz-feedback { font-size:13px; color:var(--gris); background:#fff; border-radius:8px; padding:12px 16px; margin-top:4px; margin-bottom:16px; border-left:3px solid var(--azul); }
.quiz-score { font-size:26px; font-weight:bold; color:var(--azul); margin-bottom:8px; }
.quiz-result { background:var(--claro); border-radius:12px; padding:30px; text-align:center; }
/* interactive manual (prueba) */
.im-badge { display:inline-block; background:var(--amar); color:var(--azul-d); font-size:11px; font-weight:bold; letter-spacing:1px; text-transform:uppercase; padding:4px 10px; border-radius:20px; margin-bottom:10px; }
.im-root { margin-top:10px; }
.im-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; }
.im-card { text-align:left; background:var(--claro); border:none; border-radius:12px; padding:20px 20px 18px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; box-shadow:0 2px 10px rgba(159,177,186,.28); transition:transform .12s ease, background .12s ease; }
.im-card:hover { background:#E9ECEE; transform:translateY(-2px); }
.im-card.im-card-bib { background:var(--azul); }
.im-card.im-card-bib .im-card-title, .im-card.im-card-bib .im-card-meta { color:#fff; }
.im-card-icon { font-size:22px; }
.im-card-num { display:block; font-size:11px; font-weight:bold; color:var(--humo); letter-spacing:1px; text-transform:uppercase; margin:8px 0 4px; }
.im-card-title { display:block; font-size:16px; font-weight:bold; color:var(--azul); line-height:1.3; }
.im-card-meta { display:block; font-size:12px; color:var(--humo); margin-top:6px; }
.im-chapter { }
.im-crumb { background:none; border:none; color:var(--humo); font-size:13px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; padding:0; margin-bottom:16px; text-decoration:underline; }
.im-crumb:hover { color:var(--azul); }
.im-chapter-title { color:var(--azul); font-size:23px; margin:0 0 16px; }
.im-block-p { font-size:14.5px; line-height:1.7; color:var(--gris); margin:0 0 14px; }
.im-block-ul, .im-block-ol { margin:0 0 14px; padding-left:22px; }
.im-block-ul li, .im-block-ol li { font-size:14.5px; line-height:1.65; color:var(--gris); margin-bottom:6px; }
.im-sub { border-top:1px solid #E3E7E9; }
.im-sub:first-child { border-top:none; }
.im-sub-head { width:100%; display:flex; align-items:center; justify-content:space-between; gap:10px; background:none; border:none; text-align:left; padding:16px 4px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.im-sub-head:hover .im-sub-title { color:var(--azul-d); }
.im-sub-title { font-size:15.5px; font-weight:bold; color:var(--azul); }
.im-sub-arrow { color:var(--humo); font-size:13px; transition:transform .15s ease; flex:none; }
.im-sub.open .im-sub-arrow { transform:rotate(90deg); }
.im-sub-body { max-height:0; overflow:hidden; padding:0 4px; transition:max-height .25s ease; }
.im-sub.open .im-sub-body { max-height:none; padding-bottom:14px; }
.im-code-toggle { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1.5px dashed var(--humo); color:var(--azul); font-size:12.5px; font-weight:bold; border-radius:20px; padding:7px 14px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; margin:2px 0 14px; }
.im-code-toggle:hover { border-color:var(--azul); }
.im-code-box { display:none; background:#F2F4F5; border-radius:8px; padding:14px 16px; margin:0 0 14px; overflow-x:auto; }
.im-code-box.open { display:block; }
.im-code-box pre { margin:0; font-family:"Courier New",monospace; font-size:13px; line-height:1.55; color:#1c2a30; white-space:pre-wrap; word-break:break-word; }
.im-table-toggle { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1.5px solid var(--azul); color:var(--azul); font-size:12.5px; font-weight:bold; border-radius:20px; padding:7px 14px; cursor:pointer; font-family:Arial,Helvetica,sans-serif; margin:2px 0 14px; }
.im-table-toggle:hover { background:var(--azul); color:#fff; }
.im-table-wrap { display:none; overflow-x:auto; margin:0 0 16px; border-radius:8px; box-shadow:0 2px 10px rgba(159,177,186,.28); }
.im-table-wrap.open { display:block; }
.im-table-wrap table { border-collapse:collapse; width:100%; font-size:13px; }
.im-table-wrap th { background:var(--azul); color:#fff; text-align:left; padding:9px 12px; font-size:12.5px; }
.im-table-wrap td { padding:9px 12px; border-bottom:1px solid #E3E7E9; color:var(--gris); }
.im-table-wrap tr:nth-child(even) td { background:var(--claro); }
.im-errorlist { list-style:none; padding:0; margin:0 0 6px; }
.im-errorlist li { background:var(--claro); border-left:3px solid var(--rojo); border-radius:0 8px 8px 0; padding:12px 16px; margin-bottom:10px; }
.im-errorlist .im-error-term { display:block; font-weight:bold; color:var(--azul); font-size:14px; margin-bottom:4px; }
.im-errorlist .im-error-desc { font-size:13.5px; color:var(--gris); line-height:1.6; }
.im-cite { color:var(--azul); font-weight:bold; cursor:pointer; border-bottom:1.5px dotted var(--azul); white-space:normal; }
.im-cite:hover { color:var(--azul-d); }
.im-cite-pop { display:none; background:var(--azul-d); color:#fff; border-radius:8px; padding:12px 16px; font-size:12.5px; line-height:1.6; margin:6px 0 14px; }
.im-cite-pop.open { display:block; }
.im-cite-pop p { margin:0 0 8px; }
.im-cite-pop p:last-child { margin-bottom:0; }
.im-cite-pop a { color:var(--amar); }
.im-bib-list { margin-top:6px; }
.im-bib-item.im-bib-highlight { background:#FDF1C7; border-radius:8px; padding:10px 14px; margin-left:-14px; margin-right:-14px; }
code.im-inline { background:#F2F4F5; padding:1px 6px; border-radius:4px; font-family:"Courier New",monospace; font-size:.93em; }
/* teacher panel */
.teacher-banner { background:var(--azul-d); color:#fff; border-radius:12px; padding:18px 22px; margin-bottom:24px; }
.teacher-banner strong { color: var(--amar); }
.teacher-banner p { font-size:13px; margin:6px 0 0; color:var(--humo); }
.teacher-token-row { display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }
.teacher-token-row input { flex:1; min-width:220px; padding:9px 12px; border-radius:8px; border:none; font-size:13px; font-family:Arial,Helvetica,sans-serif; }
.teacher-token-row button { background:var(--amar); color:var(--azul-d); border:none; border-radius:8px; padding:9px 16px; font-size:13px; font-weight:bold; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.teacher-status { font-size:12px; margin-top:10px; min-height:16px; }
.teacher-toggle-list { list-style:none; padding:0; margin:16px 0 0; display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; }
.teacher-toggle-list li { background:rgba(255,255,255,.08); border-radius:8px; padding:10px 14px; display:flex; align-items:center; gap:10px; font-size:13px; }
.teacher-toggle-list input { width:18px; height:18px; }
.hub-btn .teacher-hint { position:absolute; top:10px; right:12px; font-size:10px; font-weight:bold; padding:2px 8px; border-radius:10px; }
.hub-btn .teacher-hint.on { background:#DFF3E0; color:var(--verde); }
.hub-btn .teacher-hint.off { background:#FBEAEC; color:var(--rojo); }
footer { text-align:center; padding:26px 6vw 40px; font-size:11px; color:var(--humo); font-style:italic; }
`;

const ICONS = { manual: '📘', principal: '📓', evaluable: '📝', practica: '🧪', quiz: '❓' };
const LABELS = {
  manual: 'Manual teórico', principal: 'Cuaderno principal', evaluable: 'Cuaderno evaluable',
  practica: 'Prácticas', quiz: 'Cuestionario de práctica'
};
const DESCS = {
  manual: 'Lectura en PDF, descargable',
  principal: 'Descarga el cuaderno de trabajo',
  evaluable: 'Descarga la plantilla del entregable',
  practica: 'Documento de la práctica (solo lectura)',
  quiz: '10 preguntas al azar, puntuación sobre 10'
};

function copyrightFooter(temaLabel) {
  return `© Dra. Blanca Hernández Pardo · Programación orientada a PLN${temaLabel ? ' · ' + temaLabel : ''}<br>Queda prohibida la difusión, distribución o reproducción total o parcial de este material sin autorización expresa de la autora.`;
}

function existingViews(tema) {
  return tema.viewOrder.filter(v => tema.views[v] && tema.views[v].exists);
}

function viewIcon(v, tema) { return tema.views[v].icon || ICONS[v] || '📄'; }
function viewLabel(v, tema) { return tema.views[v].label || LABELS[v] || v; }
function viewDesc(v, tema) { return tema.views[v].desc || DESCS[v] || ''; }

function buildHub(tema) {
  const buttons = existingViews(tema).map(v => {
    return `<button class="hub-btn" data-view="${v}" data-type="${v}" style="display:none">
      <span class="teacher-hint" data-hint="${v}"></span>
      <span class="hub-icon">${viewIcon(v, tema)}</span>
      <span class="hub-label">${esc(viewLabel(v, tema))}</span>
      <span class="hub-desc">${esc(viewDesc(v, tema))}</span>
    </button>`;
  }).join('\n    ');
  const toggles = existingViews(tema).map(v =>
    `<li><input type="checkbox" id="chk-${v}" data-type="${v}"><label for="chk-${v}">${esc(viewLabel(v, tema))}</label></li>`
  ).join('\n      ');
  return `<div id="hub" class="view">
  <div class="kicker">${esc(tema.kicker)}</div>
  <div id="teacher-panel" class="teacher-banner" hidden>
    <strong>⚙ Modo profesora</strong>
    <p>Pega aquí tu token de GitHub (solo para esta sesión de navegador; se pierde al cerrar la pestaña) y marca qué materiales ve el alumnado. Los cambios se publican en 1-2 minutos.</p>
    <div class="teacher-token-row">
      <input type="password" id="gh-token" placeholder="Token de GitHub (ghp_... o github_pat_...)">
      <button id="gh-token-save">Guardar token de esta sesión</button>
    </div>
    <div class="teacher-status" id="teacher-status"></div>
    <ul class="teacher-toggle-list">
      ${toggles}
    </ul>
  </div>
  <h1>¿Qué quieres consultar?</h1>
  <div class="hub-grid">
    ${buttons}
  </div>
  <a class="back-home" href="../index.html">← Volver a la asignatura</a>
</div>`;
}

function buildManualView(tema) {
  if (!tema.views.manual || !tema.views.manual.exists) return '';
  const f = tema.views.manual.file;
  return `<div id="view-manual" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Manual teórico · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Puedes leerlo aquí o descargarlo.</p>
  <a class="dl-big" href="${f}" download>⬇ Descargar PDF</a>
  <iframe class="pdf-frame" src="${f}" title="Manual teórico ${esc(tema.titleShort)}"></iframe>
</div>`;
}

function buildViewerDownloadView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Puedes leerlo aquí o descargarlo.</p>
  <a class="dl-big" href="${cfg.file}" download>⬇ Descargar PDF</a>
  <iframe class="pdf-frame" src="${cfg.file}" title="${esc(label)}"></iframe>
</div>`;
}

function buildImageView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Solo puede consultarse aquí, sin descarga.</p>
  <img class="img-frame" src="${cfg.file}" alt="${esc(label)} · ${esc(tema.titleShort)}">
</div>`;
}

function buildReflistView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  const items = cfg.refs.map(r => `<p class="ref-item">${esc(r.author)} (${esc(r.date)}). ${esc(r.title)} <em>[${esc(r.type)}]</em>. ${esc(r.platform)}. <a href="${r.url}" target="_blank" rel="noopener">${esc(r.url)}</a></p>`).join('\n  ');
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <h3 class="ref-intro">Recursos de LinguAIstica</h3>
  ${items}
</div>`;
}

function buildDownloadView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">${cfg.note || 'Descarga el fichero para trabajar con él en tu ordenador.'}</p>
  <a class="dl-big" href="${cfg.file}" download>⬇ Descargar</a>
</div>`;
}

function buildViewerGroupView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  const extraLink = cfg.extraDownload
    ? `<a class="dl-big" href="${cfg.extraDownload.file}" download>⬇ ${esc(cfg.extraDownload.label)}</a>`
    : '';
  if (cfg.items.length === 1) {
    const it = cfg.items[0];
    return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Documento de solo lectura, sin descarga.${cfg.extraDownload ? ' Los materiales que necesitas para trabajarla se descargan aparte, más abajo.' : ''}</p>
  ${extraLink}
  <iframe class="pdf-frame" src="${it.file}#toolbar=0&navpanes=0" title="${esc(label)}"></iframe>
</div>`;
  }
  const subButtons = cfg.items.map(it => `<button class="hub-btn" data-view="${viewKey}-${it.id}">
      <span class="hub-icon">🧪</span>
      <span class="hub-label">${esc(it.label)}</span>
      <span class="hub-desc">Documento (solo lectura)</span>
    </button>`).join('\n    ');
  const leaves = cfg.items.map(it => `<div id="view-${viewKey}-${it.id}" class="view sub-view" hidden>
  <button class="back-btn" data-back="${viewKey}">← Volver</button>
  <h2>${esc(it.label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Documento de solo lectura, sin descarga.</p>
  <iframe class="pdf-frame" src="${it.file}#toolbar=0&navpanes=0" title="${esc(it.label)}"></iframe>
</div>`).join('\n');
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Elige el documento que quieras consultar.</p>
  ${extraLink}
  <div class="hub-grid">
    ${subButtons}
  </div>
</div>
${leaves}`;
}

function buildInteractiveManualView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.exists) return '';
  const label = viewLabel(viewKey, tema);
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <div class="im-badge">Prueba · versión interactiva</div>
  <h2>${esc(label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Mismo contenido que el manual en PDF, en formato navegable por paneles. Pulsa un capítulo para explorarlo.</p>
  <div id="im-root-${viewKey}" class="im-root"></div>
</div>`;
}

function buildQuizView(tema) {
  const cfg = tema.views.quiz;
  if (!cfg || !cfg.exists) return '';
  return `<div id="view-quiz" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Cuestionario de práctica · ${esc(tema.titleShort)}</h2>
  <div id="quiz-root"></div>
</div>`;
}

function buildTopicHtml(tema) {
  const fixedViews = ['manual', 'principal', 'evaluable', 'practica', 'quiz'];
  const extraKeys = tema.viewOrder.filter(v => !fixedViews.includes(v));
  const extraHtml = extraKeys.map(v => {
    const cfg = tema.views[v];
    if (!cfg || !cfg.exists) return '';
    if (cfg.kind === 'viewergroup') return buildViewerGroupView(v, tema);
    if (cfg.kind === 'viewerdownload') return buildViewerDownloadView(v, tema);
    if (cfg.kind === 'image') return buildImageView(v, tema);
    if (cfg.kind === 'reflist') return buildReflistView(v, tema);
    if (cfg.kind === 'interactive_manual') return buildInteractiveManualView(v, tema);
    return buildDownloadView(v, tema);
  });

  const payloadHtml = [
    buildHub(tema),
    buildManualView(tema),
    buildDownloadView('principal', tema),
    buildDownloadView('evaluable', tema),
    buildViewerGroupView('practica', tema),
    ...extraHtml,
    buildQuizView(tema)
  ].filter(Boolean).join('\n');

  const hash = sha256(STUDENT_PASSWORD);
  const teacherHash = sha256(TEACHER_PASSWORD);
  const payloadB64 = b64(payloadHtml);

  let quizManual = '[]', quizCuaderno = '[]';
  if (tema.views.quiz && tema.views.quiz.exists) {
    quizManual = JSON.stringify(JSON.parse(fs.readFileSync(path.join(ROOT, tema.dir, 'quiz_manual.json'), 'utf8')).quiz);
    quizCuaderno = JSON.stringify(JSON.parse(fs.readFileSync(path.join(ROOT, tema.dir, 'quiz_cuaderno.json'), 'utf8')).quiz);
  }

  // Interactive-manual data: one JSON payload per view key using kind 'interactive_manual',
  // e.g. tX/manual_interactivo.json — read at build time and inlined like the quiz banks above.
  const imViewKeys = tema.viewOrder.filter(v => tema.views[v] && tema.views[v].exists && tema.views[v].kind === 'interactive_manual');
  const imData = {};
  imViewKeys.forEach(v => {
    const file = tema.views[v].dataFile || (v + '.json');
    imData[v] = JSON.parse(fs.readFileSync(path.join(ROOT, tema.dir, file), 'utf8'));
  });
  const imDataJson = JSON.stringify(imData);

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(tema.titleFull)} — PLN</title>
<style>${CSS_TOPIC}</style>
</head>
<body>

<div id="gate">
  <div class="box">
    <div class="kicker">${esc(tema.kicker)}</div>
    <h1>PLN</h1>
    <p>Contenido protegido. Introduce la contraseña facilitada en clase.</p>
    <input type="password" id="pw" placeholder="Contraseña" autofocus>
    <button class="submit" id="enter">Acceder</button>
    <div class="error" id="err"></div>
  </div>
</div>

<div id="page">
  <main id="content"></main>
  <footer>
    ${copyrightFooter(tema.titleShort)}
  </footer>
</div>

<script>
(function() {
  var HASH = "${hash}";
  var TEACHER_HASH = "${teacherHash}";
  var PAYLOAD = "${payloadB64}";
  var QUIZ_MANUAL = ${quizManual};
  var QUIZ_CUADERNO = ${quizCuaderno};
  var IM_DATA = ${imDataJson};
  var imRendered = {};
  var SESSION_KEY = "pln_unlocked";
  var REPO = "${REPO}";
  var LOCAL_CONFIG = "config.json";
  var GH_CONFIG_PATH = "${tema.dir}/config.json";
  var ROOT_CONFIG = "../config.json";
  var TEMA_KEY = "${tema.dir}";
  var isTeacher = false;
  var configSha = null;

  function sha256Hex(text) {
    var enc = new TextEncoder().encode(text);
    return crypto.subtle.digest("SHA-256", enc).then(function(buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function(b) {
        return b.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function showView(id) {
    document.querySelectorAll(".view").forEach(function(v) { v.hidden = true; });
    var el = document.getElementById(id) || document.getElementById("view-" + id);
    if (el) el.hidden = false;
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  var quizState = null;

  function renderQuizStart() {
    var root = document.getElementById("quiz-root");
    if (!root) return;
    root.innerHTML =
      '<div class="quiz-start">' +
      '<p>10 preguntas: 5 elegidas al azar del banco del manual y 5 del banco del cuaderno. Puedes repetir el intento tantas veces como quieras — cada vez se vuelven a elegir y reordenar las preguntas.</p>' +
      '<button class="quiz-btn" id="quiz-begin">Empezar</button>' +
      '</div>';
    document.getElementById("quiz-begin").addEventListener("click", startQuiz);
  }

  function startQuiz() {
    var fromManual = shuffle(QUIZ_MANUAL).slice(0, 5);
    var fromCuaderno = shuffle(QUIZ_CUADERNO).slice(0, 5);
    quizState = { questions: shuffle(fromManual.concat(fromCuaderno)), index: 0, score: 0 };
    renderQuizQuestion();
  }

  function renderQuizQuestion() {
    var root = document.getElementById("quiz-root");
    var total = quizState.questions.length;
    if (quizState.index >= total) {
      root.innerHTML =
        '<div class="quiz-result">' +
        '<div class="quiz-score">' + quizState.score + ' / ' + total + '</div>' +
        '<p>Puntuación de este intento.</p>' +
        '<button class="quiz-btn" id="quiz-retry">Volver a intentar</button>' +
        '</div>';
      document.getElementById("quiz-retry").addEventListener("click", startQuiz);
      return;
    }
    var q = quizState.questions[quizState.index];
    var opts = shuffle(q.answerOptions);
    var html = '<div class="quiz-progress">Pregunta ' + (quizState.index + 1) + ' de ' + total + ' · Puntuación provisional: ' + quizState.score + '</div>';
    html += '<div class="quiz-q"><h3>' + q.question + '</h3>';
    opts.forEach(function(opt, i) {
      html += '<button class="quiz-opt" data-idx="' + i + '">' + opt.text + '</button>';
    });
    html += '<div class="quiz-feedback" id="quiz-feedback" hidden></div>';
    html += '</div>';
    root.innerHTML = html;
    var buttons = root.querySelectorAll(".quiz-opt");
    buttons.forEach(function(btn, i) {
      btn.addEventListener("click", function() {
        buttons.forEach(function(b) { b.disabled = true; });
        var chosen = opts[i];
        if (chosen.isCorrect) { btn.classList.add("correct"); quizState.score++; }
        else {
          btn.classList.add("incorrect");
          buttons.forEach(function(b2, j) { if (opts[j].isCorrect) b2.classList.add("correct"); });
        }
        var fb = document.getElementById("quiz-feedback");
        fb.hidden = false;
        fb.textContent = chosen.rationale || (chosen.isCorrect ? "Correcto." : "Incorrecto.");
        var next = document.createElement("button");
        next.className = "quiz-btn";
        next.style.marginTop = "14px";
        next.textContent = quizState.index + 1 < total ? "Siguiente" : "Ver puntuación";
        next.addEventListener("click", function() { quizState.index++; renderQuizQuestion(); });
        root.querySelector(".quiz-q").appendChild(next);
      });
    });
  }

  // ---- Interactive manual engine (self-contained mini-app rendered lazily into #im-root-<key>) ----
  function imEsc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function imFormatBackticks(s) {
    var parts = s.split("\`"), out = "";
    for (var i = 0; i < parts.length; i++) out += (i % 2 === 1) ? '<code class="im-inline">' + imEsc(parts[i]) + "</code>" : imEsc(parts[i]);
    return out;
  }
  function imFormatInline(raw) {
    var re = /{{cite:([^}]*)}}([\\s\\S]*?){{\\/cite}}/g;
    var out = "", last = 0, m;
    while ((m = re.exec(raw))) {
      out += imFormatBackticks(raw.slice(last, m.index));
      out += '<span class="im-cite" data-refs="' + m[1] + '">' + imFormatBackticks(m[2]) + ' <span aria-hidden="true">ⓘ</span></span>';
      last = re.lastIndex;
    }
    out += imFormatBackticks(raw.slice(last));
    return out;
  }
  function imBibText(text) {
    var re = /(https?:\\/\\/[^\\s]+)/g;
    var out = "", last = 0, m;
    while ((m = re.exec(text))) {
      out += imEsc(text.slice(last, m.index));
      var url = m[1].replace(/[.,;]+$/, "");
      out += '<a href="' + imEsc(url) + '" target="_blank" rel="noopener">' + imEsc(url) + "</a>";
      last = m.index + url.length;
    }
    out += imEsc(text.slice(last));
    return out;
  }
  function imRefLookup(data) {
    var m = {};
    data.references.forEach(function(r) { m[r.key] = r.text; });
    return m;
  }
  function imRenderTable(rows, key) {
    var head = rows[0], body = rows.slice(1);
    var t = "<table><thead><tr>" + head.map(function(h) { return "<th>" + imEsc(h) + "</th>"; }).join("") + "</tr></thead><tbody>";
    body.forEach(function(r) { t += "<tr>" + r.map(function(c) { return "<td>" + imEsc(c) + "</td>"; }).join("") + "</tr>"; });
    t += "</tbody></table>";
    return '<button class="im-table-toggle" data-im-table="' + key + '">▤ Ver tabla (' + body.length + ' filas)</button>' +
      '<div class="im-table-wrap" id="im-table-' + key + '">' + t + "</div>";
  }
  function imRenderBlocks(blocks, keyPrefix) {
    var html = "";
    blocks.forEach(function(b, i) {
      var key = keyPrefix + "-" + i;
      if (b.type === "p") html += '<p class="im-block-p">' + imFormatInline(b.text) + "</p>";
      else if (b.type === "ul") html += '<ul class="im-block-ul">' + b.items.map(function(t) { return "<li>" + imFormatInline(t) + "</li>"; }).join("") + "</ul>";
      else if (b.type === "ol") html += '<ol class="im-block-ol">' + b.items.map(function(t) { return "<li>" + imFormatInline(t) + "</li>"; }).join("") + "</ol>";
      else if (b.type === "code") html += '<button class="im-code-toggle" data-im-code="' + key + '">🔎 Descubre el código</button>' +
        '<div class="im-code-box" id="im-code-' + key + '"><pre>' + imEsc(b.code) + "</pre></div>";
      else if (b.type === "table") html += imRenderTable(b.rows, key);
      else if (b.type === "errorlist") html += '<ul class="im-errorlist">' + b.items.map(function(it) {
        return '<li><span class="im-error-term">' + imFormatInline(it.term) + '</span><span class="im-error-desc">' + imFormatInline(it.desc) + "</span></li>";
      }).join("") + "</ul>";
    });
    return html;
  }
  function imWireCommon(root, data) {
    root.querySelectorAll("[data-im-code]").forEach(function(btn) {
      btn.addEventListener("click", function() {
        var box = document.getElementById("im-code-" + btn.dataset.imCode);
        var open = box.classList.toggle("open");
        btn.textContent = open ? "🔽 Ocultar el código" : "🔎 Descubre el código";
      });
    });
    root.querySelectorAll("[data-im-table]").forEach(function(btn) {
      btn.addEventListener("click", function() {
        document.getElementById("im-table-" + btn.dataset.imTable).classList.toggle("open");
      });
    });
    root.querySelectorAll(".im-cite").forEach(function(span) {
      span.addEventListener("click", function() {
        var existing = span.nextElementSibling;
        if (existing && existing.classList && existing.classList.contains("im-cite-pop")) {
          existing.classList.toggle("open");
          return;
        }
        var refs = imRefLookup(data);
        var keys = span.dataset.refs.split(",");
        var pop = document.createElement("div");
        pop.className = "im-cite-pop open";
        pop.innerHTML = keys.map(function(k) { return "<p>" + imBibText(refs[k] || k) + "</p>"; }).join("") +
          '<p><a href="#" data-im-goto-bib="' + keys[0] + '">Ver en Bibliografía →</a></p>';
        span.parentNode.insertBefore(pop, span.nextSibling);
        pop.querySelector("[data-im-goto-bib]").addEventListener("click", function(e) {
          e.preventDefault();
          imShowBib(root, data, this.dataset.imGotoBib);
        });
      });
    });
  }
  function imShowBib(root, data, highlightKey) {
    var html = '<button class="im-crumb" data-im-back="1">← Índice del manual</button>';
    html += '<h3 class="im-chapter-title">Bibliografía</h3>';
    html += '<h4 class="ref-intro">Referencias en formato APA (7ª edición)</h4>';
    html += '<div class="im-bib-list">' + data.references.map(function(r) {
      var cls = "ref-item im-bib-item" + (r.key === highlightKey ? " im-bib-highlight" : "");
      return '<p class="' + cls + '" id="im-bib-' + r.key + '">' + imBibText(r.text) + "</p>";
    }).join("") + "</div>";
    root.innerHTML = html;
    root.querySelector("[data-im-back]").addEventListener("click", function() { imShowIndex(root, data); });
    if (highlightKey) {
      var el = document.getElementById("im-bib-" + highlightKey);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }
  function imShowChapter(root, data, idx) {
    var sec = data.sections[idx];
    var html = '<button class="im-crumb" data-im-back="1">← Índice del manual</button>';
    html += '<h3 class="im-chapter-title">' + imEsc(sec.title) + "</h3>";
    html += imRenderBlocks(sec.blocks, idx + "-i");
    sec.subsections.forEach(function(sub, j) {
      html += '<div class="im-sub" data-im-sub="' + j + '">' +
        '<button class="im-sub-head"><span class="im-sub-title">' + imEsc(sub.title) + '</span><span class="im-sub-arrow">▶</span></button>' +
        '<div class="im-sub-body">' + imRenderBlocks(sub.blocks, idx + "-" + j) + "</div></div>";
    });
    root.innerHTML = html;
    imWireCommon(root, data);
    root.querySelector("[data-im-back]").addEventListener("click", function() { imShowIndex(root, data); });
    root.querySelectorAll(".im-sub-head").forEach(function(head) {
      head.addEventListener("click", function() { head.parentElement.classList.toggle("open"); });
    });
  }
  function imShowIndex(root, data) {
    var cards = data.sections.map(function(sec, i) {
      return '<button class="im-card" data-im-chapter="' + i + '">' +
        '<span class="im-card-icon">📖</span>' +
        '<span class="im-card-num">Capítulo ' + (i + 1) + "</span>" +
        '<span class="im-card-title">' + imEsc(sec.title) + "</span>" +
        (sec.subsections.length ? '<span class="im-card-meta">' + sec.subsections.length + " apartados</span>" : "") +
        "</button>";
    }).join("");
    var bibCard = '<button class="im-card im-card-bib" data-im-bib="1">' +
      '<span class="im-card-icon">📚</span><span class="im-card-num">Referencias</span>' +
      '<span class="im-card-title">Bibliografía</span>' +
      '<span class="im-card-meta">' + data.references.length + ' referencias en APA 7ª ed.</span></button>';
    root.innerHTML = '<div class="im-grid">' + cards + bibCard + "</div>";
    root.querySelectorAll("[data-im-chapter]").forEach(function(btn) {
      btn.addEventListener("click", function() { imShowChapter(root, data, parseInt(btn.dataset.imChapter, 10)); });
    });
    var bibBtn = root.querySelector("[data-im-bib]");
    if (bibBtn) bibBtn.addEventListener("click", function() { imShowBib(root, data, null); });
  }
  function renderInteractiveManual(viewKey) {
    if (imRendered[viewKey]) return;
    imRendered[viewKey] = true;
    var data = IM_DATA[viewKey];
    if (!data) return;
    var root = document.getElementById("im-root-" + viewKey);
    if (!root) return;
    imShowIndex(root, data);
  }

  function wireNav() {
    document.querySelectorAll(".hub-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        showView(btn.dataset.view);
        if (btn.dataset.view === "quiz") renderQuizStart();
        if (IM_DATA[btn.dataset.view]) renderInteractiveManual(btn.dataset.view);
      });
    });
    document.querySelectorAll("[data-back]").forEach(function(btn) {
      btn.addEventListener("click", function() { showView(btn.dataset.back); });
    });
  }

  function applyStudentVisibility(config) {
    document.querySelectorAll(".hub-btn[data-type]").forEach(function(btn) {
      var t = btn.dataset.type;
      btn.style.display = config[t] ? "" : "none";
    });
  }

  function applyTeacherHints(config) {
    document.querySelectorAll(".teacher-hint[data-hint]").forEach(function(span) {
      var t = span.dataset.hint;
      var on = !!config[t];
      span.textContent = on ? "visible" : "oculto";
      span.className = "teacher-hint " + (on ? "on" : "off");
    });
    document.querySelectorAll("#teacher-panel input[type=checkbox][data-type]").forEach(function(chk) {
      chk.checked = !!config[chk.dataset.type];
    });
  }

  function fetchConfig() {
    return fetch(LOCAL_CONFIG + "?t=" + Date.now()).then(function(r) { return r.json(); });
  }

  function ghHeaders(token) {
    return { "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json" };
  }

  function ghGetFile(token) {
    return fetch("https://api.github.com/repos/" + REPO + "/contents/" + GH_CONFIG_PATH, { headers: ghHeaders(token) })
      .then(function(r) {
        if (!r.ok) throw new Error("No se pudo leer el fichero (" + r.status + ")");
        return r.json();
      })
      .then(function(data) {
        configSha = data.sha;
        return JSON.parse(decodeURIComponent(escape(atob(data.content.replace(/\\n/g, "")))));
      });
  }

  function ghSaveFile(token, configObj) {
    var content = btoa(unescape(encodeURIComponent(JSON.stringify(configObj, null, 2) + "\\n")));
    return fetch("https://api.github.com/repos/" + REPO + "/contents/" + GH_CONFIG_PATH, {
      method: "PUT",
      headers: Object.assign({ "Content-Type": "application/json" }, ghHeaders(token)),
      body: JSON.stringify({
        message: "Modo profesora: actualizar visibilidad de materiales (" + GH_CONFIG_PATH + ")",
        content: content,
        sha: configSha
      })
    }).then(function(r) {
      if (!r.ok) return r.text().then(function(t) { throw new Error("Error al guardar (" + r.status + "): " + t); });
      return r.json();
    }).then(function(data) {
      configSha = data.content.sha;
    });
  }

  function getToken() {
    try { return sessionStorage.getItem("gh_pat") || ""; } catch (e) { return ""; }
  }
  function setToken(t) {
    try { sessionStorage.setItem("gh_pat", t); } catch (e) {}
  }

  function setStatus(msg, isError) {
    var el = document.getElementById("teacher-status");
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? "#FFB3B3" : "#9FE6A0";
  }

  function initTeacherPanel() {
    document.getElementById("teacher-panel").hidden = false;
    var tokenInput = document.getElementById("gh-token");
    tokenInput.value = getToken();

    document.getElementById("gh-token-save").addEventListener("click", function() {
      setToken(tokenInput.value.trim());
      setStatus(tokenInput.value.trim() ? "Token guardado para esta sesión." : "Token borrado.");
      refreshFromGithub();
    });

    document.querySelectorAll("#teacher-panel input[type=checkbox][data-type]").forEach(function(chk) {
      chk.addEventListener("change", function() {
        var token = getToken();
        if (!token) { setStatus("Pega primero tu token de GitHub.", true); chk.checked = !chk.checked; return; }
        setStatus("Guardando...");
        ghGetFile(token).then(function(current) {
          current[chk.dataset.type] = chk.checked;
          return ghSaveFile(token, current).then(function() { return current; });
        }).then(function(current) {
          applyTeacherHints(current);
          setStatus("Guardado ✓ — el alumnado lo verá en 1-2 minutos.");
        }).catch(function(err) {
          chk.checked = !chk.checked;
          setStatus(err.message, true);
        });
      });
    });

    refreshFromGithub();

    function refreshFromGithub() {
      var token = getToken();
      if (!token) { fetchConfig().then(applyTeacherHints); return; }
      setStatus("Cargando estado actual...");
      ghGetFile(token).then(function(current) {
        applyTeacherHints(current);
        setStatus("Conectado. Puedes marcar/desmarcar materiales.");
      }).catch(function(err) { setStatus(err.message, true); fetchConfig().then(applyTeacherHints); });
    }
  }

  function reveal(teacherMode) {
    isTeacher = teacherMode;
    document.getElementById("content").innerHTML = decodeURIComponent(escape(atob(PAYLOAD)));
    document.getElementById("gate").style.display = "none";
    document.getElementById("page").style.display = "block";
    wireNav();
    if (teacherMode) {
      document.querySelectorAll(".hub-btn[data-type]").forEach(function(btn) { btn.style.display = ""; });
      initTeacherPanel();
    } else {
      fetchConfig().then(applyStudentVisibility);
    }
    try { sessionStorage.setItem(SESSION_KEY, teacherMode ? "teacher" : "1"); } catch (e) {}
  }

  function tryUnlock() {
    var val = document.getElementById("pw").value;
    sha256Hex(val).then(function(hex) {
      if (hex === TEACHER_HASH) { reveal(true); return; }
      if (hex === HASH) {
        fetch(ROOT_CONFIG + "?t=" + Date.now()).then(function(r) { return r.json(); }).then(function(rootCfg) {
          if (rootCfg[TEMA_KEY] === false) {
            document.getElementById("err").textContent = "Este tema no está disponible por el momento.";
          } else {
            reveal(false);
          }
        }).catch(function() { reveal(false); });
        return;
      }
      document.getElementById("err").textContent = "Contraseña incorrecta.";
    });
  }

  document.getElementById("enter").addEventListener("click", tryUnlock);
  document.getElementById("pw").addEventListener("keydown", function(e) { if (e.key === "Enter") tryUnlock(); });

  try {
    var saved = sessionStorage.getItem(SESSION_KEY);
    if (saved === "teacher") reveal(true);
    else if (saved === "1") reveal(false);
  } catch (e) {}
})();
</script>
</body>
</html>`;
}

function buildIndexHtml(temas) {
  const buttons = temas.map(t => `<a class="tema-btn" data-tema="${t.dir}" href="${t.dir}/index.html" style="display:none">
    <span class="teacher-hint" data-hint="${t.dir}"></span>
    <span class="tema-num">${esc(t.numLabel)}</span>
    <span class="tema-title">${esc(t.titleShort)}</span>
  </a>`).join('\n  ');
  const teacherHash = sha256(TEACHER_PASSWORD);
  const toggles = temas.map(t =>
    `<li><input type="checkbox" id="chk-tema-${t.dir}" data-tema="${t.dir}"><label for="chk-tema-${t.dir}">${esc(t.numLabel)} · ${esc(t.titleShort)}</label></li>`
  ).join('\n      ');
  const studentHash = sha256(STUDENT_PASSWORD);
  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Programación orientada a PLN</title>
<style>${CSS_INDEX}</style>
</head>
<body>

<div id="gate">
  <div class="box">
    <div class="kicker">Programación orientada a PLN</div>
    <h1>PLN</h1>
    <p>Contenido protegido. Introduce la contraseña facilitada en clase.</p>
    <input type="password" id="pw" placeholder="Contraseña" autofocus>
    <button class="submit" id="enter">Acceder</button>
    <div class="error" id="err"></div>
  </div>
</div>

<div id="page">
<header>
  <div class="kicker">Programación orientada a PLN</div>
  <h1>Materiales de la asignatura</h1>
  <p class="author">Dra. Blanca Hernández Pardo</p>
  <p>Elige un tema para acceder a su material</p>
</header>
<div class="teacher-wrap">
  <div id="teacher-panel-index" class="teacher-banner" hidden>
    <strong>⚙ Modo profesora</strong>
    <p>Pega aquí tu token de GitHub (solo para esta sesión de navegador; se pierde al cerrar la pestaña) y marca qué temas ve el alumnado. Los cambios se publican en 1-2 minutos.</p>
    <div class="teacher-token-row">
      <input type="password" id="gh-token" placeholder="Token de GitHub (ghp_... o github_pat_...)">
      <button id="gh-token-save">Guardar token de esta sesión</button>
    </div>
    <div class="teacher-status" id="teacher-status"></div>
    <ul class="teacher-toggle-list">
      ${toggles}
    </ul>
  </div>
</div>
<main>
  ${buttons}
</main>
<button class="teacher-link" id="teacher-toggle-link">⚙ Modo profesora</button>
<footer>
  ${copyrightFooter()}
</footer>
</div>

<script>
(function() {
  var HASH = "${studentHash}";
  var TEACHER_HASH = "${teacherHash}";
  var SESSION_KEY = "pln_unlocked";
  var REPO = "${REPO}";
  var LOCAL_CONFIG = "config.json";
  var GH_CONFIG_PATH = "config.json";
  var configSha = null;
  var isTeacher = false;

  function sha256Hex(text) {
    var enc = new TextEncoder().encode(text);
    return crypto.subtle.digest("SHA-256", enc).then(function(buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function(b) {
        return b.toString(16).padStart(2, "0");
      }).join("");
    });
  }

  function fetchConfig() {
    return fetch(LOCAL_CONFIG + "?t=" + Date.now()).then(function(r) { return r.json(); });
  }

  function ghHeaders(token) {
    return { "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json" };
  }

  function ghGetFile(token) {
    return fetch("https://api.github.com/repos/" + REPO + "/contents/" + GH_CONFIG_PATH, { headers: ghHeaders(token) })
      .then(function(r) {
        if (!r.ok) throw new Error("No se pudo leer el fichero (" + r.status + ")");
        return r.json();
      })
      .then(function(data) {
        configSha = data.sha;
        return JSON.parse(decodeURIComponent(escape(atob(data.content.replace(/\\n/g, "")))));
      });
  }

  function ghSaveFile(token, configObj) {
    var content = btoa(unescape(encodeURIComponent(JSON.stringify(configObj, null, 2) + "\\n")));
    return fetch("https://api.github.com/repos/" + REPO + "/contents/" + GH_CONFIG_PATH, {
      method: "PUT",
      headers: Object.assign({ "Content-Type": "application/json" }, ghHeaders(token)),
      body: JSON.stringify({
        message: "Modo profesora: actualizar visibilidad de temas (" + GH_CONFIG_PATH + ")",
        content: content,
        sha: configSha
      })
    }).then(function(r) {
      if (!r.ok) return r.text().then(function(t) { throw new Error("Error al guardar (" + r.status + "): " + t); });
      return r.json();
    }).then(function(data) {
      configSha = data.content.sha;
    });
  }

  function getToken() {
    try { return sessionStorage.getItem("gh_pat") || ""; } catch (e) { return ""; }
  }
  function setToken(t) {
    try { sessionStorage.setItem("gh_pat", t); } catch (e) {}
  }

  function setStatus(msg, isError) {
    var el = document.getElementById("teacher-status");
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? "#FFB3B3" : "#9FE6A0";
  }

  function applyVisibility(config) {
    document.querySelectorAll(".tema-btn[data-tema]").forEach(function(btn) {
      if (isTeacher) { btn.style.display = ""; return; }
      var k = btn.dataset.tema;
      btn.style.display = (config[k] === false) ? "none" : "";
    });
  }

  function applyTeacherHints(config) {
    document.querySelectorAll(".teacher-hint[data-hint]").forEach(function(span) {
      var k = span.dataset.hint;
      var on = config[k] !== false;
      span.textContent = on ? "visible" : "oculto";
      span.className = "teacher-hint " + (on ? "on" : "off");
    });
    document.querySelectorAll("#teacher-panel-index input[type=checkbox][data-tema]").forEach(function(chk) {
      chk.checked = config[chk.dataset.tema] !== false;
    });
  }

  function initTeacherPanel() {
    document.getElementById("teacher-panel-index").hidden = false;
    applyVisibility({});
    var tokenInput = document.getElementById("gh-token");
    tokenInput.value = getToken();

    document.getElementById("gh-token-save").addEventListener("click", function() {
      setToken(tokenInput.value.trim());
      setStatus(tokenInput.value.trim() ? "Token guardado para esta sesión." : "Token borrado.");
      refreshFromGithub();
    });

    document.querySelectorAll("#teacher-panel-index input[type=checkbox][data-tema]").forEach(function(chk) {
      chk.addEventListener("change", function() {
        var token = getToken();
        if (!token) { setStatus("Pega primero tu token de GitHub.", true); chk.checked = !chk.checked; return; }
        setStatus("Guardando...");
        ghGetFile(token).then(function(current) {
          current[chk.dataset.tema] = chk.checked;
          return ghSaveFile(token, current).then(function() { return current; });
        }).then(function(current) {
          applyTeacherHints(current);
          setStatus("Guardado ✓ — el alumnado lo verá en 1-2 minutos.");
        }).catch(function(err) {
          chk.checked = !chk.checked;
          setStatus(err.message, true);
        });
      });
    });

    refreshFromGithub();

    function refreshFromGithub() {
      var token = getToken();
      if (!token) { fetchConfig().then(applyTeacherHints); return; }
      setStatus("Cargando estado actual...");
      ghGetFile(token).then(function(current) {
        applyTeacherHints(current);
        setStatus("Conectado. Puedes marcar/desmarcar temas.");
      }).catch(function(err) { setStatus(err.message, true); fetchConfig().then(applyTeacherHints); });
    }
  }

  function reveal(teacherMode) {
    isTeacher = teacherMode;
    document.getElementById("gate").style.display = "none";
    document.getElementById("page").style.display = "flex";
    if (teacherMode) {
      initTeacherPanel();
    } else {
      fetchConfig().then(applyVisibility).catch(function() {});
    }
    try { sessionStorage.setItem(SESSION_KEY, teacherMode ? "teacher" : "1"); } catch (e) {}
  }

  function tryUnlock() {
    var val = document.getElementById("pw").value;
    sha256Hex(val).then(function(hex) {
      if (hex === TEACHER_HASH) { reveal(true); return; }
      if (hex === HASH) { reveal(false); return; }
      document.getElementById("err").textContent = "Contraseña incorrecta.";
    });
  }

  document.getElementById("enter").addEventListener("click", tryUnlock);
  document.getElementById("pw").addEventListener("keydown", function(e) { if (e.key === "Enter") tryUnlock(); });

  document.getElementById("teacher-toggle-link").addEventListener("click", function() {
    var val = prompt("Contraseña de profesora:");
    if (val === null) return;
    sha256Hex(val).then(function(hex) {
      if (hex === TEACHER_HASH) reveal(true);
      else alert("Contraseña incorrecta.");
    });
  });

  try {
    var saved = sessionStorage.getItem(SESSION_KEY);
    if (saved === "teacher") reveal(true);
    else if (saved === "1") reveal(false);
  } catch (e) {}
})();
</script>
</body>
</html>`;
}

// ---- Topic configuration ----
// "exists" = el material existe de verdad (hay fichero) y por tanto tiene botón/subvista construidos.
// La visibilidad real para el alumnado vive en tX/config.json (editable en vivo desde el modo profesora).
const TEMAS = [
  { dir: 'inicio', numLabel: 'INICIO', titleShort: 'Inicio', titleFull: 'Inicio', kicker: 'Inicio',
    viewOrder: ['vscode', 'ipynb', 'adicionales'],
    views: {
      vscode: { exists: true, kind: 'viewerdownload', label: 'Entornos de Python y VS Code', icon: '💻',
        desc: 'Guía de instalación y primeros pasos, para consultar o descargar', file: 'entornos_python_vscode.pdf' },
      ipynb: { exists: true, kind: 'viewerdownload', label: 'Trabajar con ficheros .ipynb', icon: '📓',
        desc: 'Cómo abrir, ejecutar y guardar cuadernos en Colab y VS Code, para consultar o descargar', file: 'trabajar_con_ipynb.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 27 de mayo', title: '5 mitos sobre la lingüística computacional', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DY2RmVODdai/' },
          { author: 'linguAIstica', date: '2026, 7 de agosto', title: 'La "prehistoria" del NLP conversacional: cuando los chatbots solo sabían seguir reglas', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DbvWKLWDyYp/' },
          { author: 'linguAIstica', date: '2026, 12 de agosto', title: 'La historia reciente del NLP conversacional: de los asistentes a los LLM', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/Db8iuToDcmG/' },
          { author: 'linguAIstica', date: '2026, 1 de agosto', title: 'Historia de los chatbots: de ELIZA a ChatGPT y más allá', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=uKnjZx3jKeg' },
          { author: 'linguAIstica', date: '2026, 15 de junio', title: 'Historia completa del NLP: de las reglas al deep learning', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=bFyUm1m2_4A' },
          { author: 'linguAIstica', date: '2026, 25 de mayo', title: '¿Qué hace un lingüista computacional?', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=HmM6Z5dfnoc' },
        ] },
    } },
  { dir: 't0a', numLabel: 'TEMA 0', titleShort: 'Recordatorio', titleFull: 'Tema 0 · Recordatorio de Python', kicker: 'Tema 0 · Recordatorio',
    viewOrder: ['manual','adicionales','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 24 de julio', title: 'Python para análisis de texto: tus primeras 6 armas', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DbLh6IEDZFS/' },
          { author: 'linguAIstica', date: '2026, 20 de julio', title: 'Python no muerde: por qué es la herramienta perfecta para lingüistas', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DbBNp_ijVEo/' },
          { author: 'linguAIstica', date: '2026, 15 de julio', title: 'Python para lingüistas aterrorizados (primeros pasos)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=LXpGwHU2eOM' },
          { author: 'linguAIstica', date: '2026, 20 de julio', title: 'Python para lingüistas: decisiones y herramientas', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/10pIuQ2DJHY' },
          { author: 'linguAIstica', date: '2026, 24 de julio', title: 'Python para lingüistas: organiza y automatiza', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/QB-UFoS52YA' },
        ] },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: false },
      practica: { exists: true, items: [
        { id: 'p1', label: 'Prácticas 1', file: 'practica.pdf' },
        { id: 'p2', label: 'Prácticas 2', file: 'practica2.pdf' }
      ] },
      quiz: { exists: false }
    } },
  { dir: 't0b', numLabel: 'TEMA 0', titleShort: 'Regex', titleFull: 'Tema 0 · Regex', kicker: 'Tema 0 · Regex',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb', note: 'Este cuaderno reúne teoría y práctica de Regex en un solo fichero.' },
      evaluable: { exists: false },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { exists: false }
    } },
  { dir: 't1', numLabel: 'TEMA 1', titleShort: 'Tema 1', titleFull: 'Tema 1', kicker: 'Tema 1',
    viewOrder: ['manual','manual_interactivo','adicionales','infografia','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      manual_interactivo: { exists: true, kind: 'interactive_manual', label: 'Manual teórico interactivo (prueba)', icon: '✨',
        desc: 'Mismo contenido del manual, navegable por paneles — versión de prueba', dataFile: 'manual_interactivo.json' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 1 de junio', title: 'Tokenización: el arte de cortar texto para que la IA lo entienda', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DZDa4tNjcOn/' },
          { author: 'linguAIstica', date: '2026, 1 de junio', title: 'Fundamentos del NLP: tokenización, stop words, stemming y lematización', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=KEww-OoMDLI' },
          { author: 'linguAIstica', date: '2026, 8 de julio', title: 'Tu texto se deshace así dentro de una IA', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/_guUwlMJqw8' },
          { author: 'linguAIstica', date: '2026, 27 de julio', title: 'Analizando obras literarias con Python (parte 1: importación con spaCy y NLTK)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/ja19CYEZ4kg' },
          { author: 'linguAIstica', date: '2026, 17 de agosto', title: 'Tokenización práctica: ejemplos en múltiples idiomas (¡parte 1!)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=H3vKfUj5ZSM' },
          { author: 'linguAIstica', date: '2026, 20 de agosto', title: '5 tokenizadores, una frase, 5 visiones', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/Wh35H7lOSxU' },
        ] },
      infografia: { exists: true, kind: 'image', label: 'Infografía', icon: '🖼️',
        desc: 'Resumen visual del tema, en imagen grande', file: 'infografia.png' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { exists: true }
    } },
  { dir: 't2', numLabel: 'TEMA 2', titleShort: 'Tema 2', titleFull: 'Tema 2', kicker: 'Tema 2',
    viewOrder: ['manual','adicionales','infografia','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 19 de junio', title: 'NLP antes del machine learning: la era de las reglas y la estadística', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DZxocbUDXtV/' },
          { author: 'linguAIstica', date: '2026, 7 de agosto', title: 'La "prehistoria" del NLP conversacional: cuando los chatbots solo sabían seguir reglas', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DbvWKLWDyYp/' },
          { author: 'linguAIstica', date: '2026, 1 de agosto', title: 'Historia de los chatbots: de ELIZA a ChatGPT y más allá', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=uKnjZx3jKeg' },
        ] },
      infografia: { exists: true, kind: 'image', label: 'Infografía', icon: '🖼️',
        desc: 'Resumen visual del tema, en imagen grande', file: 'infografia.png' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { exists: true }
    } },
  { dir: 't3', numLabel: 'TEMA 3', titleShort: 'Tema 3', titleFull: 'Tema 3', kicker: 'Tema 3',
    viewOrder: ['manual','adicionales','stopwords','pandas','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 25 de agosto', title: 'Errores de tokenización que arruinan proyectos multilingües', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/Dcd6OP7jdQv/' },
          { author: 'linguAIstica', date: '2026, 18 de agosto', title: 'Tipos de tokenización según el idioma que se trabaje: 5 estrategias para cortar los textos', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DcL4tvHDfEc/' },
          { author: 'linguAIstica', date: '2026, 15 de junio', title: 'Stop words, stemming y lematización: limpiando texto para la IA', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DZmnvaGDdAd/' },
          { author: 'linguAIstica', date: '2026, 17 de agosto', title: 'Tokenización práctica: ejemplos en múltiples idiomas (¡parte 1!)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=H3vKfUj5ZSM' },
          { author: 'linguAIstica', date: '2026, 24 de agosto', title: 'Tokenización práctica: ejemplos en múltiples idiomas (¡parte 2!)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=t4jCHD8kLss' },
          { author: 'linguAIstica', date: '2026, 20 de agosto', title: '5 tokenizadores, una frase, 5 visiones', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/Wh35H7lOSxU' },
          { author: 'linguAIstica', date: '2026, 25 de agosto', title: '¿Puede un sistema de NLP tokenizar mal y aun así "funcionar"?', type: 'Publicación', platform: 'LinkedIn', url: 'https://es.linkedin.com/posts/linguaistica_linguaistica-nlp-tokenizaci%C3%B3n-activity-7498031528334045184-ueIN' },
          { author: 'linguAIstica', date: '2026, 18 de agosto', title: '¿Y si tokenizar un texto no significara simplemente separarlo por espacios?', type: 'Publicación', platform: 'LinkedIn', url: 'https://es.linkedin.com/posts/linguaistica_linguaistica-nlp-tokenizaci%C3%B3n-activity-7495494733327310848-Dtsx' },
        ] },
      stopwords: { exists: true, kind: 'viewerdownload', label: 'Diferencias entre las stopwords de spaCy y NLTK', icon: '📄',
        desc: 'Documento comparativo, para consultar o descargar', file: 'stopwords.pdf' },
      pandas: { exists: true, kind: 'viewerdownload', label: 'Pandas para lingüistas', icon: '📄',
        desc: 'Guía práctica de pandas, para consultar o descargar', file: 'pandas.pdf' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [
        { id: 'p1', label: 'Prácticas 3.1', file: 'practica1.pdf' },
        { id: 'p2', label: 'Prácticas 3.2', file: 'practica2.pdf' }
      ] },
      quiz: { exists: true }
    } },
  { dir: 't4', numLabel: 'TEMA 4', titleShort: 'Tema 4', titleFull: 'Tema 4', kicker: 'Tema 4',
    viewOrder: ['manual','adicionales','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 19 de junio', title: 'NLP antes del machine learning: la era de las reglas y la estadística', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DZxocbUDXtV/' },
          { author: 'linguAIstica', date: '2026, 1 de agosto', title: 'Historia de los chatbots: de ELIZA a ChatGPT y más allá', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/watch?v=uKnjZx3jKeg' },
        ] },
      principal: { exists: true, file: 'cuaderno_principal.zip', note: 'Incluye el cuaderno y los dos ficheros de texto (texto1.txt, texto2.txt) que necesita para funcionar.' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }],
        extraDownload: { file: 'materiales_practica.zip', label: 'Descargar los 6 textos del corpus' } },
      quiz: { exists: true }
    } },
  { dir: 't5', numLabel: 'TEMA 5', titleShort: 'Tema 5', titleFull: 'Tema 5', kicker: 'Tema 5',
    viewOrder: ['manual','adicionales','principal','evaluable','practica','metric2','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 4 de julio', title: 'La IA traduce Shakespeare... pero no esto', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/yU7lt82hy_M' },
          { author: 'linguAIstica', date: '2026, 3 de julio', title: 'La IA reemplazará a los traductores', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/4z_qvGFZwCU' },
        ] },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      metric2: { exists: true, kind: 'download', label: 'Métricas parte II', icon: '📐',
        desc: 'Cuaderno complementario sobre METEOR, para descargar', file: 'metrica2.ipynb' },
      quiz: { exists: true }
    } },
  { dir: 't6', numLabel: 'TEMA 6', titleShort: 'Tema 6', titleFull: 'Tema 6', kicker: 'Tema 6',
    viewOrder: ['manual','adicionales','infografia','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 10 de agosto', title: 'El chatbot que se volvió n*zi en 24 horas', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/fCbntlnKXwg' },
          { author: 'linguAIstica', date: '2026, 10 de agosto', title: 'A veces, los mayores avances en inteligencia artificial nacen de sus mayores fracasos', type: 'Publicación', platform: 'LinkedIn', url: 'https://es.linkedin.com/posts/linguaistica_linguaistica-artificialintelligence-llm-activity-7492542781912158208-rSmX' },
        ] },
      infografia: { exists: true, kind: 'image', label: 'Infografía', icon: '🖼️',
        desc: 'Resumen visual del tema, en imagen grande', file: 'infografia.png' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: false },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { exists: true }
    } },
  { dir: 't7', numLabel: 'TEMA 7', titleShort: 'Tema 7', titleFull: 'Tema 7', kicker: 'Tema 7',
    viewOrder: ['manual','adicionales','infografia','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 29 de julio', title: 'Analizando obras literarias con Python (parte 3: definir qué buscamos)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/oE19LAsrVbw' },
        ] },
      infografia: { exists: true, kind: 'image', label: 'Infografía', icon: '🖼️',
        desc: 'Resumen visual del tema, en imagen grande', file: 'infografia.png' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { exists: true }
    } },
  { dir: 't8', numLabel: 'TEMA 8', titleShort: 'Tema 8', titleFull: 'Tema 8', kicker: 'Tema 8',
    viewOrder: ['manual','adicionales','infografia','principal','evaluable','practica','quiz'],
    views: {
      manual: { exists: true, file: 'manual.pdf' },
      adicionales: { exists: true, kind: 'reflist', label: 'Conocimientos adicionales', icon: '🔗',
        desc: 'Recursos externos recomendados (LinguAIstica)', refs: [
          { author: 'linguAIstica', date: '2026, 12 de julio', title: 'El PDF que cambió el mundo (Attention is all you need)', type: 'Vídeo', platform: 'YouTube', url: 'https://www.youtube.com/shorts/2OJT5H0wnio' },
          { author: 'linguAIstica', date: '2026, 25 de junio', title: 'NLP moderno: deep learning, transformers y la revolución actual', type: 'Carrusel de fotos', platform: 'Instagram', url: 'https://www.instagram.com/linguaistica/p/DaBBKuJDa3v/' },
        ] },
      infografia: { exists: true, kind: 'image', label: 'Infografía', icon: '🖼️',
        desc: 'Resumen visual del tema, en imagen grande', file: 'infografia.png' },
      principal: { exists: true, file: 'cuaderno_principal.ipynb' },
      evaluable: { exists: true, file: 'evaluable.ipynb' },
      practica: { exists: true, items: [
        { id: 'sms', label: 'Clasificación de SMS', file: 'practica_sms.pdf' },
        { id: 'agnews', label: 'Clasificación AG News', file: 'practica_agnews.pdf' },
        { id: 'imdb', label: 'Clasificación IMDB', file: 'practica_imdb.pdf' }
      ] },
      quiz: { exists: true }
    } }
];

module.exports = { TEMAS, buildTopicHtml, buildIndexHtml, existingViews, TEACHER_PASSWORD, STUDENT_PASSWORD };

if (require.main === module) {
  for (const tema of TEMAS) {
    const html = buildTopicHtml(tema);
    fs.writeFileSync(path.join(ROOT, tema.dir, 'index.html'), html, 'utf8');

    // Only (re)seed config.json if it doesn't already exist, so live teacher toggles
    // made via GitHub are never clobbered by a later `node build.js` run.
    const configPath = path.join(ROOT, tema.dir, 'config.json');
    if (!fs.existsSync(configPath)) {
      const seed = {};
      existingViews(tema).forEach(v => { seed[v] = v === 'manual'; });
      fs.writeFileSync(configPath, JSON.stringify(seed, null, 2) + '\n', 'utf8');
      console.log('seeded config for', tema.dir, seed);
    }
    console.log('built', tema.dir);
  }
  fs.writeFileSync(path.join(ROOT, 'index.html'), buildIndexHtml(TEMAS), 'utf8');
  console.log('built index.html');

  // Root-level config.json controls whether each topic's card/link is shown at all.
  // Only seeded if missing, so it never clobbers a live teacher toggle.
  const rootConfigPath = path.join(ROOT, 'config.json');
  if (!fs.existsSync(rootConfigPath)) {
    const rootSeed = {};
    TEMAS.forEach(t => { rootSeed[t.dir] = true; });
    fs.writeFileSync(rootConfigPath, JSON.stringify(rootSeed, null, 2) + '\n', 'utf8');
    console.log('seeded root config.json', rootSeed);
  }

  console.log('\nContraseña del alumnado (todas las páginas):', STUDENT_PASSWORD);
  console.log('Contraseña de profesora (todas las páginas):', TEACHER_PASSWORD);
}
