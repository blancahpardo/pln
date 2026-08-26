const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = __dirname;

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
header { padding: 60px 6vw 20px; text-align:center; }
header .kicker { color: var(--amar); font-size:12px; font-weight:bold; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:10px; }
header h1 { color:#fff; font-size:clamp(26px,4.2vw,40px); margin:0 0 10px; }
header p { color: var(--humo); font-size:14px; margin:0; }
main { flex:1; max-width:1000px; width:100%; margin:0 auto; padding:40px 6vw 60px; display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:22px; align-content:start; }
.tema-btn { display:flex; flex-direction:column; align-items:flex-start; gap:8px; background:#fff; border:none; border-radius:14px; padding:28px 24px; text-decoration:none; box-shadow:0 4px 16px rgba(0,0,0,.18); transition:transform .15s ease; }
.tema-btn:hover { transform:translateY(-3px); }
.tema-num { font-size:13px; font-weight:bold; color:var(--amar); background:var(--azul); padding:4px 12px; border-radius:20px; letter-spacing:1px; }
.tema-title { font-size:19px; font-weight:bold; color:var(--azul); margin-top:4px; }
footer { text-align:center; padding:20px 6vw 34px; font-size:11px; color:var(--humo); font-style:italic; }
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
.hub-btn { display:flex; flex-direction:column; align-items:flex-start; gap:6px; background:var(--claro); border:none; border-radius:12px; padding:26px 22px; cursor:pointer; text-align:left; box-shadow:0 2px 10px rgba(159,177,186,.28); font-family:Arial,Helvetica,sans-serif; }
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

function buildHub(tema) {
  const buttons = tema.viewOrder.filter(v => tema.views[v] && tema.views[v].enabled).map(v => {
    return `<button class="hub-btn" data-view="${v}">
      <span class="hub-icon">${ICONS[v]}</span>
      <span class="hub-label">${LABELS[v]}</span>
      <span class="hub-desc">${DESCS[v]}</span>
    </button>`;
  }).join('\n    ');
  return `<div id="hub" class="view">
  <div class="kicker">${esc(tema.kicker)}</div>
  <h1>¿Qué quieres consultar?</h1>
  <div class="hub-grid">
    ${buttons}
  </div>
  <a class="back-home" href="../index.html">← Volver a la asignatura</a>
</div>`;
}

function buildManualView(tema) {
  if (!tema.views.manual || !tema.views.manual.enabled) return '';
  const f = tema.views.manual.file;
  return `<div id="view-manual" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Manual teórico · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Puedes leerlo aquí o descargarlo.</p>
  <a class="dl-big" href="${f}" download>⬇ Descargar PDF</a>
  <iframe class="pdf-frame" src="${f}" title="Manual teórico ${esc(tema.titleShort)}"></iframe>
</div>`;
}

function buildDownloadView(viewKey, tema) {
  const cfg = tema.views[viewKey];
  if (!cfg || !cfg.enabled) return '';
  const label = LABELS[viewKey];
  return `<div id="view-${viewKey}" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>${label} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">${cfg.note || 'Descarga el fichero para trabajar con él en tu ordenador.'}</p>
  <a class="dl-big" href="${cfg.file}" download>⬇ Descargar</a>
</div>`;
}

function buildPracticaView(tema) {
  const cfg = tema.views.practica;
  if (!cfg || !cfg.enabled) return '';
  if (cfg.items.length === 1) {
    const it = cfg.items[0];
    return `<div id="view-practica" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Prácticas · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Documento de la práctica. Solo lectura, sin descarga.</p>
  <iframe class="pdf-frame" src="${it.file}#toolbar=0&navpanes=0" title="Práctica ${esc(tema.titleShort)}"></iframe>
</div>`;
  }
  // multiple practices -> sub-hub with its own buttons, then leaf viewers
  const subButtons = cfg.items.map(it => `<button class="hub-btn" data-view="practica-${it.id}">
      <span class="hub-icon">🧪</span>
      <span class="hub-label">${esc(it.label)}</span>
      <span class="hub-desc">Documento de la práctica (solo lectura)</span>
    </button>`).join('\n    ');
  const leaves = cfg.items.map(it => `<div id="view-practica-${it.id}" class="view sub-view" hidden>
  <button class="back-btn" data-back="practica">← Volver</button>
  <h2>${esc(it.label)} · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Documento de la práctica. Solo lectura, sin descarga.</p>
  <iframe class="pdf-frame" src="${it.file}#toolbar=0&navpanes=0" title="${esc(it.label)}"></iframe>
</div>`).join('\n');
  return `<div id="view-practica" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Prácticas · ${esc(tema.titleShort)}</h2>
  <p class="section-note">Elige la práctica que quieras consultar.</p>
  <div class="hub-grid">
    ${subButtons}
  </div>
</div>
${leaves}`;
}

function buildQuizView(tema) {
  const cfg = tema.views.quiz;
  if (!cfg || !cfg.enabled) return '';
  return `<div id="view-quiz" class="view sub-view" hidden>
  <button class="back-btn" data-back="hub">← Volver</button>
  <h2>Cuestionario de práctica · ${esc(tema.titleShort)}</h2>
  <div id="quiz-root"></div>
</div>`;
}

function buildTopicHtml(tema) {
  const payloadHtml = [
    buildHub(tema),
    buildManualView(tema),
    buildDownloadView('principal', tema),
    buildDownloadView('evaluable', tema),
    buildPracticaView(tema),
    buildQuizView(tema)
  ].filter(Boolean).join('\n');

  const hash = sha256(tema.password);
  const payloadB64 = b64(payloadHtml);

  let quizManual = '[]', quizCuaderno = '[]';
  if (tema.views.quiz && tema.views.quiz.enabled) {
    quizManual = JSON.stringify(JSON.parse(fs.readFileSync(path.join(ROOT, tema.dir, 'quiz_manual.json'), 'utf8')).quiz);
    quizCuaderno = JSON.stringify(JSON.parse(fs.readFileSync(path.join(ROOT, tema.dir, 'quiz_cuaderno.json'), 'utf8')).quiz);
  }

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
  var PAYLOAD = "${payloadB64}";
  var QUIZ_MANUAL = ${quizManual};
  var QUIZ_CUADERNO = ${quizCuaderno};
  var SESSION_KEY = "${tema.dir}_unlocked";

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

  function wireNav() {
    document.querySelectorAll(".hub-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        showView(btn.dataset.view);
        if (btn.dataset.view === "quiz") renderQuizStart();
      });
    });
    document.querySelectorAll("[data-back]").forEach(function(btn) {
      btn.addEventListener("click", function() { showView(btn.dataset.back); });
    });
  }

  function reveal() {
    document.getElementById("content").innerHTML = decodeURIComponent(escape(atob(PAYLOAD)));
    document.getElementById("gate").style.display = "none";
    document.getElementById("page").style.display = "block";
    wireNav();
    try { sessionStorage.setItem(SESSION_KEY, "1"); } catch (e) {}
  }

  function tryUnlock() {
    var val = document.getElementById("pw").value;
    sha256Hex(val).then(function(hex) {
      if (hex === HASH) reveal();
      else document.getElementById("err").textContent = "Contraseña incorrecta.";
    });
  }

  document.getElementById("enter").addEventListener("click", tryUnlock);
  document.getElementById("pw").addEventListener("keydown", function(e) { if (e.key === "Enter") tryUnlock(); });

  try { if (sessionStorage.getItem(SESSION_KEY) === "1") reveal(); } catch (e) {}
})();
</script>
</body>
</html>`;
}

function buildIndexHtml(temas) {
  const buttons = temas.map(t => `<a class="tema-btn" href="${t.dir}/index.html">
    <span class="tema-num">${esc(t.numLabel)}</span>
    <span class="tema-title">${esc(t.titleShort)}</span>
  </a>`).join('\n  ');
  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Programación orientada a PLN</title>
<style>${CSS_INDEX}</style>
</head>
<body>
<header>
  <div class="kicker">Programación orientada a PLN</div>
  <h1>Materiales de la asignatura</h1>
  <p>Elige un tema para acceder a su material</p>
</header>
<main>
  ${buttons}
</main>
<footer>
  ${copyrightFooter()}
</footer>
</body>
</html>`;
}

