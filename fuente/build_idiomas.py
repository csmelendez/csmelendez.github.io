"""Separa cada página bilingüe en dos versiones con URL propia: español en la raíz e inglés en /en/.

Se ejecuta después de build_pages.py, sobre la misma carpeta de salida:
    python fuente/build_idiomas.py _trabajo/dist

Para cada página (index, proyectos, cv, privacidad):
- quita del HTML los textos del otro idioma (elementos con data-l="es" o data-l="en");
- pone lang, title, description, Open Graph, canonical y datos estructurados del idioma;
- añade los enlaces hreflang recíprocos (es, en y x-default);
- convierte los botones ES/EN en enlaces a la página equivalente del otro idioma;
- reescribe el sitemap con las dos versiones y sus alternativas.
Los enlaces antiguos con ?lang=en llevan a la versión inglesa.
"""
import json, os, re, sys

outdir = sys.argv[1]
BASE = "https://www.cesarsanchezmelendez.es/"
FECHA = os.environ.get("FECHA") or "2026-10-25"
PAGES = ["index.html", "proyectos.html", "cv.html", "privacidad.html"]
EN_DIR = os.path.join(outdir, "en")

# Textos que la plantilla solo tiene en español y necesitan versión inglesa
ALT_EN = {
    "César Sánchez Meléndez en una mesa de ponentes / at a conference panel": "César Sánchez Meléndez at a conference panel",
    "César Sánchez Meléndez en una mesa de ponentes": "César Sánchez Meléndez at a conference panel",
    "55 proyectos de I+D+i y 6,3 M€ captados para la UCLM": "55 R&amp;D&amp;I projects and €6.3M secured for UCLM",
}
PERSONA_EN = {
    "jobTitle": "Associate Professor (Profesor Titular de Universidad)",
    "description": "Telecommunications engineer and PhD. Healthcare technology (assessment, regulation and management of medical devices), biomedical engineering and forest bioeconomy.",
    "award": ["Personality of the Year, Impulso a las Telecomunicaciones Awards (2024)",
              "Top 10 Transformative Leaders, Top100 Innovative Leaders Ranking (2023)"],
    "knowsAbout": ["Biomedical engineering", "Clinical engineering and electromedicine", "Health technology assessment",
                   "Biomedical signal processing", "Electronic instrumentation", "Forest bioeconomy",
                   "Territorial development", "Demographic challenge"],
}
RECURSO_EN = {
    "buscaPICO": "Interactive teaching tool (in Spanish) that guides users from a structured question (PICO, PECO, SPIDER) to a reproducible search strategy for PubMed, Embase, Cochrane and other databases, documented with PRISMA-S.",
    "clasificaMD": "Interactive teaching tool (in Spanish) to qualify medical devices and classify their risk under Annex VIII of Regulation (EU) 2017/745 (MDR) and Regulation (EU) 2017/746 (IVDR), with EMDN category, conformity assessment route and 113 solved practice cases.",
}


def url_for(page, lang):
    """URL pública de una página en un idioma (index.html se publica como la carpeta)."""
    base = BASE if lang == "es" else BASE + "en/"
    return base if page == "index.html" else base + page


def drop_elements(html, lang):
    """Quita los elementos <span|div data-l="lang">…</span|div>, respetando anidamientos."""
    open_re = re.compile(r'<(span|div)\b[^>]*\bdata-l="%s"[^>]*>' % lang)
    out, pos = [], 0
    while True:
        m = open_re.search(html, pos)
        if not m:
            out.append(html[pos:])
            return "".join(out)
        out.append(html[pos:m.start()])
        tag, depth, i = m.group(1), 1, m.end()
        tok = re.compile(r'<(/?)%s\b[^>]*>' % tag)
        while depth:
            t = tok.search(html, i)
            if not t:
                raise ValueError(f"<{tag} data-l={lang}> sin cerrar cerca de: {html[m.start():m.start()+80]}")
            depth += -1 if t.group(1) else 1
            i = t.end()
        pos = i


