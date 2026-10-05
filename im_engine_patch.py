# -*- coding: utf-8 -*-
"""Parche del motor de manuales interactivos en build.js (se aplica una sola vez).

Añade: vista ancha y modo pantalla completa, lema narrativo en la portada,
paginador anterior/siguiente, capítulos leídos, lista de comprobación en
«Qué vas a aprender», tarjetas que se destapan en «Errores frecuentes», y los
bloques docimg (figuras del documento) y biblist (lista de recursos).
"""
p = 'build.js'
s = open(p).read()


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:70], s.count(old))
    s = s.replace(old, new)


# ---------- CSS
rep(".im-root { margin-top:0; }", """.im-root { margin-top:0; }
.im-view .im-root { width:min(1320px, 96vw); margin-left:calc(50% - min(660px, 48vw)); }
.im-root:fullscreen { width:100%; margin:0; background:#fff; overflow:auto; padding:22px clamp(16px,4vw,56px) 40px; box-sizing:border-box; }
.im-root:-webkit-full-screen { width:100%; margin:0; background:#fff; overflow:auto; padding:22px clamp(16px,4vw,56px) 40px; box-sizing:border-box; }
.im-hero-tools { position:absolute; top:16px; right:16px; display:flex; gap:8px; z-index:1; flex-wrap:wrap; justify-content:flex-end; }
.im-hero-tools .im-hero-dl { position:static; }
.im-fs-btn { background:rgba(255,255,255,.14); color:#fff; border:1.5px solid rgba(255,255,255,.55); border-radius:20px; padding:8px 14px; font-size:12px; font-weight:bold; cursor:pointer; font-family:Arial,Helvetica,sans-serif; }
.im-fs-btn:hover { background:rgba(255,255,255,.26); }
.im-rail .im-fs-rail { margin-left:auto; }
.im-hero-lema { color:#fff; opacity:.86; font-style:italic; font-size:14.5px; line-height:1.5; margin:12px 0 0; max-width:720px; position:relative; z-index:1; }
.im-card { position:relative; }
.im-card.visited::after { content:"✓ leído"; position:absolute; top:12px; right:12px; font-size:10.5px; font-weight:bold; color:var(--verde); background:#DFF3E0; border-radius:10px; padding:2px 8px; }
.im-progress { font-size:12.5px; color:var(--humo); margin:-8px 0 14px; }
.im-docimg { margin:8px 0 18px; text-align:center; }
.im-docimg img { max-width:100%; max-height:60vh; height:auto; cursor:zoom-in; border-radius:6px; }
.im-biblist { list-style:none; padding:0; margin:0 0 8px; }
.im-biblist li { background:var(--claro); border-left:3px solid var(--amar); border-radius:0 8px 8px 0; padding:10px 14px; margin-bottom:8px; font-size:13.5px; line-height:1.55; color:var(--gris); }
.im-biblist a { color:var(--azul); word-break:break-word; }
.im-check { list-style:none; padding:0; margin:0 0 14px; }
.im-check li { margin-bottom:8px; }
.im-check label { display:flex; gap:10px; align-items:flex-start; cursor:pointer; font-size:14.5px; line-height:1.55; color:var(--gris); background:var(--claro); border-radius:10px; padding:10px 14px; }
.im-check input { margin-top:4px; accent-color:var(--azul); width:16px; height:16px; flex:none; }
.im-check input:checked + span { text-decoration:line-through; text-decoration-color:var(--humo); color:var(--humo); }
.im-check-hint { font-size:12.5px; color:var(--humo); margin:0 0 10px; font-style:italic; }
.im-errorlist li.im-err-reveal { cursor:pointer; }
.im-errorlist li.im-err-reveal .im-error-desc { display:none; }
.im-errorlist li.im-err-reveal.open .im-error-desc { display:block; animation:imFadeIn .2s ease; }
.im-errorlist li.im-err-reveal .im-err-cta { display:inline-block; font-size:11.5px; font-weight:bold; color:var(--azul); margin-top:4px; }
.im-errorlist li.im-err-reveal.open .im-err-cta { display:none; }
.im-pager { display:flex; justify-content:space-between; gap:12px; margin:30px 0 6px; flex-wrap:wrap; }
.im-pager button { background:#fff; border:1.5px solid var(--azul); color:var(--azul); border-radius:22px; padding:9px 16px; font-size:13px; font-weight:bold; cursor:pointer; font-family:Arial,Helvetica,sans-serif; max-width:48%; }
.im-pager button:hover { background:var(--azul); color:#fff; }
.im-pager .im-next { margin-left:auto; }""")
rep("  .im-hero-dl { position:static; display:flex;",
    "  .im-hero-tools { position:static; margin:0 0 14px; justify-content:stretch; }\n"
    "  .im-hero-tools > * { flex:1; text-align:center; justify-content:center; }\n"
    "  .im-hero-dl { position:static; display:flex;")

