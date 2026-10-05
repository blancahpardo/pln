# -*- coding: utf-8 -*-
"""Figuras SVG de los manuales interactivos (temas 3-8).

Cada figura reproduce, sin añadir información, contenido que ya está en el
manual (mapa conceptual o un apartado concreto); las etiquetas se copian del
texto. Paleta de la casa: azul #003B5C, amarillo #F4C542, gris #34484F.
"""
import os
from xml.sax.saxutils import escape as esc

SITE = os.path.dirname(os.path.abspath(__file__))
AZ, AM, GR, CL, HU = '#003B5C', '#F4C542', '#34484F', '#F3F3F4', '#9FB1BA'
FONT = "Arial, Helvetica, sans-serif"
MONO = "'Courier New', monospace"


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">'
            f'<rect width="{w}" height="{h}" rx="18" fill="#fff"/>'
            f'<text x="{w/2}" y="46" text-anchor="middle" font-family="{FONT}" font-size="26" font-weight="bold" fill="{AZ}">{esc(title)}</text>'
            f'<rect x="{w/2-60}" y="58" width="120" height="4" rx="2" fill="{AM}"/>'
            f'<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{AM}"/></marker></defs>'
            + body + '</svg>')


def lines(x, y, text_lines, size, color, weight='normal', family=FONT, lh=None, anchor='middle'):
    lh = lh or size * 1.25
    return ''.join(f'<text x="{x}" y="{y + i*lh}" text-anchor="{anchor}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{color}">{esc(t)}</text>'
                   for i, t in enumerate(text_lines))


def pipeline(steps, title, per_row=4, w=1100, box_h=150):
    """steps: lista de (nombre, [líneas de detalle], estilo_detalle 'mono'|'txt')."""
    gap_x, margin = 36, 40
    box_w = (w - 2 * margin - gap_x * (per_row - 1)) / per_row
    rows = (len(steps) + per_row - 1) // per_row
    gap_y = 70
    h = 100 + rows * box_h + (rows - 1) * gap_y + 40
    body = ''
    pos = []
    for i, (name, detail, kind) in enumerate(steps):
        r, c = divmod(i, per_row)
        if r % 2 == 1:                      # recorrido en zigzag: la segunda fila va de derecha a izquierda
            c = per_row - 1 - c
        x = margin + c * (box_w + gap_x); y = 95 + r * (box_h + gap_y)
        pos.append((x, y, r, c))
        body += f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="14" fill="{CL}" stroke="{AZ}" stroke-width="2"/>'
        body += f'<circle cx="{x+26}" cy="{y+26}" r="15" fill="{AZ}"/>' + lines(x + 26, y + 32, [str(i + 1)], 15, '#fff', 'bold')
        fs = min(19, (box_w - 16) / (len(name) * 0.56))
        body += lines(x + box_w / 2, y + 62, [name], round(fs, 1), AZ, 'bold')
        fam = MONO if kind == 'mono' else FONT
        body += lines(x + box_w / 2, y + 92, detail, 15 if kind == 'mono' else 15, GR, 'normal', fam, lh=20)
    for i in range(len(pos) - 1):
        x1, y1, r1, c1 = pos[i]; x2, y2, r2, c2 = pos[i + 1]
        if r1 == r2:
            if c2 > c1:
                body += f'<line x1="{x1+box_w+4}" y1="{y1+box_h/2}" x2="{x2-6}" y2="{y2+box_h/2}" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
            else:
                body += f'<line x1="{x1-4}" y1="{y1+box_h/2}" x2="{x2+box_w+6}" y2="{y2+box_h/2}" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
        else:
            body += f'<line x1="{x1+box_w/2}" y1="{y1+box_h+4}" x2="{x2+box_w/2}" y2="{y2-6}" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
    return svg(w, h, body, title)


def save(tema, name, content):
    d = os.path.join(SITE, tema, 'img'); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
        f.write(content)


# ---------- Tema 3: mapa conceptual (filas Normalización → Glosario técnico)
save('t3', 'fig_pipeline.svg', pipeline([
    ('Normalización', ['.lower()'], 'mono'),
    ('Limpieza', ['re.sub()'], 'mono'),
    ('Tokenización', ['nlp(texto)', 'token.text'], 'mono'),
    ('Stopwords', ["stopwords.words(", "'spanish')"], 'mono'),
    ('Lematización', ['token.lemma_'], 'mono'),
    ('Frecuencia', ['Counter'], 'mono'),
    ('PoS', ['token.pos_'], 'mono'),
    ('Glosario técnico', ['Sustantivos', '+ contexto'], 'txt'),
], 'El pipeline de preprocesamiento de la unidad'))

