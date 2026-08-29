# -*- coding: utf-8 -*-
import docx, json, re
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = '/Users/blanca/Library/CloudStorage/OneDrive-UniversidadPontificiaComillas/2. Trabajo/4. UPComillas/1. Docencia UPCO/21. Programación para PLN/0.1 Recordatorio/0. Teoría/Teoría - Recordatorio Python.docx'
OUT = '/tmp/pln-interactive/t0a/manual_interactivo.json'

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

# Document header block: the first few non-empty 'Normal' paragraphs before
# the first heading. Some docx templates (like Teoría_PLN1/2) insert a
# "Comillas TOC Title" + TOC page between the header and the first real
# heading; this one (Teoría - Recordatorio Python) has no TOC page at all and
# goes straight into "Título narrativo" as a heading -> stopping at the first
# Heading 1 *or* Heading 2 (instead of a hardcoded TOC-title style name)
# handles both cases.
header = {}
i = 0
normals = []
while i < len(stream) and not (stream[i][0]=='p' and stream[i][1] in ('Heading 1', 'Heading 2', 'Comillas TOC Title')):
    if stream[i][0]=='p' and stream[i][2].strip():
        normals.append(stream[i][2].strip())
    i += 1
# normals should be: ['Tema 0.', 'Repaso de Python para lingüistas', 'Primer encargo...', 'Material teórico | ...']
header['kicker'] = normals[0] if len(normals) > 0 else ''
header['title'] = normals[1] if len(normals) > 1 else ''
header['subtitle'] = normals[2] if len(normals) > 2 else ''
header['meta'] = normals[3] if len(normals) > 3 else ''
# Only skip a paragraph here if we actually stopped on a TOC title (docs with
# a real TOC page); if we stopped on a heading instead, that heading is the
# first real content and must be processed, not skipped.
if i < len(stream) and stream[i][1] == 'Comillas TOC Title':
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
seen_h1 = False

for kind, style, content in rest:
    if kind == 'p' and style == 'Heading 1':
        flush_list()
        seen_h1 = True
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
        if not seen_h1:
            # This doc's template tags the two intro sections ("Título
            # narrativo", "Contexto profesional") as Heading 2, not Heading 1,
            # even though they act as top-level sections (they both come
            # before the first Heading 1) -> treat every Heading 2 reached
            # before the first Heading 1 as a top-level section too (not just
            # the first one -> a plain "cur_section is None" check would
            # wrongly nest the second intro H2 under the first).
            cur_section = {'id': slug(title), 'title': title, 'blocks': [], 'subsections': []}
            sections.append(cur_section)
            cur_sub = None
            cur_target_blocks = cur_section['blocks']
            continue
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

# This doc has no "Errores frecuentes de aprendizaje" section in the paired-
# paragraph format T1/T2 use (its closest equivalent, "17. Errores habituales
# y como interpretarlos", already has real Heading 2 subsections instead) ->
# the special-case pairing below simply won't match anything, left in as a
# no-op for template consistency rather than deleted.
for sec in sections:
    if sec['title'] == 'Errores frecuentes de aprendizaje':
        paras = [b['text'] for b in sec['blocks'] if b.get('type') == 'p']
        items = []
        for j in range(0, len(paras) - 1, 2):
            items.append({'term': paras[j], 'desc': paras[j+1]})
        sec['blocks'] = [{'type': 'errorlist', 'items': items}]

# The "Título narrativo" section is a single paragraph duplicating
# header['subtitle'] verbatim (the narrative title) -> drop it as a chapter,
# it becomes the hero title on the manual's landing screen instead (see
# build.js imShowIndex).
sections = [s for s in sections if s['title'] != 'Título narrativo']

# Short nav labels for the index cards (in-page chapter heading text is left
# untouched, e.g. "4. Operadores básicos" stays as-is once you're inside it).
NAV_TITLES = {
    'Contexto profesional': 'Contexto profesional',
    '1. Qué es Python y por qué le interesa a una lingüista': 'Qué es Python',
    '2. Scripts y notebooks': 'Scripts y notebooks',
    '3. Expresiones, comentarios y salida por pantalla': 'Expresiones y comentarios',
    '4. Operadores básicos': 'Operadores básicos',
    '5. Strings: representar texto en Python': 'Strings',
    '6. Variables y objetos': 'Variables y objetos',
    '7. Atributos y métodos': 'Atributos y métodos',
    '8. Colecciones: agrupar datos lingüísticos': 'Colecciones',
    '9. Funciones comunes para colecciones': 'Funciones para colecciones',
    '10. Índices y slicing': 'Índices y slicing',
    '11. Eliminar elementos': 'Eliminar elementos',
    '12. Control de flujo: tomar decisiones': 'Control de flujo',
    '13. Bucles: repetir una tarea': 'Bucles',
    '14. Funciones: crear herramientas reutilizables': 'Funciones',
    '15. Limpieza básica de texto': 'Limpieza de texto',
    '16. Importar librerías: NLTK y tokenización': 'NLTK y tokenización',
    '17. Errores habituales y como interpretarlos': 'Errores habituales',
    '18. Cierre narrativo': 'Cierre narrativo',
}
for sec in sections:
    sec['navTitle'] = NAV_TITLES.get(sec['title'], sec['title'])

# Short custom titles for "Ver tabla" buttons/modals, curated from each
# table's real content (not invented) -> keyed by (section/subsection title,
# row-1 header tuple).
TABLE_TITLES = {
    ('4. Operadores básicos', ('Operador', 'Significado', 'Ejemplo', 'Resultado')): 'Tabla de operadores básicos',
    ('10. Índices y slicing', ('Indice', 'Caracter')): 'Ejemplo de indexación de caracteres',
}
for sec in sections:
    containers = [sec] + sec['subsections']
    for cont in containers:
        for b in cont['blocks']:
            if b.get('type') == 'table':
                head = tuple(b['rows'][0])
                b['title'] = TABLE_TITLES.get((cont['title'], head), 'Tabla')

# References -> structured with keys, matching known author/year patterns
# This doc has no "Referencias" heading at all -> `references` stays empty,
# no bibliography for this topic (build.js hides the Bibliografía card/rail
# entry automatically when there are zero references).
REF_KEYS = []
refs_out = []
for ref_text in references:
    key = None
    for k, needle in REF_KEYS:
        if ref_text.startswith(needle):
            key = k
            break
    refs_out.append({'key': key or slug(ref_text[:30]), 'text': ref_text})

ITALIC_SPANS = {}
for r in refs_out:
    span = ITALIC_SPANS.get(r['key'])
    if span and span in r['text']:
        r['text'] = r['text'].replace(span, '*' + span + '*', 1)

# No in-text citations to wrap either (no references to link to).
CITATIONS = []

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
# "Teoría - Recordatorio Python.docx" only, verified against the document's
# real figures before accepting) -> inserted as 'image' blocks at the front
# of the section/subsection they illustrate, image files live in t0a/img/.
# Add new ones here as they're generated; keep the underlying table/content
# block too so no information from the manual is lost, only made more visual.
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
# Empty until Tema 0a's infographics are generated in NotebookLM and the user
# hands over the downloaded files -> then compress, drop into t0a/img/, and
# add entries here the same way Tema 1's five were added (see SKILL.md's
# Interactive manual section).
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
