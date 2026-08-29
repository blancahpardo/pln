# -*- coding: utf-8 -*-
import docx, json, re
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = '/Users/blanca/Library/CloudStorage/OneDrive-UniversidadPontificiaComillas/2. Trabajo/4. UPComillas/1. Docencia UPCO/21. Programación para PLN/2. PLN 2/0. Teoría PLN2/Teoría_PLN2.docx'
OUT = '/tmp/pln-interactive/t2/manual_interactivo.json'

d = docx.Document(SRC)

def iter_block_items(parent):
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

# The word "y" is in Courier New on literally every occurrence throughout
# the whole document (confirmed by scanning all paragraphs and table cells) -
# a document-wide formatting artifact, not intentional code styling. Treating
# a Courier New run as real code requires it not be just this stray "y".
_FALSE_POSITIVE_CODE_RUNS = {'y'}

def runs_to_markup(paragraph):
    """Rebuild paragraph text from its runs, wrapping any run set in Courier
    New (the docx's own inline-code styling, e.g. `len()` mentioned in prose)
    in backticks so the client renders it as monospace code."""
    parts, buf, buf_code = [], '', None
    for r in paragraph.runs:
        is_code = (r.font.name == 'Courier New' and r.text.strip().lower() not in _FALSE_POSITIVE_CODE_RUNS)
        if buf_code is None:
            buf_code = is_code
        if is_code != buf_code:
            parts.append((buf_code, buf))
            buf, buf_code = '', is_code
        buf += r.text
    if buf:
        parts.append((buf_code, buf))
    return ''.join(('`' + t + '`') if code else t for code, t in parts)

def cell_markup(cell):
    return '\n'.join(runs_to_markup(p) for p in cell.paragraphs)

def slug(s):
    s = s.lower()
    s = re.sub(r'[áàä]', 'a', s); s = re.sub(r'[éèë]', 'e', s)
    s = re.sub(r'[íìï]', 'i', s); s = re.sub(r'[óòö]', 'o', s)
    s = re.sub(r'[úùü]', 'u', s); s = s.replace('ñ', 'n')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60]

items = list(iter_block_items(d))

# raw ordered stream skipping toc paragraphs
stream = []
for it in items:
    if isinstance(it, Paragraph):
        style = it.style.name
        if style.startswith('toc'):
            continue
        stream.append(('p', style, runs_to_markup(it)))
    else:
        cell = it.rows[0].cells[0]
        tcPr = cell._tc.find(qn('w:tcPr'))
        shd = tcPr.find(qn('w:shd')) if tcPr is not None else None
        fill = shd.get(qn('w:fill')) if shd is not None else None
        if fill == 'F2F4F5':
            stream.append(('code', None, cell.text))
        else:
            rows = [[cell_markup(c) for c in r.cells] for r in it.rows]
            stream.append(('table', None, rows))

# document header block: first few normal paragraphs before "Comillas TOC Title"
header = {}
i = 0
normals = []
while i < len(stream) and not (stream[i][0]=='p' and stream[i][1]=='Comillas TOC Title'):
    if stream[i][0]=='p' and stream[i][2].strip():
        normals.append(stream[i][2].strip())
    i += 1
# normals should be: ['Tema 1.', 'Fundamentos de Python para PLN', 'Primer prototipo...', 'Material teórico | ...']
header['kicker'] = normals[0] if len(normals) > 0 else ''
header['title'] = normals[1] if len(normals) > 1 else ''
header['subtitle'] = normals[2] if len(normals) > 2 else ''
header['meta'] = normals[3] if len(normals) > 3 else ''
# skip TOC title paragraph itself
i += 1

rest = stream[i:]

def make_block(kind, style, content):
    if kind == 'code':
        return {'type': 'code', 'code': content}
    if kind == 'table':
        return {'type': 'table', 'rows': content}
    # paragraph
    text = content.strip()
    return {'style': style, 'text': text}

# Group rest into H1 sections -> H2 subsections -> blocks, collapsing consecutive
# List Bullet / List Number paragraphs into ul/ol blocks.
sections = []
references = []
cur_section = None
cur_sub = None
cur_target_blocks = None  # points to blocks list currently receiving content
list_buffer = []
list_type = None

def flush_list():
    global list_buffer, list_type, cur_target_blocks
    if list_buffer and cur_target_blocks is not None:
        cur_target_blocks.append({'type': list_type, 'items': list_buffer})
    list_buffer = []
    list_type = None

IN_REFERENCES = [False]