# ---------- vista
rep('<div id="view-${viewKey}" class="view sub-view" hidden>\n  <button class="back-btn" data-back="hub">← Volver</button>\n  <div id="im-root-${viewKey}"',
    '<div id="view-${viewKey}" class="view sub-view im-view" hidden>\n  <button class="back-btn" data-back="hub">← Volver</button>\n  <div id="im-root-${viewKey}"')

# ---------- iconos
rep('''    "Síntesis": "✅", "Cierre narrativo": "🎬"
  };''', '''    "Síntesis": "✅", "Cierre narrativo": "🎬",
    "Reglas y análisis avanzado": "⚖️", "Buenas prácticas": "🧭", "Para saber más": "🔭"
  };''')

# ---------- modal dentro del elemento a pantalla completa
rep("    document.body.appendChild(overlay);\n    function close()",
    "    (document.fullscreenElement || document.webkitFullscreenElement || document.body).appendChild(overlay);\n    function close()")

# ---------- bloques nuevos y errores que se destapan
rep('''      else if (b.type === "errorlist") html += '<ul class="im-errorlist">' + b.items.map(function(it) {
        return '<li><span class="im-error-term">' + imFormatInline(it.term) + '</span><span class="im-error-desc">' + imFormatInline(it.desc) + "</span></li>";
      }).join("") + "</ul>";''', '''      else if (b.type === "errorlist") html += '<p class="im-check-hint">Antes de abrir cada error, piensa por qué es un error. Después, toca la tarjeta para comprobarlo.</p>' +
        '<ul class="im-errorlist">' + b.items.map(function(it) {
        return '<li class="im-err-reveal"><span class="im-error-term">' + imFormatInline(it.term) + '</span><span class="im-err-cta">¿Por qué es un error? Toca para verlo ▸</span><span class="im-error-desc">' + imFormatInline(it.desc) + "</span></li>";
      }).join("") + "</ul>";
      else if (b.type === "docimg") html += '<figure class="im-docimg"><img class="im-docimg-img" src="' + imEsc(b.src) + '" alt="' + imEsc(b.alt || "") + '"></figure>';
      else if (b.type === "biblist") html += '<ul class="im-biblist">' + b.items.map(function(t) { return "<li>" + imBibText(t) + "</li>"; }).join("") + "</ul>";''')