def set_meta(h, pattern, value):
    h, n = re.subn(pattern, lambda _: value, h, count=1, flags=re.S)
    assert n == 1, pattern
    return h


def script_es_en(html):
    """Lee los títulos y descripciones de cada idioma del script de la plantilla."""
    m = re.search(r"M=(\{es:\{t:.*?\}\});", html, flags=re.S)
    js = m.group(1)
    js = re.sub(r"(\{|,)(es|en|t|d|o):", r'\1"\2":', js)
    return json.loads(js)


def ld_for(blocks, lang, page, title):
    out = []
    for raw in blocks:
        d = json.loads(raw)
        t = d.get("@type")
        if t == "ProfilePage":
            d["url"] = url_for(page, lang)
            d["inLanguage"] = lang
            d["dateModified"] = FECHA
            if lang == "en":
                d["mainEntity"].update(PERSONA_EN)
        elif t == "WebPage":
            d["url"] = url_for(page, lang)
            d["name"] = title
            d["inLanguage"] = lang
        elif t == "LearningResource" and lang == "en":
            for k, v in RECURSO_EN.items():
                if f"/{k}/" in d["url"]:
                    d["description"] = v  # la herramienta sigue en español: inLanguage se mantiene "es"
        out.append(json.dumps(d, ensure_ascii=False))
    if page == "index.html":
        out.append(json.dumps({"@context": "https://schema.org", "@type": "WebSite", "@id": BASE + "#web",
                               "name": "César Sánchez Meléndez", "url": BASE, "inLanguage": ["es", "en"],
                               "author": {"@id": BASE + "#persona"}}, ensure_ascii=False))
    return "".join(f'<script type="application/ld+json">{x}</script>' for x in out)


NEW_SCRIPT = ("<script>(function(){var h=document.documentElement,q=new URLSearchParams(location.search);"
              "if(h.lang==='es'&&q.get('lang')==='en'){var e=document.querySelector('link[rel=alternate][hreflang=en]');"
              "if(e){location.replace(e.href+location.hash);return}}"
              "if(q.has('borrador'))h.classList.add('borrador');"
              "window.addEventListener('beforeprint',function(){document.querySelectorAll('details').forEach(function(d){d.open=true})});"
              "var p=document.querySelector('.pr');if(p)p.addEventListener('click',function(){window.print()})})();</script>")