for kind, style, content in rest:
    if kind == 'p' and style == 'Heading 1':
        flush_list()
        title = content.strip()
        IN_REFERENCES[0] = (title == 'Referencias')
        if IN_REFERENCES[0]:
            cur_section = None
            cur_sub = None
            cur_target_blocks = None
            continue
        cur_section = {'id': slug(title), 'title': title, 'blocks': [], 'subsections': []}
        sections.append(cur_section)
        cur_sub = None
        cur_target_blocks = cur_section['blocks']
        continue
    if IN_REFERENCES[0]:
        if kind == 'p' and style == 'Comillas References' and content.strip():
            references.append(content.strip())
        continue
    if kind == 'p' and style == 'Heading 2':
        flush_list()
        title = content.strip()
        cur_sub = {'id': slug(title), 'title': title, 'blocks': []}
        cur_section['subsections'].append(cur_sub)
        cur_target_blocks = cur_sub['blocks']
        continue
    if kind == 'p' and style in ('List Bullet', 'List Number'):
        want = 'ul' if style == 'List Bullet' else 'ol'
        if list_type and list_type != want:
            flush_list()
        list_type = want
        if content.strip():
            list_buffer.append(content.strip())
        continue
    else:
        flush_list()
    if kind == 'p' and style == 'Normal':
        if content.strip():
            cur_target_blocks.append({'type': 'p', 'text': content.strip()})
        continue
    if kind == 'code':
        cur_target_blocks.append({'type': 'code', 'code': content})
        continue
    if kind == 'table':
        cur_target_blocks.append({'type': 'table', 'rows': content})
        continue
flush_list()

# Special-case: "Errores frecuentes de aprendizaje" section -> pair up plain paragraphs into term/desc
for sec in sections:
    if sec['title'] == 'Errores frecuentes de aprendizaje':
        paras = [b['text'] for b in sec['blocks'] if b.get('type') == 'p']
        items = []
        for j in range(0, len(paras) - 1, 2):
            items.append({'term': paras[j], 'desc': paras[j+1]})
        sec['blocks'] = [{'type': 'errorlist', 'items': items}]

# The "Título narrativo" H1 is a single paragraph duplicating header['subtitle']
# verbatim (the narrative title) -> drop it as a chapter, it becomes the hero
# title on the manual's landing screen instead (see build.js imShowIndex).
sections = [s for s in sections if s['title'] != 'Título narrativo']

# Short nav labels for the index cards (in-page chapter heading text is left
# untouched, e.g. "1. Marco teórico" stays as-is once you're inside it).
NAV_TITLES = {
    'Contexto profesional': 'Contexto profesional',
    'Qué vas a aprender en esta unidad': 'Qué vas a aprender',
    'Mapa conceptual de la unidad': 'Mapa conceptual',
    '1. Marco teórico': 'Marco teórico',
    '2. Detección de patrones léxicos y falsos amigos con Python': 'Python y falsos amigos',
    'Errores frecuentes de aprendizaje': 'Errores frecuentes',
    'Síntesis final': 'Síntesis',
    'Cierre narrativo': 'Cierre narrativo',
}
for sec in sections:
    sec['navTitle'] = NAV_TITLES.get(sec['title'], sec['title'])

# Short custom titles for "Ver tabla" buttons/modals, curated from each
# table's real content (not invented) -> keyed by (section title, row-1 header
# tuple) since a couple of tables share the generic "Medida / Resultado" header.
TABLE_TITLES = {
    ('Mapa conceptual de la unidad', ('Concepto', 'En Python', 'En PLN y traducción')): 'Datos completos del mapa conceptual',
    ('1.2. Fundamentos de las expresiones regulares', ('Elemento', 'Función', 'Ejemplo en la unidad')): 'Elementos de una expresión regular',
    ('1.4. Falsos amigos: problema lingüístico y problema computacional', ('Nivel de detección', 'Qué busca', 'Interpretación')): 'Niveles de detección de falsos amigos',
    ('2.4. Límites de palabra: evitar capturas falsas', ('Forma', 'Debe coincidir con \\bactual\\b', 'Motivo')): 'Ejemplos del patrón \\bactual\\b',
    ('2.5. Buscar todas las coincidencias con re.findall()', ('Término buscado', 'Ocurrencias')): 'Ocurrencias encontradas',
    ('2.8. Comprobar presencia con re.search()', ('Función', 'Qué devuelve', 'Para qué se usa')): 'Funciones del módulo re',
    ('2.9. Glosarios como diccionarios', ('Tipo de glosario', 'Qué almacena', 'Ejemplo')): 'Tipos de glosario',
    ('2.11. Patrones dinámicos con f-strings raw', ('Prefijo', 'Función')): 'Prefijos de cadena en Python',
    ('2.13. Segundo tipo de informe: error probable en TO y TM', ('Inglés', 'Español detectado', 'Motivo')): 'Ejemplo de falso amigo detectado',
    ('2.16. Falsos positivos y falsos negativos', ('Tipo', 'Qué ocurre', 'Ejemplo')): 'Tipos de error en la detección',
}
for sec in sections:
    containers = [sec] + sec['subsections']
    for cont in containers:
        for b in cont['blocks']:
            if b.get('type') == 'table':
                head = tuple(b['rows'][0])
                b['title'] = TABLE_TITLES.get((cont['title'], head), 'Tabla')

