# -*- coding: utf-8 -*-
import docx, json, re
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = '/Users/blanca/Library/CloudStorage/OneDrive-UniversidadPontificiaComillas/2. Trabajo/4. UPComillas/1. Docencia UPCO/21. Programación para PLN/1. PLN 1/0. Teoría PLN1/Teoría_PLN1_v2.docx'
OUT = '/tmp/pln-interactive/t1/manual_interactivo.json'

d = docx.Document(SRC)

def iter_block_items(parent):
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

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
        stream.append(('p', style, it.text))
    else:
        cell = it.rows[0].cells[0]
        tcPr = cell._tc.find(qn('w:tcPr'))
        shd = tcPr.find(qn('w:shd')) if tcPr is not None else None
        fill = shd.get(qn('w:fill')) if shd is not None else None
        if fill == 'F2F4F5':
            stream.append(('code', None, cell.text))
        else:
            rows = [[c.text for c in r.cells] for r in it.rows]
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
    '2. Python para PLN: del texto como dato al primer prototipo de legibilidad': 'Python para PLN',
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
    ('1. Marco teórico', ('Elemento', 'Función didáctica', 'Riesgo que conviene controlar')): 'Piezas de un notebook',
    ('1. Marco teórico', ('Decisión', 'Regla simple de la unidad', 'Limitación lingüística')): 'Qué cuenta cada unidad lingüística',
    ('2. Python para PLN: del texto como dato al primer prototipo de legibilidad', ('Medida', 'Resultado')): None,  # resolved below by content
    ('2. Python para PLN: del texto como dato al primer prototipo de legibilidad', ('Fragmento', 'Significado')): 'Partes del patrón regex',
    ('2. Python para PLN: del texto como dato al primer prototipo de legibilidad', ('Parte de la fórmula', 'Qué mide', 'Interpretación')): 'Fórmula del índice de legibilidad',
}
# The four "Medida / Resultado" tables are distinguished by their first data row.
MEDIDA_RESULTADO_TITLES = {
    'Número de palabras': 'Número de palabras',
    'Signos encontrados': 'Signos de puntuación encontrados',
    'Número aproximado de sílabas': 'Número de sílabas',
    'Palabras': 'Resultado del índice de legibilidad',
}
for sec in sections:
    containers = [sec] + sec['subsections']
    for cont in containers:
        for b in cont['blocks']:
            if b.get('type') == 'table':
                head = tuple(b['rows'][0])
                if head == ('Medida', 'Resultado'):
                    b['title'] = MEDIDA_RESULTADO_TITLES.get(b['rows'][1][0], 'Resultado')
                else:
                    b['title'] = TABLE_TITLES.get((sec['title'], head), 'Tabla')

# References -> structured with keys, matching known author/year patterns
REF_KEYS = [
    ('biber1998', 'Biber, D., Conrad, S. y Reppen, R. (1998)'),
    ('bird2009', "Bird, S., Klein, E. y Loper, E. (2009)"),
    ('fernandezhuerta1959', 'Fernández Huerta, J. (1959)'),
    ('flesch1948', 'Flesch, R. (1948)'),
    ('google2026', 'Google. (2026)'),
    ('gries2009', 'Gries, S. T. (2009)'),
    ('jupyter2026', 'Jupyter Notebook Team. (2026)'),
    ('jurafsky2026', 'Jurafsky, D. y Martin, J. H. (2026)'),
    ('kluyver2016', 'Kluyver, T.,'),
    ('psf2026a', 'Python Software Foundation. (2026a)'),
    ('psf2026b', 'Python Software Foundation. (2026b)'),
    ('psf2026c', 'Python Software Foundation. (2026c)'),
    ('psf2026d', 'Python Software Foundation. (2026d)'),
    ('szigriszt1993', 'Szigriszt Pazos, F. (1993)'),
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
    'biber1998': 'Corpus linguistics: Investigating language structure and use',
    'bird2009': 'Natural language processing with Python',
    'fernandezhuerta1959': 'Consigna, 214',
    'flesch1948': 'Journal of Applied Psychology, 32',
    'google2026': 'Colaboratory: Frequently asked questions',
    'gries2009': 'Quantitative corpus linguistics with R: A practical introduction',
    'jupyter2026': 'Jupyter Notebook documentation',
    'jurafsky2026': 'Speech and language processing',
    'kluyver2016': 'Positioning and power in academic publishing: Players, agents and agendas',
    'psf2026a': 'Python 3.14 documentation',
    'psf2026b': 'Python 3.14 documentation',
    'psf2026c': 'Python 3.14 documentation',
    'psf2026d': 'Python 3.14 documentation',
    'szigriszt1993': 'Sistemas predictivos de legibilidad del mensaje escrito: Fórmula de perspicuidad',
}
for r in refs_out:
    span = ITALIC_SPANS.get(r['key'])
    if span and span in r['text']:
        r['text'] = r['text'].replace(span, '*' + span + '*', 1)

# Inline citation wrapping: exact-substring replace across all 'p' block texts and errorlist descs
CITATIONS = [
    ('(Biber, Conrad y Reppen, 1998; Gries, 2009)', ['biber1998', 'gries2009']),
    ('(Kluyver et al., 2016)', ['kluyver2016']),
    ('(Bird, Klein y Loper, 2009; Jurafsky y Martin, 2026)', ['bird2009', 'jurafsky2026']),
    ('(Python Software Foundation, 2026a)', ['psf2026a']),
    ('(Python Software Foundation, 2026b)', ['psf2026b']),
    ('(Python Software Foundation, 2026c)', ['psf2026c']),
    ('(Python Software Foundation, 2026d)', ['psf2026d']),
    ('Flesch (1948)', ['flesch1948']),
    ('Fernández Huerta (1959)', ['fernandezhuerta1959']),
    ('Szigriszt Pazos (1993)', ['szigriszt1993']),
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

data = {'header': header, 'sections': sections, 'references': refs_out}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('sections:', len(sections))
for s in sections:
    print(' -', s['title'], '| subsecciones:', len(s['subsections']), '| blocks:', len(s['blocks']))
print('references:', len(refs_out))
missing_keys = [r['text'][:40] for r in refs_out if r['key'] is None]
print('missing keys:', missing_keys)