# ---------- utilidades: lista de comprobación, leídos, pantalla completa
rep('''  function imRenderBlocks(blocks, keyPrefix) {
    var html = "";''', '''  function imCheckKey(root, idx) { return "im-check:" + location.pathname + ":" + root.id + ":" + idx; }
  function imRenderChecklist(root, idx, blocks) {
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(imCheckKey(root, idx)) || "{}"); } catch (e) {}
    var n = 0, html = '<p class="im-check-hint">Marca lo que ya sabrías explicar con tus palabras. Se guarda en este navegador.</p>';
    blocks.forEach(function(b, bi) {
      if (b.type === "ul" || b.type === "ol") {
        html += '<ul class="im-check">' + b.items.map(function(t) {
          var k = n++;
          return '<li><label><input type="checkbox" data-im-check="' + k + '"' + (saved[k] ? " checked" : "") + "><span>" + imFormatInline(t) + "</span></label></li>";
        }).join("") + "</ul>";
      } else html += imRenderBlocks([b], idx + "-c" + bi);
    });
    return html;
  }
  function imVisitedKey(root) { return "im-visited:" + location.pathname + ":" + root.id; }
  function imGetVisited(root) { try { return JSON.parse(localStorage.getItem(imVisitedKey(root)) || "{}"); } catch (e) { return {}; } }
  function imMarkVisited(root, idx) { try { var v = imGetVisited(root); v[idx] = 1; localStorage.setItem(imVisitedKey(root), JSON.stringify(v)); } catch (e) {} }
  function imFsElement() { return document.fullscreenElement || document.webkitFullscreenElement; }
  function imToggleFullscreen(root) {
    if (imFsElement()) { (document.exitFullscreen || document.webkitExitFullscreen).call(document); return; }
    var req = root.requestFullscreen || root.webkitRequestFullscreen;
    if (req) req.call(root);
  }
  function imFsLabel() { return imFsElement() ? "✕ Salir de pantalla completa" : "⛶ Pantalla completa"; }
  ["fullscreenchange", "webkitfullscreenchange"].forEach(function(ev) {
    document.addEventListener(ev, function() {
      document.querySelectorAll(".im-fs-btn").forEach(function(btn) { btn.textContent = imFsLabel(); });
      document.querySelectorAll(".im-fs-rail .im-rail-label").forEach(function(l) { l.textContent = imFsElement() ? "Salir" : "Pantalla"; });
    });
  });
  function imScrollTop(root) {
    if (imFsElement() === root) { root.scrollTop = 0; return; }
    var y = root.getBoundingClientRect().top + window.pageYOffset - 20;
    if (window.pageYOffset > y) window.scrollTo(0, y);
  }
  function imRenderBlocks(blocks, keyPrefix) {
    var html = "";''')

# ---------- wiring común
rep('''  function imWireCommon(root, data) {''', '''  function imWireCommon(root, data) {
    root.querySelectorAll(".im-err-reveal").forEach(function(li) {
      li.addEventListener("click", function() { li.classList.toggle("open"); });
    });
    root.querySelectorAll(".im-docimg-img").forEach(function(img) {
      img.addEventListener("click", function() { imOpenModal("Figura del manual", '<img src="' + img.src + '" alt="">', true); });
    });
    root.querySelectorAll("[data-im-check]").forEach(function(cb) {
      cb.addEventListener("change", function() {
        var key = cb.closest("[data-im-checklist]").dataset.imChecklist, saved = {};
        try { saved = JSON.parse(localStorage.getItem(key) || "{}"); } catch (e) {}
        if (cb.checked) saved[cb.dataset.imCheck] = 1; else delete saved[cb.dataset.imCheck];
        try { localStorage.setItem(key, JSON.stringify(saved)); } catch (e) {}
      });
    });''')

# ---------- carril: botón de pantalla completa
rep('''    return '<div class="im-rail">' + items + "</div>";''', '''    items += '<button class="im-rail-btn im-fs-rail" data-im-fs-rail="1" title="Pantalla completa"><span class="im-rail-icon">⛶</span><span class="im-rail-label">' + (imFsElement() ? "Salir" : "Pantalla") + "</span></button>";
    return '<div class="im-rail">' + items + "</div>";''')
rep('''    var railBib = root.querySelector("[data-im-rail-bib]");
    if (railBib) railBib.addEventListener("click", function() { imShowBib(root, data, null); });''', '''    var railBib = root.querySelector("[data-im-rail-bib]");
    if (railBib) railBib.addEventListener("click", function() { imShowBib(root, data, null); });
    var railFs = root.querySelector("[data-im-fs-rail]");
    if (railFs) railFs.addEventListener("click", function() { imToggleFullscreen(root); });''')