def build(page, src, lang):
    other = "en" if lang == "es" else "es"
    texts = script_es_en(src)[lang]
    h = drop_elements(src, other)
    h = h.replace('<html lang="es">', f'<html lang="{lang}">', 1)

    # Cabecera: textos, URLs y alternativas de idioma
    esc = lambda s: s.replace("&", "&amp;").replace('"', "&quot;").replace("&amp;amp;", "&amp;")
    t, d, o = esc(texts["t"]), esc(texts["d"]), esc(texts["o"])
    url = url_for(page, lang)
    h = set_meta(h, r"<title>.*?</title>", f"<title>{t}</title>")
    h = set_meta(h, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{d}">')
    h = set_meta(h, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">')
    h = set_meta(h, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{o}">')
    h = set_meta(h, r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{t}">')
    h = set_meta(h, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{o}">')
    h = set_meta(h, r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">')
    h = set_meta(h, r'<meta property="og:locale" content="[^"]*">',
                 '<meta property="og:locale" content="%s">' % ("es_ES" if lang == "es" else "en_GB"))
    h = set_meta(h, r'<meta property="og:locale:alternate" content="[^"]*">',
                 '<meta property="og:locale:alternate" content="%s">' % ("en_GB" if lang == "es" else "es_ES"))
    alts = (f'<link rel="canonical" href="{url}">'
            f'<link rel="alternate" hreflang="es" href="{url_for(page, "es")}">'
            f'<link rel="alternate" hreflang="en" href="{url_for(page, "en")}">'
            f'<link rel="alternate" hreflang="x-default" href="{url_for(page, "es")}">')
    h = set_meta(h, r'<link rel="canonical" href="[^"]*">', alts)
    if lang == "en":
        for es_alt, en_alt in ALT_EN.items():
            h = h.replace(f'content="{es_alt}"', f'content="{en_alt}"').replace(f'alt="{es_alt}"', f'alt="{en_alt}"')

    # Datos estructurados del idioma
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, flags=re.S)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>', "", h, flags=re.S)
    h = h.replace("<style>", ld_for(blocks, lang, page, texts["t"]) + "<style>", 1)

    # Selector de idioma: enlaces a la página equivalente en lugar de botones
    def lb(code):
        cur = code == lang
        prefix = "" if code == lang else ("../" if lang == "en" else "en/")
        href = (prefix + ("" if page == "index.html" else page)) or "./"
        aria = ' aria-current="true"' if cur else ""
        return (f'<a class="lb" href="{href}" hreflang="{code}" lang="{code}"{aria}>{code.upper()}</a>')
    h = set_meta(h, r'<button class="lb" type="button" data-lang="es"[^>]*>ES</button><button class="lb" type="button" data-lang="en"[^>]*>EN</button>',
                 lb("es") + lb("en"))
    h = h.replace(".lb[aria-pressed=true]{background:var(--red);color:#fff}",
                  "a.lb{text-decoration:none;display:inline-block}.lb[aria-current=true]{background:var(--red);color:#fff}")
    h = h.replace('aria-label="Idioma / Language"', 'aria-label="%s"' % ("Idioma" if lang == "es" else "Language"))
    h = h.replace("Saltar al contenido / Skip to content", "Saltar al contenido" if lang == "es" else "Skip to content")
    h = h.replace('title="Imprimir / Print"', 'title="%s"' % ("Imprimir" if lang == "es" else "Print"))

    # Script: sin cambio de idioma en el navegador
    h = set_meta(h, r"<script>\(function\(\)\{var h=document\.documentElement,M=.*?</script>", NEW_SCRIPT)

    # Enlaces internos: la portada como carpeta; en /en/, las imágenes están un nivel arriba
    h = re.sub(r'href="index\.html(#[^"]*)?"', lambda m: f'href="./{m.group(1) or ""}"', h)
    if lang == "en":
        h = re.sub(r'(src|href)="img/', r'\1="../img/', h)
    leftover = re.findall(r'data-l="%s"' % other, h)
    assert not leftover, (page, lang, len(leftover))
    return h


os.makedirs(EN_DIR, exist_ok=True)
for page in PAGES:
    path = os.path.join(outdir, page)
    src = open(path, encoding="utf-8").read()
    es, en = build(page, src, "es"), build(page, src, "en")
    open(path, "w", encoding="utf-8").write(es)
    open(os.path.join(EN_DIR, page), "w", encoding="utf-8").write(en)
    print(f"{page}: es {len(es)} · en/{page} {len(en)}")

# Sitemap con las dos versiones de cada página indexable y las herramientas (solo en español)
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for page in ["index.html", "proyectos.html", "cv.html"]:
    for lang in ("es", "en"):
        sm.append(f"  <url><loc>{url_for(page, lang)}</loc><lastmod>{FECHA}</lastmod>")
        for alt in ("es", "en"):
            sm.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{url_for(page, alt)}"/>')
        sm.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{url_for(page, "es")}"/>')
        sm.append("  </url>")
for herramienta in ["clasificaMD/", "buscaPICO/"]:
    sm.append(f"  <url><loc>{BASE}{herramienta}</loc><lastmod>{FECHA}</lastmod></url>")
sm.append("</urlset>\n")
open(os.path.join(outdir, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
print("idiomas separados y sitemap con hreflang")