# ---------- Tema 4: mapa conceptual (Lectura de archivos → Informe), resultado esperado
save('t4', 'fig_cadena.svg', pipeline([
    ('Lectura de archivos', ['Cadenas de texto', 'cargadas en memoria'], 'txt'),
    ('Segmentación', ['Lista de oraciones', 'o segmentos'], 'txt'),
    ('Frecuencia léxica', ['Recuentos', 'comparables'], 'txt'),
    ('Patrones formales', ['Posiciones', 'y contexto'], 'txt'),
    ('Expresiones regulares', ['Coincidencias', 'interpretables'], 'txt'),
    ('Funciones', ['Comprobaciones', 'reutilizables'], 'txt'),
    ('Informe', ['Informe de revisión', 'preliminar'], 'txt'),
], 'Del corpus al informe: resultado de cada paso'))

# ---------- Tema 6: mapa conceptual (Corpus → Interpretación crítica), resultado esperado
save('t6', 'fig_pipeline.svg', pipeline([
    ('Corpus', ['Colección organizada', 'de documentos'], 'txt'),
    ('Normalización', ['Textos más', 'comparables'], 'txt'),
    ('Tokenización', ['Listas de tokens'], 'txt'),
    ('Lematización', ['Formas más', 'generales'], 'txt'),
    ('Léxicos', ['Repertorios', 'explícitos'], 'txt'),
    ('Detección', ['Marcas por', 'documento'], 'txt'),
    ('Agregación', ['Frecuencias', 'y resúmenes'], 'txt'),
    ('KWIC', ['Concordancias'], 'txt'),
    ('Coocurrencias', ['Listado de', 'asociaciones'], 'txt'),
    ('Interpretación crítica', ['Informe lingüístico', 'prudente'], 'txt'),
], 'Del corpus a la interpretación crítica', per_row=5, w=1200))

# ---------- Tema 7: mapa conceptual (Tokenización → KWIC)
save('t7', 'fig_pipeline.svg', pipeline([
    ('Corpus', ['especializado', '+ general'], 'txt'),
    ('Tokenización', ['simple_tokenize()'], 'mono'),
    ('Stopwords', ['remove_stopwords()'], 'mono'),
    ('N-gramas', ['get_ngrams(', 'tokens, n)'], 'mono'),
    ('Frecuencia absoluta', ['Counter'], 'mono'),
    ('Frecuencia relativa', ['freq / N'], 'mono'),
    ('Weirdness', ['Ranking', 'contrastivo'], 'txt'),
    ('Heurísticas', ['Umbral, blacklist,', 'bordes'], 'txt'),
    ('KWIC', ['Ejemplos para', 'validar'], 'txt'),
], 'De los corpus a los candidatos terminológicos', per_row=5, w=1200))


# ---------- Tema 7: fórmula de weirdness (apartado 1.7)
def weirdness():
    w, h = 1100, 470
    b = ''
    b += lines(150, 245, ['weirdness(t) ='], 30, AZ, 'bold', anchor='middle')
    # numerador
    b += f'<rect x="300" y="120" width="330" height="86" rx="12" fill="{CL}" stroke="{AZ}" stroke-width="2"/>'
    b += lines(465, 172, ['f_esp(t) / N_esp'], 26, AZ, 'bold', MONO)
    b += f'<line x1="290" y1="235" x2="1030" y2="235" stroke="{AZ}" stroke-width="4"/>'
    # denominador
    b += f'<rect x="300" y="262" width="330" height="86" rx="12" fill="{CL}" stroke="{AZ}" stroke-width="2"/>'
    b += lines(465, 314, ['f_gen(t) / N_gen'], 26, AZ, 'bold', MONO)
    b += lines(675, 314, ['+'], 32, AZ, 'bold')
    b += f'<rect x="715" y="262" width="110" height="86" rx="12" fill="#FFF7DD" stroke="{AM}" stroke-width="2.5"/>'
    b += lines(770, 316, ['ε'], 34, AZ, 'bold')
    # explicaciones
    b += lines(870, 150, ['Frecuencia relativa', 'en el corpus', 'especializado'], 17, GR, 'normal', anchor='start', lh=22)
    b += f'<line x1="640" y1="163" x2="860" y2="163" stroke="{HU}" stroke-width="2" stroke-dasharray="5 4"/>'
    b += lines(870, 380, ['Frecuencia relativa', 'en el corpus general'], 17, GR, 'normal', anchor='start', lh=22)
    b += f'<line x1="465" y1="352" x2="465" y2="392" stroke="{HU}" stroke-width="2" stroke-dasharray="5 4"/><line x1="465" y1="392" x2="860" y2="392" stroke="{HU}" stroke-width="2" stroke-dasharray="5 4"/>'
    b += lines(770, 430, ['ε: número muy pequeño que evita la división entre cero'], 16, GR, 'normal')
    b += f'<line x1="770" y1="352" x2="770" y2="410" stroke="{AM}" stroke-width="2"/>'
    return svg(w, h, b, 'Weirdness: fórmula didáctica de la unidad')


save('t7', 'fig_weirdness.svg', weirdness())