# ---------- capítulo: lista de comprobación, paginador, leído
rep('''    html += '<div class="im-chapter"><h3 class="im-chapter-title">' + icon + " " + imFormatInline(sec.title) + "</h3>";
    html += imRenderBlocks(sec.blocks, idx + "-i");''', '''    html += '<div class="im-chapter"><h3 class="im-chapter-title">' + icon + " " + imFormatInline(sec.title) + "</h3>";
    if (sec.navTitle === "Qué vas a aprender") html += '<div data-im-checklist="' + imCheckKey(root, idx) + '">' + imRenderChecklist(root, idx, sec.blocks) + "</div>";
    else html += imRenderBlocks(sec.blocks, idx + "-i");''')
rep('''        '<div class="im-sub-body">' + imRenderBlocks(sub.blocks, idx + "-" + j) + "</div></div>";
    });
    html += "</div>";
    root.innerHTML = html;''', '''        '<div class="im-sub-body">' + imRenderBlocks(sub.blocks, idx + "-" + j) + "</div></div>";
    });
    var prev = data.sections[idx - 1], next = data.sections[idx + 1];
    html += '<div class="im-pager">' +
      (prev ? '<button class="im-prev" data-im-goto="' + (idx - 1) + '">← ' + imEsc(prev.navTitle) + "</button>" : "") +
      (next ? '<button class="im-next" data-im-goto="' + (idx + 1) + '">' + imEsc(next.navTitle) + " →</button>"
            : (data.references && data.references.length ? '<button class="im-next" data-im-goto="bib">Bibliografía →</button>' : "")) +
      "</div>";
    html += "</div>";
    root.innerHTML = html;
    imMarkVisited(root, idx);
    imScrollTop(root);
    root.querySelectorAll("[data-im-goto]").forEach(function(btn) {
      btn.addEventListener("click", function() {
        if (btn.dataset.imGoto === "bib") imShowBib(root, data, null);
        else imShowChapter(root, data, parseInt(btn.dataset.imGoto, 10));
      });
    });''')

# ---------- índice: lema, pantalla completa, leídos
rep('''    var pdf = root.dataset.pdf;
    var cards = data.sections.map(function(sec, i) {''', '''    var pdf = root.dataset.pdf;
    var visited = imGetVisited(root);
    var nVisited = data.sections.filter(function(s, i) { return visited[i]; }).length;
    var cards = data.sections.map(function(sec, i) {''')
rep('''      return '<button class="im-card" data-im-chapter="' + i + '" style="animation-delay:' + (i * 0.04) + 's">' +''',
    '''      return '<button class="im-card' + (visited[i] ? " visited" : "") + '" data-im-chapter="' + i + '" style="animation-delay:' + (i * 0.04) + 's">' +''')
rep('''    var hero = '<div class="im-hero">' +
      (pdf ? '<a class="im-hero-dl" href="' + imEsc(pdf) + '" download>⬇ Descargar manual en PDF</a>' : "") +
      '<div class="im-hero-kicker">' + imEsc(data.header.kicker) + " · " + imEsc(data.header.title) + "</div>" +
      '<h1 class="im-hero-title">' + imEsc(data.header.subtitle) + "</h1></div>";
    root.innerHTML = hero + '<div class="im-grid">' + cards + bibCard + "</div>";''', '''    var hero = '<div class="im-hero"><div class="im-hero-tools">' +
      '<button class="im-fs-btn">' + imFsLabel() + "</button>" +
      (pdf ? '<a class="im-hero-dl" href="' + imEsc(pdf) + '" download>⬇ Descargar manual en PDF</a>' : "") + "</div>" +
      '<div class="im-hero-kicker">' + imEsc(data.header.kicker) + " · " + imEsc(data.header.title) + "</div>" +
      '<h1 class="im-hero-title">' + imEsc(data.header.subtitle) + "</h1>" +
      (data.header.narrative ? '<p class="im-hero-lema">' + imEsc(data.header.narrative) + "</p>" : "") + "</div>";
    var progress = nVisited ? '<p class="im-progress">Has abierto ' + nVisited + " de " + data.sections.length + " capítulos.</p>" : "";
    root.innerHTML = hero + progress + '<div class="im-grid">' + cards + bibCard + "</div>";
    root.querySelector(".im-fs-btn").addEventListener("click", function() { imToggleFullscreen(root); });
    imScrollTop(root);''')

open(p, 'w').write(s)
print('motor parcheado')
