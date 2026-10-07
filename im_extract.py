# -*- coding: utf-8 -*-
"""Extractor común docx -> manual_interactivo.json (temas 3-8).

Generaliza build_manual_interactivo_*.py: mismo modelo de datos que el motor de
build.js, y además
  - extrae las imágenes incrustadas del docx en su posición exacta (fórmulas,
    figuras) y las guarda en tX/img/;
  - enlaza las citas en el texto con la bibliografía por (apellido, año), sin
    lista manual, e informa de las que no encuentra;
  - titula cada tabla para su ventana emergente.
Uso: python3 im_extract.py <tema>   (la configuración de cada tema está en TEMAS).
Nunca añade ni quita contenido: solo reorganiza la presentación.
"""
import io, json, os, re, sys, unicodedata
import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

BASE = ("/Users/blanca/Library/CloudStorage/OneDrive-UniversidadPontificiaComillas/2. Trabajo/"
        "4. UPComillas/1. Docencia UPCO/21. Programación para PLN/")
SITE = os.path.dirname(os.path.abspath(__file__))

TEMAS = {
    't3': '3. PLN 3/0. Teoría/Teoría_PLN3_act_v2.docx',
    't4': 'manuales 2027/Tema 4 - Análisis automático de textos para revisión lingüística (2027).docx',
    't5': 'manuales 2027/Tema 5 - Evaluación automática de traducciones (2027).docx',
    't6': 'manuales 2027/Tema 6 - Análisis automático de sesgo léxico y discursivo (2027).docx',
    't7': 'manuales 2027/Tema 7 - Extracción automática de terminología (2027).docx',
    't8': 'manuales 2027/Tema 8 - Clasificación temática de textos (2027).docx',
}

NAV_FIXED = {
    'Contexto profesional': 'Contexto profesional',
    'Qué vas a aprender en esta unidad': 'Qué vas a aprender',
    'Mapa conceptual de la unidad': 'Mapa conceptual',
    '1. Marco teórico': 'Marco teórico',
    'Errores frecuentes de aprendizaje': 'Errores frecuentes',
    'Síntesis final': 'Síntesis',
    'Cierre narrativo': 'Cierre narrativo',
    'Título narrativo': 'Título narrativo',
    'Reglas simples frente a análisis lingüístico avanzado': 'Reglas y análisis avanzado',
    'Buenas prácticas para revisar textos con Python': 'Buenas prácticas',
    'Para saber más: Preparación previa a la práctica': 'Para saber más',
}

EMPH = {t: 'all' for t in ('t4', 't5', 't6', 't7', 't8')}
# figuras de los manuales 2027 que la web sustituye por su versión SVG (FIGURAS)
GENERATED = {
    't3': ('Pipeline de preprocesamiento lingüístico de la unidad',),
    't4': ('Cadena de análisis para la revisión de versiones paralelas monolingües',),
    't5': ('Métricas de evaluación según el tipo de similitud que observan',),
    't6': ('Pipeline de análisis de sesgo léxico y discursivo',),
    't7': ('Pipeline de extracción automática de terminología', 'Componentes de la fórmula de weirdness'),
    't8': ('Clasificación por prototipos temáticos',),
}

NS_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
NS_R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def slug(s):
    s = strip_accents(s.lower())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60]


CODE_FONTS = {'Courier New', 'Consolas'}


def _run_kind(r, emph):
    rp = r._r.rPr
    font = rp.rFonts.get(qn('w:ascii')) if (rp is not None and rp.rFonts is not None) else None
    if (font in CODE_FONTS or r.font.name in CODE_FONTS) and r.text.strip():
        return 'code'
    if emph == 'all':
        if r.bold and r.italic: return 'bi'
        if r.bold: return 'b'
        if r.italic: return 'it'
    elif emph == 'italic' and r.italic:
        return 'it'
    return 'n'


MARKS = {'code': '`', 'it': '*', 'b': '**', 'bi': '***'}


