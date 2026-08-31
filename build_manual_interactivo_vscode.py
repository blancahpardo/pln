# -*- coding: utf-8 -*-
import docx, json, re
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = '/Users/blanca/Library/CloudStorage/OneDrive-UniversidadPontificiaComillas/2. Trabajo/4. UPComillas/1. Docencia UPCO/21. Programación para PLN/0.0 Instalaciones iniciales/manual-entornos-python-vscode/manual_entornos_python_vscode.docx'
OUT = '/tmp/pln-interactive/inicio/vscode_manual_interactivo.json'

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
# the stopping point. Prefer stopping at "Comillas TOC Title" when the doc
# has one (its real header can itself contain a Heading-2-styled cover title,
# e.g. this doc's own title line, found adapting this for "Trabajar con
# ficheros .ipynb" -> stopping at the first *heading* would cut the header
# short there); only fall back to stopping at the first Heading 1/2 for docs
# with no TOC page at all (like "Teoría - Recordatorio Python").
_has_toc_title = any(k == 'p' and st == 'Comillas TOC Title' for k, st, c in stream)
_stop_styles = ('Comillas TOC Title',) if _has_toc_title else ('Heading 1', 'Heading 2')
header = {}
i = 0
normals = []
while i < len(stream) and not (stream[i][0]=='p' and stream[i][1] in _stop_styles):
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
    # This doc's TOC page is a single giant 'Normal' paragraph (title + tab +
    # page number, joined with '\n' for every entry) rather than separate
    # toc-1/toc-2 styled paragraphs like Teoría_PLN1/2 use -> the generic
    # toc-style skip at stream-build time never catches it. Detect it here by
    # its telltale run of tab characters and drop it explicitly.
    if i < len(stream) and stream[i][0] == 'p' and stream[i][2].count('\t') > 3:
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
        # Some docs (found adapting this for the "Trabajar con .ipynb" and
        # "Entornos de Python y VS Code" guides) style their reference
        # entries as plain 'Normal' instead of 'Comillas References' -> only
        # safe to accept both when the References section genuinely has no
        # other 'Normal' filler content (check the source before reusing).
        if kind == 'p' and style in ('Comillas References', 'Normal') and content.strip():
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
    if kind == 'p' and style == 'Heading 3':
        # This doc goes a level deeper than the sections/subsections model
        # supports (e.g. "2.2. Procedimiento principal" contains ten
        # "Paso N. ..." Heading 3s) -> rather than build a third collapsible
        # UI level, flatten it into the current subsection's content as an
        # inline bold sub-heading ('h4' block). Nothing is dropped, it just
        # reads as a longer subsection page instead of a third accordion
        # level -- appropriate here since steps are meant to be read in
        # sequence, not toggled individually.
        flush_list()
        cur_target_blocks.append({'type': 'h4', 'text': content.strip()})
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

# In T1/T2/T0a, "Título narrativo" is a single paragraph duplicating
# header['subtitle'] verbatim -> safe to drop as a chapter (it becomes the
# hero title on the manual's landing screen instead, see build.js
# imShowIndex). This doc's "Título narrativo" is NOT that trivial case
# (found adapting this for "Trabajar con ficheros .ipynb") -> it has its own
# subsection and a real narrative paragraph beyond the subtitle, so dropping
# it blindly would lose real content. Only drop it when it actually matches
# the trivial single-paragraph-duplicate shape; otherwise keep it as a real
# chapter.
def _is_trivial_titulo_narrativo(sec):
    return (
        sec['title'] == 'Título narrativo' and
        not sec['subsections'] and
        len(sec['blocks']) == 1 and
        sec['blocks'][0].get('type') == 'p' and
        sec['blocks'][0]['text'].strip() == header.get('subtitle', '').strip()
    )

sections = [s for s in sections if not _is_trivial_titulo_narrativo(s)]