# ---------- Tema 5: tipos de similitud (apartado 1.3) y métricas (mapa conceptual, 1.11)
def metricas():
    w, h = 1200, 560
    cols = [
        ('Similitud superficial', 'Coincidencia de palabras o caracteres', [('Precision · Recall · F1', 'palabras'), ('Exact Match · Jaccard', 'palabras'), ('chrF', 'caracteres')]),
        ('Similitud estructural', 'Coincidencia de secuencias u orden', [('BLEU', 'n-gramas'), ('METEOR', 'coincidencias flexibles y orden')]),
        ('Similitud semántica', 'Coincidencia de significado', [('BERTScore', 'embeddings contextuales'), ('BLEURT', 'aprende de juicios humanos'), ('COMET', 'también puede usar el texto fuente')]),
    ]
    b = ''
    cw, gap, x0 = 352, 32, 40
    for i, (name, obs, metrics) in enumerate(cols):
        x = x0 + i * (cw + gap)
        b += f'<rect x="{x}" y="90" width="{cw}" height="430" rx="16" fill="{CL}"/>'
        b += f'<rect x="{x}" y="90" width="{cw}" height="88" rx="16" fill="{AZ}"/><rect x="{x}" y="150" width="{cw}" height="28" fill="{AZ}"/>'
        b += lines(x + cw / 2, 128, [name], 21, '#fff', 'bold')
        b += lines(x + cw / 2, 158, [obs], 14.5, AM, 'bold')
        for j, (m, note) in enumerate(metrics):
            y = 205 + j * 102
            b += f'<rect x="{x+20}" y="{y}" width="{cw-40}" height="82" rx="12" fill="#fff" stroke="{HU}" stroke-width="1.5"/>'
            b += lines(x + cw / 2, y + 35, [m], 19, AZ, 'bold')
            b += lines(x + cw / 2, y + 61, [note], 14.5, GR)
    b += lines(w / 2, 548, ['Métricas clásicas: sobre todo similitud superficial y estructural · Métricas neuronales: se aproximan mejor a la similitud semántica'], 14.5, GR)
    return svg(w, h, b, 'Qué observa cada métrica')


save('t5', 'fig_metricas.svg', metricas())


# ---------- Tema 8: clasificación por prototipos (apartado 1.7 y mapa conceptual)
def prototipos():
    w, h = 1200, 560
    b = ''
    steps = [('Texto', ['por clasificar'], 'txt'), ('Preprocesamiento', ['spaCy: tokenizar,', 'lematizar, filtrar'], 'txt'), ('Vector TF', ['Counter(tokens)'], 'mono')]
    for i, (n, d, k) in enumerate(steps):
        x = 40; y = 95 + i * 150
        b += f'<rect x="{x}" y="{y}" width="260" height="120" rx="14" fill="{CL}" stroke="{AZ}" stroke-width="2"/>'
        b += lines(x + 130, y + 48, [n], 20, AZ, 'bold') + lines(x + 130, y + 78, d, 15, GR, 'normal', MONO if k == 'mono' else FONT, lh=20)
        if i < 2:
            b += f'<line x1="170" y1="{y+124}" x2="170" y2="{y+144}" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
    clases = ['Jurídico', 'Técnico', 'Divulgativo', 'Literario']
    for j, c in enumerate(clases):
        y = 95 + j * 108
        b += f'<line x1="304" y1="{395}" x2="436" y2="{y+45}" stroke="{AM}" stroke-width="3" marker-end="url(#ar)"/>'
        b += f'<rect x="440" y="{y}" width="330" height="90" rx="14" fill="#fff" stroke="{AZ}" stroke-width="2"/>'
        b += lines(605, y + 36, [f'Prototipo {c.lower()}'], 18, AZ, 'bold')
        sub = 'p. ej. ley, artículo, obligación, contrato' if c == 'Jurídico' else 'palabras clave de la clase'
        b += lines(605, y + 64, [sub], 14, GR)
        b += lines(785, y + 52, ['coseno'], 14, GR, 'normal', anchor='start')
    b += f'<rect x="870" y="160" width="290" height="120" rx="14" fill="{AZ}"/>'
    b += lines(1015, 205, ['Clasificación'], 21, '#fff', 'bold') + lines(1015, 240, ['max(scores, key=scores.get)'], 13.5, AM, 'bold', MONO)
    b += f'<line x1="845" y1="260" x2="866" y2="230" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
    b += f'<rect x="870" y="330" width="290" height="120" rx="14" fill="#FFF7DD" stroke="{AM}" stroke-width="2.5"/>'
    b += lines(1015, 375, ['Evidencias'], 21, AZ, 'bold') + lines(1015, 405, ['lemas compartidos', 'texto / prototipo'], 15, GR, lh=20)
    b += f'<line x1="1015" y1="284" x2="1015" y2="326" stroke="{AM}" stroke-width="4" marker-end="url(#ar)"/>'
    b += lines(w / 2, 540, ['Gana la clase más similar · las evidencias hacen visible el criterio de la decisión'], 15, GR)
    return svg(w, h, b, 'Clasificación por prototipos temáticos')


save('t8', 'fig_prototipos.svg', prototipos())
print('figuras generadas')