// ---- Topic configuration ----
const TEMAS = [
  { dir: 't0a', numLabel: 'TEMA 0', titleShort: 'Recordatorio', titleFull: 'Tema 0 · Recordatorio de Python', kicker: 'Tema 0 · Recordatorio', password: 't0_alcachofa',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false },
      practica: { enabled: false, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { enabled: false }
    } },
  { dir: 't0b', numLabel: 'TEMA 0', titleShort: 'Regex', titleFull: 'Tema 0 · Regex', kicker: 'Tema 0 · Regex', password: 't0_playa',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb', note: 'Este cuaderno reúne teoría y práctica de Regex en un solo fichero.' },
      evaluable: { enabled: false },
      practica: { enabled: false, items: [{ id: 'unica', label: 'Prácticas', file: 'practica.pdf' }] },
      quiz: { enabled: false }
    } },
  { dir: 't1', numLabel: 'TEMA 1', titleShort: 'Tema 1', titleFull: 'Tema 1', kicker: 'Tema 1', password: 't1_mariflor',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't2', numLabel: 'TEMA 2', titleShort: 'Tema 2', titleFull: 'Tema 2', kicker: 'Tema 2', password: 't2_cortavientos',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't3', numLabel: 'TEMA 3', titleShort: 'Tema 3', titleFull: 'Tema 3', kicker: 'Tema 3', password: 't3_boina',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't4', numLabel: 'TEMA 4', titleShort: 'Tema 4', titleFull: 'Tema 4', kicker: 'Tema 4', password: 't4_chascarrillo',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.zip', note: 'Incluye el cuaderno y los dos ficheros de texto (texto1.txt, texto2.txt) que necesita para funcionar.' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't5', numLabel: 'TEMA 5', titleShort: 'Tema 5', titleFull: 'Tema 5', kicker: 'Tema 5', password: 't5_cangrejo',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't6', numLabel: 'TEMA 6', titleShort: 'Tema 6', titleFull: 'Tema 6', kicker: 'Tema 6', password: 't6_ibuprofeno',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't7', numLabel: 'TEMA 7', titleShort: 'Tema 7', titleFull: 'Tema 7', kicker: 'Tema 7', password: 't7_cantamañanas',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [] },
      quiz: { enabled: false }
    } },
  { dir: 't8', numLabel: 'TEMA 8', titleShort: 'Tema 8', titleFull: 'Tema 8', kicker: 'Tema 8', password: 't8_pagafantas',
    viewOrder: ['manual','principal','evaluable','practica','quiz'],
    views: {
      manual: { enabled: true, file: 'manual.pdf' },
      principal: { enabled: false, file: 'cuaderno_principal.ipynb' },
      evaluable: { enabled: false, file: 'evaluable.ipynb' },
      practica: { enabled: false, items: [
        { id: 'sms', label: 'Clasificación de SMS', file: 'practica_sms.pdf' },
        { id: 'agnews', label: 'Clasificación AG News', file: 'practica_agnews.pdf' },
        { id: 'imdb', label: 'Clasificación IMDB', file: 'practica_imdb.pdf' }
      ] },
      quiz: { enabled: false }
    } }
];
// fix t0b manual to use the notebook-as-manual convention note (handled specially below)

module.exports = { TEMAS, buildTopicHtml, buildIndexHtml };

if (require.main === module) {
  for (const tema of TEMAS) {
    const html = buildTopicHtml(tema);
    fs.writeFileSync(path.join(ROOT, tema.dir, 'index.html'), html, 'utf8');
    console.log('built', tema.dir);
  }
  fs.writeFileSync(path.join(ROOT, 'index.html'), buildIndexHtml(TEMAS), 'utf8');
  console.log('built index.html');
}