def runs_to_markup(paragraph, italics=False, emph=None):
    """Courier New/Consolas -> `código`; cursiva -> *texto*; negrita -> **texto** (con emph='all').
    Los runs contiguos del mismo tipo se fusionan antes de marcar."""
    if emph is None:
        emph = 'italic' if italics else 'none'
    segs = []
    runs = []
    for item in paragraph.iter_inner_content():     # incluye el texto de los hipervínculos
        runs.extend(item.runs if hasattr(item, 'runs') else [item])
    for r in runs:
        t = r.text
        if not t:
            continue
        kind = _run_kind(r, emph)
        if not t.strip() and kind != 'code' and segs:
            kind = segs[-1][0]
        if segs and segs[-1][0] == kind:
            segs[-1][1] += t
        else:
            segs.append([kind, t])
    out = []
    for kind, t in segs:
        if kind == 'n' or not t.strip():
            out.append(t); continue
        lead = t[:len(t) - len(t.lstrip())]; trail = t[len(t.rstrip()):]
        mark = MARKS[kind]
        out.append(lead + mark + t.strip() + mark + trail)
    return ''.join(out)


def run(tema):
    src = BASE + TEMAS[tema]
    out_dir = os.path.join(SITE, tema)
    img_dir = os.path.join(out_dir, 'img')
    d = docx.Document(src)
    rels = d.part.rels

    def blocks_of(parent):
        for ch in parent.element.body.iterchildren():
            if ch.tag == qn('w:p'):
                yield Paragraph(ch, parent)
            elif ch.tag == qn('w:tbl'):
                yield Table(ch, parent)

    # ---- flujo ordenado
    stream, seen_heading, img_n = [], False, 0
    saved_imgs = []
    for it in blocks_of(d):
        if isinstance(it, Paragraph):
            style = it.style.name
            if style.startswith('toc'):
                continue
            if style.startswith('Heading'):
                seen_heading = True
            blips = it._p.findall('.//' + NS_A + 'blip')
            if style == 'Caption':
                full = ''.join(x.text or '' for x in it._p.iter(qn('w:t'))).strip()
                lab = 'fig' if full.startswith('Figura') else 'tab'
                stream.append(('cap', lab, full.split('. ', 1)[1] if '. ' in full else full))
                continue
            if style == 'Nota figura':
                stream.append(('note', None, re.sub(r'^Nota\.\s*', '', it.text.strip())))
                continue
            if style.startswith('Heading'):
                txt = it.text
            else:
                txt = runs_to_markup(it, italics=(style == 'Comillas References'),
                                     emph=('italic' if style == 'Comillas References' else EMPH.get(tema, 'none')))
            stream.append(('p', style, txt))
            if blips and seen_heading:
                exts = it._p.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent')
                for bi, b in enumerate(blips):
                    width_px = round(int(exts[bi].get('cx')) / 9525) if bi < len(exts) else None
                    rid = b.get(NS_R + 'embed')
                    blob = rels[rid].target_part.blob
                    img_n += 1
                    os.makedirs(img_dir, exist_ok=True)
                    name, data = save_image(blob, img_n)
                    with open(os.path.join(img_dir, name), 'wb') as f:
                        f.write(data)
                    saved_imgs.append(name)
                    stream.append(('img', width_px, 'img/' + name))
        else:
            cell = it.rows[0].cells[0]
            tcPr = cell._tc.find(qn('w:tcPr'))
            shd = tcPr.find(qn('w:shd')) if tcPr is not None else None
            fill = shd.get(qn('w:fill')) if shd is not None else None
            if fill == 'F2F4F5' and len(it.rows) == 1 and len(it.columns) == 1:
                stream.append(('code', None, cell.text))
            else:
                rows = [['\n'.join(runs_to_markup(p, emph=EMPH.get(tema, 'none')) for p in c.paragraphs) for c in r.cells] for r in it.rows]
                stream.append(('table', None, rows))

    # ---- cabecera (hasta el título del índice)
    i, normals = 0, []
    while i < len(stream) and not (stream[i][0] == 'p' and stream[i][1] == 'Comillas TOC Title'):
        if stream[i][0] == 'p' and stream[i][2].strip():
            normals.append(stream[i][2].strip())
        i += 1
    normals = [n.replace('*', '').strip() for n in normals]
    header = {'kicker': normals[0] if normals else '', 'title': normals[1] if len(normals) > 1 else '',
              'subtitle': normals[2] if len(normals) > 2 else '', 'meta': normals[3] if len(normals) > 3 else ''}
    i += 1
    if i < len(stream) and stream[i][0] == 'p' and stream[i][2].count('\t') > 3:
        i += 1

    # ---- capítulos / apartados / bloques
    sections, references = [], []
    cur_sec = cur_target = None
    lst, lst_type = [], None
    in_refs = False
    last_para = ''

    def flush():
        nonlocal lst, lst_type
        if lst and cur_target is not None:
            cur_target.append({'type': lst_type, 'items': lst})
        lst, lst_type = [], None

    pending = {'tab': None, 'fig': None}
    skip_note = False
    for kind, style, content in stream[i:]:
        if kind == 'cap':
            pending[style] = content
            continue
        if kind == 'note':
            if skip_note:
                skip_note = False
            elif cur_target and cur_target[-1].get('type') == 'image':
                cur_target[-1]['caption'] = content
            continue
        if kind == 'p' and style == 'Heading 1':
            flush()
            title = content.strip()
            in_refs = (title == 'Referencias')
            if in_refs:
                cur_sec = cur_target = None
                continue
            cur_sec = {'id': slug(title), 'title': title, 'blocks': [], 'subsections': []}
            sections.append(cur_sec); cur_target = cur_sec['blocks']
            continue
        if in_refs:
            if kind == 'p' and style == 'Comillas References' and content.strip():
                references.append(content.strip())
            continue
        if cur_target is None:
            continue
        if kind == 'p' and style == 'Heading 2':
            flush()
            sub = {'id': slug(content.strip()), 'title': content.strip(), 'blocks': []}
            cur_sec['subsections'].append(sub); cur_target = sub['blocks']
            continue
        if kind == 'p' and style == 'Heading 3':
            flush(); cur_target.append({'type': 'h4', 'text': content.strip()})
            continue
        if kind == 'p' and style in ('List Bullet', 'List Number'):
            want = 'ul' if style == 'List Bullet' else 'ol'
            if lst_type and lst_type != want:
                flush()
            lst_type = want
            if content.strip():
                lst.append(content.strip())
            continue
        if kind == 'p' and style == 'Comillas References' and content.strip():
            if lst_type and lst_type != 'biblist':
                flush()
            lst_type = 'biblist'; lst.append(content.strip())
            continue
        flush()
        if kind == 'p':
            if content.strip():
                cur_target.append({'type': 'p', 'text': content.strip()})
                last_para = content.strip()
        elif kind == 'code':
            cur_target.append({'type': 'code', 'code': content})
        elif kind == 'table':
            title = pending['tab'] or table_title(content, last_para)
            pending['tab'] = None
            cur_target.append({'type': 'table', 'rows': content, 'title': title})
        elif kind == 'img' and pending['fig']:
            title = pending['fig']; pending['fig'] = None
            if title in GENERATED.get(tema, ()):      # la web ya muestra esta figura en SVG (FIGURAS)
                skip_note = True
                continue
            cur_target.append({'type': 'image', 'src': content, 'alt': title, 'caption': title})
        elif kind == 'img':
            blk = {'type': 'docimg', 'src': content, 'alt': 'Figura del manual'}
            if style:
                blk['w'] = style          # ancho de visualización en el docx (px)
            cur_target.append(blk)
    flush()

    # Errores frecuentes: pares término/explicación
    for sec in sections:
        if sec['title'] == 'Errores frecuentes de aprendizaje' and not sec['subsections']:
            paras = [re.sub(r'^\*\*(.+?):\*\*\s*', r'\1: ', b['text']) for b in sec['blocks'] if b.get('type') == 'p']
            if paras and len(sec['blocks']) == len(paras) and all(re.match(r'^[^:]{6,90}: ', x) for x in paras):
                sec['blocks'] = [{'type': 'errorlist', 'items': [{'term': x.split(': ', 1)[0], 'desc': x.split(': ', 1)[1]} for x in paras]}]
            elif len(paras) >= 2 and len(paras) % 2 == 0 and len(sec['blocks']) == len(paras):
                sec['blocks'] = [{'type': 'errorlist', 'items': [{'term': paras[k], 'desc': paras[k + 1]} for k in range(0, len(paras), 2)]}]

    # Título narrativo de una sola frase -> lema de la portada (no un capítulo de una línea)
    keep = []
    for s in sections:
        if s['title'] == 'Título narrativo' and not s['subsections'] and len(s['blocks']) == 1 and s['blocks'][0].get('type') == 'p':
            if s['blocks'][0]['text'].strip() != header['subtitle'].strip():
                header['narrative'] = s['blocks'][0]['text'].strip()
            continue
        keep.append(s)
    sections = keep

    for sec in sections:
        t = sec['title']
        sec['navTitle'] = NAV_FIXED.get(t) or ('Python para PLN' if re.match(r'^2\.\s', t) else re.sub(r'^\d+\.\s*', '', t))

    place_figures(tema, sections)
    refs_out = build_refs(references)
    unmatched = link_citations(sections, refs_out)

    data = {'header': header, 'sections': sections, 'references': refs_out}
    with open(os.path.join(out_dir, 'manual_interactivo.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    used = json.dumps(data, ensure_ascii=False)
    for name in list(saved_imgs):
        if 'img/' + name not in used:
            os.remove(os.path.join(img_dir, name)); saved_imgs.remove(name)

    print(f'== {tema}: {header["kicker"]} {header["title"]}')
    for s in sections:
        print(f'   - {s["navTitle"]:28} | apartados {len(s["subsections"]):2} | bloques {len(s["blocks"])}')
    print(f'   referencias: {len(refs_out)} | imágenes: {len(saved_imgs)} | citas sin pareja: {sorted(unmatched)}')


# Figuras creadas para el manual (im_figuras.py); cada una sale del contenido del propio manual.
MAPA = 'Figura elaborada a partir del mapa conceptual de la unidad.'
FIGURAS = {
    't3': [(('1. Marco teórico', '1.2. Qué es un pipeline lingüístico'), {'type': 'image', 'position': 'end', 'src': 'img/fig_pipeline.svg',
            'alt': 'El pipeline de preprocesamiento de la unidad, de la normalización al glosario técnico', 'caption': MAPA})],
    't4': [(('1. Marco teórico', '1.3. Del corpus al informe: una cadena de análisis'), {'type': 'image_reveal', 'position': 'end', 'src': 'img/fig_cadena.svg',
            'alt': 'Del corpus al informe: resultado de cada paso', 'labelClosed': '🔎 Descubre la cadena de análisis paso a paso', 'caption': MAPA})],
    't5': [(('1. Marco teórico', '1.3. Qué tipos de similitud puede observar una métrica'), {'type': 'image', 'position': 'end', 'src': 'img/fig_metricas.svg',
            'alt': 'Qué observa cada métrica: similitud superficial, estructural y semántica',
            'caption': 'Figura elaborada a partir de los apartados 1.3 y 1.11 y del mapa conceptual de la unidad.'})],
    't6': [('Mapa conceptual de la unidad', {'type': 'image_modal', 'position': 'end', 'src': 'img/fig_pipeline.svg',
            'alt': 'Del corpus a la interpretación crítica: resultado de cada paso', 'label': 'Ver el recorrido completo en una figura',
            'sub': 'Diez pasos, del corpus a la interpretación crítica', 'caption': MAPA})],
    't7': [('Mapa conceptual de la unidad', {'type': 'image', 'position': 'end', 'src': 'img/fig_pipeline.svg',
            'alt': 'De los corpus a los candidatos terminológicos', 'caption': MAPA}),
           (('1. Marco teórico', '1.7. Weirdness: rareza relativa y especificidad de dominio'), {'type': 'image_modal', 'position': 'end',
            'src': 'img/fig_weirdness.svg', 'alt': 'Weirdness: fórmula didáctica de la unidad', 'label': 'Ver la fórmula desglosada',
            'sub': 'Qué mide cada parte de weirdness', 'caption': 'Figura elaborada a partir del apartado 1.7 de la unidad.'})],
    't8': [(('1. Marco teórico', '1.7. Prototipos temáticos y clasificación por cercanía'), {'type': 'image', 'position': 'end',
            'src': 'img/fig_prototipos.svg', 'alt': 'Clasificación por prototipos temáticos',
            'caption': 'Figura elaborada a partir del apartado 1.7 y del mapa conceptual de la unidad.'})],
}


def place_figures(tema, sections):
    for where, fig in FIGURAS.get(tema, []):
        fig = dict(fig); pos = fig.pop('position', 'end')
        if isinstance(where, tuple):
            target = [sub for s in sections if s['title'] == where[0] for sub in s['subsections'] if sub['title'] == where[1]]
        else:
            target = [s for s in sections if s['title'] == where]
        assert len(target) == 1, (tema, where)
        blocks = target[0]['blocks']
        blocks.append(fig) if pos == 'end' else blocks.insert(0, fig)


def save_image(blob, n):
    from PIL import Image
    im = Image.open(io.BytesIO(blob))
    if len(blob) > 300_000:
        im = im.convert('RGB')
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)))
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=86, optimize=True)
        return f'doc_{n:02d}.jpg', buf.getvalue()
    return f'doc_{n:02d}.png', blob