# References -> structured with keys, matching known author/year patterns
REF_KEYS = [
    ('bird2009', "Bird, S., Klein, E. y Loper, E. (2009)"),
    ('chamizo2008', 'Chamizo Domínguez, P. J. (2008)'),
    ('friedl2006', 'Friedl, J. E. F. (2006)'),
    ('goyvaerts2009', 'Goyvaerts, J. y Levithan, S. (2009)'),
    ('jurafsky2026', 'Jurafsky, D. y Martin, J. H. (2026)'),
    ('kleene1956', 'Kleene, S. C. (1956)'),
    ('psf2026', 'Python Software Foundation. (2026)'),
]
refs_out = []
for ref_text in references:
    key = None
    for k, needle in REF_KEYS:
        if ref_text.startswith(needle):
            key = k
            break
    refs_out.append({'key': key or slug(ref_text[:30]), 'text': ref_text})

# APA 7 italicizes the container title (book, journal name + volume, standalone
# report/webpage title, dissertation title...). The source .docx carries no
# run-level italics at all (checked directly in its XML), so this is restored
# here rather than lost in the docx -> apply the APA convention, wrapping the
# exact substring in *asterisks* (rendered as <em> in build.js's imBibText).
ITALIC_SPANS = {
    'bird2009': 'Natural language processing with Python',
    'chamizo2008': 'Semantics and pragmatics of false friends',
    'friedl2006': 'Mastering regular expressions',
    'goyvaerts2009': 'Regular expressions cookbook',
    'jurafsky2026': 'Speech and language processing',
    'kleene1956': 'Automata studies',
    'psf2026': 'Python 3.14 documentation',
}
for r in refs_out:
    span = ITALIC_SPANS.get(r['key'])
    if span and span in r['text']:
        r['text'] = r['text'].replace(span, '*' + span + '*', 1)

# Inline citation wrapping: exact-substring replace across all 'p' block texts and errorlist descs
CITATIONS = [
    ('(Kleene, 1956)', ['kleene1956']),
    ('(Chamizo Domínguez, 2008)', ['chamizo2008']),
    ('(Python Software Foundation, 2026)', ['psf2026']),
]

def wrap_citations(text):
    for needle, keys in CITATIONS:
        if needle in text:
            marker = '{{cite:' + ','.join(keys) + '}}' + needle + '{{/cite}}'
            text = text.replace(needle, marker)
    return text

def walk_and_wrap(blocks):
    for b in blocks:
        if b.get('type') == 'p':
            b['text'] = wrap_citations(b['text'])
        elif b.get('type') == 'errorlist':
            for it in b['items']:
                it['desc'] = wrap_citations(it['desc'])
        elif b.get('type') in ('ul', 'ol'):
            b['items'] = [wrap_citations(x) for x in b['items']]

for sec in sections:
    walk_and_wrap(sec['blocks'])
    for sub in sec['subsections']:
        walk_and_wrap(sub['blocks'])

# Infographics generated with NotebookLM from this same source (scoped to
# Teoría_PLN2.docx only, verified against the document's real figures before
# accepting) -> inserted as 'image' blocks at the front of the section/
# subsection they illustrate, image files live in t2/img/. Add new ones here
# as they're generated; keep the underlying table/content block too so no
# information from the manual is lost, only made more visual.
IMAGE_CAPTION = 'Infografía generada con NotebookLM a partir del manual teórico elaborado por la Dr.ª Blanca Hernández Pardo.'

# key: section title, or (section title, subsection title) for a subsection.
# 'type' picks the presentation: 'image' = embedded full-width with caption,
# 'image_modal' = a small button with a thumbnail that opens the image in a
# popup (label/sub customize the button text), 'image_reveal' = a
# code-toggle-style button that expands the image inline (labelClosed
# customizes the button text). Alternate these across placements.
# 'position': 'start' (default) inserts before the section's other content;
# 'end' appends after it -> use 'end' when a table/button should read first
# and the image serves as a visual summary afterwards.
# Empty until Tema 2's infographics are generated in NotebookLM (scoped to
# Teoría_PLN2.docx only) and the user hands over the downloaded files -> then
# compress, drop into t2/img/, and add entries here the same way Tema 1's
# five were added (see SKILL.md's Interactive manual section).
IMAGE_BLOCKS = {}

def _place_image(blocks, img):
    t = img.pop('type', 'image')
    pos = img.pop('position', 'start')
    block = {'type': t, 'caption': IMAGE_CAPTION, **img}
    if pos == 'end':
        blocks.append(block)
    else:
        blocks.insert(0, block)

for sec in sections:
    for img in IMAGE_BLOCKS.get(sec['title'], []):
        _place_image(sec['blocks'], img)
    for sub in sec['subsections']:
        for img in IMAGE_BLOCKS.get((sec['title'], sub['title']), []):
            _place_image(sub['blocks'], img)

data = {'header': header, 'sections': sections, 'references': refs_out}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('sections:', len(sections))
for s in sections:
    print(' -', s['title'], '| subsecciones:', len(s['subsections']), '| blocks:', len(s['blocks']))
print('references:', len(refs_out))
missing_keys = [r['text'][:40] for r in refs_out if r['key'] is None]
print('missing keys:', missing_keys)