# Short nav labels for the index cards (in-page chapter heading text is left
# untouched, e.g. "4. Operadores básicos" stays as-is once you're inside it).
NAV_TITLES = {
    '1. Introducción': 'Introducción',
    '2. Instalación de Visual Studio Code': 'Instalar VS Code',
    '3. Instalación de Python': 'Instalar Python',
    '4. Instalación de extensiones de VS Code': 'Extensiones de VS Code',
    '5. Uso de la Terminal integrada de VS Code': 'La Terminal de VS Code',
    '6. Creación de una carpeta de proyecto': 'Carpeta de proyecto',
    '7. Primer archivo Python': 'Primer archivo Python',
    '8. Entornos virtuales': 'Entornos virtuales',
    '9. Crear un entorno virtual en Windows': 'Entorno virtual (Windows)',
    '10. Crear un entorno virtual en macOS': 'Entorno virtual (macOS)',
    '11. Seleccionar el intérprete de Python en VS Code': 'Seleccionar intérprete',
    '12. Instalación de paquetes con pip': 'Instalar paquetes con pip',
    '13. Prueba completa con pandas': 'Prueba con pandas',
    '14. Archivo requirements.txt': 'requirements.txt',
    '15. Qué subir y qué no subir a GitHub': 'Qué subir a GitHub',
    '16. Estructura recomendada de un proyecto': 'Estructura de proyecto',
    '17. Errores frecuentes y soluciones': 'Errores frecuentes',
    '18. Flujo de trabajo recomendado para cada práctica': 'Flujo de trabajo',
    '19. Resumen final': 'Resumen final',
}
for sec in sections:
    sec['navTitle'] = NAV_TITLES.get(sec['title'], sec['title'])

# Short custom titles for "Ver tabla" buttons/modals, curated from each
# table's real content (not invented) -> keyed by (section/subsection title,
# row-1 header tuple).
TABLE_TITLES = {
    ('4. Instalación de extensiones de VS Code', ('Extensión', 'Editor', 'Para qué sirve')): 'Extensiones recomendadas',
    ('15. Qué subir y qué no subir a GitHub', ('Entrada', 'Significado')): 'Qué subir y qué no subir',
    ('16. Estructura recomendada de un proyecto', ('Elemento', 'Uso recomendado')): 'Estructura de carpetas y ficheros',
    ('Diferencia entre python, python3, python3.13 y py', ('Comando', 'Uso habitual')): 'Comandos python, python3 y py',
    ('Tabla comparativa de comandos principales', ('Tarea', 'Windows', 'macOS')): 'Comandos: Windows frente a macOS',
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
    ('ms_getting_started', 'Microsoft. (s. f.). Getting started with Python in VS Code'),
    ('ms_python_vscode', 'Microsoft. (s. f.). Python in Visual Studio Code'),
    ('ms_download_vscode', 'Microsoft. (s. f.). Download Visual Studio Code'),
    ('psf_download_python', 'Python Software Foundation. (s. f.). Download Python'),
    ('psf_venv', 'Python Software Foundation. (s. f.). venv'),
]
refs_out = []
for ref_text in references:
    key = None
    for k, needle in REF_KEYS:
        if ref_text.startswith(needle):
            key = k
            break
    refs_out.append({'key': key or slug(ref_text[:30]), 'text': ref_text})

# APA 7 italicizes the container title. The source .docx carries no run-level
# italics at all (same as every other topic checked so far), so this is
# restored here rather than lost -> for webpage/documentation-site entries
# where the author differs from the site name, italicize the site name (as
# established for Tema 1/2's "Python 3.14 documentation" entries); for the
# Google FAQ and Project Jupyter entries, the "site" and the standalone work
# are effectively the same thing, so italicize the work's own title instead.
ITALIC_SPANS = {
    'ms_getting_started': 'Visual Studio Code Documentation',
    'ms_python_vscode': 'Visual Studio Code Documentation',
    'ms_download_vscode': 'Download Visual Studio Code',
    'psf_download_python': 'Download Python',
    'psf_venv': 'Python Documentation',
}
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

# Infographics (NotebookLM), inserted as 'image' blocks at the front of the
# section/subsection they illustrate, image files would live in inicio/img/.
# Not built for this guide yet (2026-08-29: converted to interactive-manual
# format only, images explicitly deferred by the user) -> keep the underlying
# table/content block too whenever these are added, so no information from
# the manual is lost, only made more visual.
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