def table_title(rows, last_para):
    p = re.sub(r'`', '', last_para).strip()
    if p.endswith(':') and 8 <= len(p) <= 70:
        return p[:-1].strip()
    head = [re.sub(r'`', '', c).strip() for c in rows[0] if c.strip()]
    return ' · '.join(head)[:80] or 'Tabla'


# ---------------- bibliografía y citas
ALIASES = {'iso': 'internationalorganizationforstandardization'}


def _surname_key(s):
    s = strip_accents(s).lower().replace('\xa0', ' ')
    if s.strip().startswith('real academia'):
        return 'realacademiaespanola'
    s = re.sub(r'\bet al\.?', '', s)
    s = re.split(r',| y | and | & ', s)[0]
    s = re.sub(r'[^a-z]', '', s)
    return ALIASES.get(s, s)


def build_refs(references):
    out, seen = [], {}
    for t in references:
        m = re.search(r'\((\d{4}[a-z]?|s\.\s?f\.)', t)
        year = m.group(1).replace(' ', '') if m else 'sf'
        author = t[:m.start()] if m else t
        sk = _surname_key(author.split(',')[0] if ',' in author.split('.')[0] else author)
        key = (sk[:20] or 'ref') + year
        if key in seen:
            seen[key] += 1; key += f'_{seen[key]}'
        else:
            seen[key] = 1
        out.append({'key': key, 'text': t, '_sk': sk, '_year': year})
    return out


def _match(refs, name, year):
    sk = _surname_key(name)
    if not sk:
        return None
    cands = [r for r in refs if r['_year'] == year and (r['_sk'].startswith(sk) or sk.startswith(r['_sk']))]
    return cands[0]['key'] if len(cands) == 1 else (cands[0]['key'] if cands else None)


def link_citations(sections, refs):
    unmatched = set()
    paren = re.compile(r'\(([^()]*?\d{4}[a-z]?)\)')
    narr = re.compile(r"((?:de |van |von )?[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñüćčš'’\-]+(?:\s(?:et\s?al\.|y\s[A-ZÁÉÍÓÚ][\w\-]+))?)\s\((\d{4}[a-z]?)\)")

    def wrap(text):
        def rep_paren(m):
            inner = re.sub(r'(\d{4})/\d{4}', r'\1', m.group(1))
            keys, ok = [], True
            for part in inner.split(';'):
                part = part.strip().replace('\xa0', ' ')
                yrs = re.findall(r'\d{4}[a-z]?', part)
                name = re.split(r',\s*\d{4}', part)[0]
                if not yrs or not re.search(r'[A-Za-zÁÉÍÓÚ]', name):
                    ok = False; break
                for y in yrs:
                    k = _match(refs, name, y)
                    if k:
                        keys.append(k)
                    else:
                        ok = False
            if ok and keys:
                return '{{cite:' + ','.join(dict.fromkeys(keys)) + '}}' + m.group(0) + '{{/cite}}'
            if re.search(r'[A-Za-z]', inner):
                unmatched.add(m.group(0))
            return m.group(0)

        def rep_narr(m):
            k = _match(refs, m.group(1), m.group(2))
            if k:
                return '{{cite:' + k + '}}' + m.group(0) + '{{/cite}}'
            return m.group(0)

        # proteger citas ya envueltas y código
        out = paren.sub(rep_paren, text)
        pieces = re.split(r'(\{\{cite:.*?\{\{/cite\}\}|`[^`]*`)', out)
        return ''.join(p if (p.startswith('{{cite:') or p.startswith('`')) else narr.sub(rep_narr, p) for p in pieces)

    def walk(blocks):
        for b in blocks:
            if b.get('type') == 'p':
                b['text'] = wrap(b['text'])
            elif b.get('type') in ('ul', 'ol'):
                b['items'] = [wrap(x) for x in b['items']]
            elif b.get('type') == 'errorlist':
                for it in b['items']:
                    it['desc'] = wrap(it['desc'])
            elif b.get('type') == 'table':
                b['rows'] = [[wrap(c) for c in r] for r in b['rows']]

    for s in sections:
        walk(s['blocks'])
        for sub in s['subsections']:
            walk(sub['blocks'])
    for r in refs:
        r.pop('_sk'); r.pop('_year')
    return unmatched


if __name__ == '__main__':
    for t in (sys.argv[1:] or TEMAS):
        run(t)
