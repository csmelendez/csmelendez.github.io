"""Divide la web de una sola página en index, proyectos, cv y privacidad con una plantilla común."""
import re, sys, json, os
src, outdir = sys.argv[1], sys.argv[2]
S = open(src, encoding="utf-8").read()
BASE = "https://www.cesarsanchezmelendez.es/"
FECHA = os.environ.get("FECHA") or "2026-10-23"  # fecha de la última actualización: datos estructurados y sitemap (la GitHub Action pone la del día)

def bi(es, en):
    return f'<span data-l="es">{es}</span><span data-l="en">{en}</span>'

def cut(start, end=None, frm=0):
    i = S.index(start, frm)
    j = S.index(end, i) if end else len(S)
    return S[i:j]

def section(sid):
    i = S.index(f'<section id="{sid}">')
    j = S.index('</section>', i) + len('</section>')
    return S[i:j]

def unwrap_details(h):
    h = re.sub(r'<details class="more"><summary>.*?</summary>', '', h, flags=re.S)
    return h.replace('</details>', '')

# ---------- piezas comunes ----------
head = S[:S.index('</head>')]
ld_blocks = re.findall(r'<script type="application/ld\+json">.*?</script>', head, flags=re.S)
style = re.search(r'<style>.*?</style>', head, flags=re.S).group(0)
script = S[S.index('<script>(function(){var h=document.documentElement'):S.index('</body>')]

extra_css = ("main{display:block}.pagehead{background:var(--red);color:#fff}.pagehead .in{max-width:1080px;margin:auto;padding:30px 24px 34px}"
             ".pagehead a{color:#fff}.pagehead .eyebrow a{text-decoration:none;font-weight:700}.pagehead .eyebrow a:hover{text-decoration:underline}"
             ".pagehead h1{font-size:2.2rem}.pagehead .sub{max-width:62ch;font-size:1.1rem;margin:.4em 0 0}"
             "nav a[aria-current=page]{color:var(--red);text-decoration:underline;text-underline-offset:4px}"
             ".more-cta{margin:14px 0 0}.mini{grid-template-columns:repeat(auto-fit,minmax(185px,1fr))}.mini .card h4{font-size:1.05rem}.mini .card p{margin:.3em 0}"
             "footer nav{position:static;border:0;background:none}footer .links{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 0 10px}"
             "@media print{.pagehead{background:#fff;color:#000}.pagehead a{color:#000}}")
style = style.replace('</style>', extra_css + '</style>')

NAV = [("index.html#sobre-mi", "Sobre mí", "About", "index"),
       ("index.html#docencia", "Docencia", "Teaching", "index"),
       ("proyectos.html", "Proyectos (I+D+i)", "Projects (R&amp;D&amp;I)", "proyectos"),
       ("index.html#divulgacion", "Divulgación y medios", "Outreach and media", "index"),
       ("cv.html", "CV", "CV", "cv"),
       ("index.html#contacto", "Contacto", "Contact", "index")]
tools = S[S.index('<span class="tools"'):S.index('</div></nav>')]

def nav(page):
    links = ""
    for href, es, en, pg in NAV:
        cur = ' aria-current="page"' if pg == page and not href.startswith("index.html#") else ""
        if page == "index" and href.startswith("index.html#"):
            href = href[len("index.html"):]
        links += f'<a href="{href}"{cur}>{bi(es, en)}</a>'
    return f'<nav aria-label="Principal"><div class="in">{links}{tools}</div></nav>'

def pagehead(title_es, title_en, sub_es, sub_en):
    return (f'<header class="pagehead"><div class="in"><p class="eyebrow"><a href="index.html">César Sánchez Meléndez</a></p>'
            f'<h1>{bi(title_es, title_en)}</h1><p class="sub">{bi(sub_es, sub_en)}</p></div></header>')

AMOUNTS = re.search(r'<p><span data-l="es">Importes: .*?</p>', S, flags=re.S).group(0)
DISCLAIMER = bi("Las opiniones y contenidos de este sitio son personales y no representan a la Universidad de Castilla-La Mancha.",
                "The views and content of this site are personal and do not represent the University of Castilla-La Mancha.")
IA = (bi("Web elaborada con ayuda de herramientas de inteligencia artificial; todos los contenidos están revisados por el autor, que es responsable de ellos.",
         "Built with the help of AI tools; all content has been reviewed by the author, who is responsible for it.") +
      f' <a href="privacidad.html#sobre-esta-web">{bi("Más información", "More information")}</a>')

def footer(with_amounts):
    links = (f'<p class="links"><a href="index.html">{bi("Inicio","Home")}</a><a href="proyectos.html">{bi("Proyectos (I+D+i)","Projects (R&amp;D&amp;I)")}</a>'
             f'<a href="cv.html">CV</a><a href="index.html#contacto">{bi("Contacto","Contact")}</a><a href="privacidad.html">{bi("Política de privacidad","Privacy policy")}</a></p>')
    return f'<footer><div class="wrap">{links}{AMOUNTS if with_amounts else ""}<p>{DISCLAIMER}</p><p>{IA}</p></div></footer>'

def head_for(p):
    h = head
    h = re.sub(r'<style>.*?</style>', '', h, flags=re.S)
    for b in ld_blocks:
        h = h.replace(b, "")
    reps = {
        r'<title>.*?</title>': f'<title>{p["t_es"]}</title>',
        r'<meta name="description" content="[^"]*">': f'<meta name="description" content="{p["d_es"]}">',
        r'<meta name="robots" content="[^"]*">': f'<meta name="robots" content="{p.get("robots","index, follow, max-image-preview:large")}">',
        r'<link rel="canonical" href="[^"]*">': f'<link rel="canonical" href="{p["url"]}">',
        r'<meta property="og:type" content="[^"]*">': f'<meta property="og:type" content="{p.get("ogtype","website")}">',
        r'<meta property="og:title" content="[^"]*">': f'<meta property="og:title" content="{p["t_es"]}">',
        r'<meta property="og:description" content="[^"]*">': f'<meta property="og:description" content="{p["o_es"]}">',
        r'<meta property="og:url" content="[^"]*">': f'<meta property="og:url" content="{p["url"]}">',
        r'<meta property="og:image" content="[^"]*">': f'<meta property="og:image" content="{p["img"]}">',
        r'<meta property="og:image:alt" content="[^"]*">': f'<meta property="og:image:alt" content="{p["img_alt"]}">',
        r'<meta name="twitter:title" content="[^"]*">': f'<meta name="twitter:title" content="{p["t_es"]}">',
        r'<meta name="twitter:description" content="[^"]*">': f'<meta name="twitter:description" content="{p["o_es"]}">',
        r'<meta name="twitter:image" content="[^"]*">': f'<meta name="twitter:image" content="{p["img"]}">',
    }
    for pat, new in reps.items():
        h, n = re.subn(pat, lambda m: new, h)
        assert n == 1, pat
    if p.get("ogtype", "website") != "profile":
        h = re.sub(r'<meta property="profile:[^>]*>', '', h)
    ld = p.get("ld") or [json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": p["t_es"], "url": p["url"],
                                     "inLanguage": "es", "dateModified": FECHA,
                                     "isPartOf": {"@type": "WebSite", "name": "César Sánchez Meléndez", "url": BASE},
                                     "author": {"@id": BASE + "#persona"}}, ensure_ascii=False)]
    ld_html = "".join(x if x.startswith("<script") else f'<script type="application/ld+json">{x}</script>' for x in ld)
    return h + ld_html + style + "</head>"

def script_for(p):
    m = (f"M={{es:{{t:{json.dumps(p['t_es'],ensure_ascii=False)},d:{json.dumps(p['d_es'],ensure_ascii=False)},o:{json.dumps(p['o_es'],ensure_ascii=False)}}},"
         f"en:{{t:{json.dumps(p['t_en'],ensure_ascii=False)},d:{json.dumps(p['d_en'],ensure_ascii=False)},o:{json.dumps(p['o_en'],ensure_ascii=False)}}}}}")
    sc, n = re.subn(r"M=\{es:\{t:.*?\}\};", lambda _: m + ";", script, count=1, flags=re.S)
    assert n == 1
    return sc

# ---------- contenido ----------
hero = cut('<header class="hero" id="inicio">', '<section class="intro"')
hero = hero.replace('<a class="btn" href="#proyectos">', '<a class="btn" href="proyectos.html">')
intro = section_intro = S[S.index('<section class="intro"'):S.index('<section id="sobre-mi">')]
sobre = section("sobre-mi")

doc = section("docencia")
marks = ['<h3><span data-l="es">Asignaturas de los últimos', '<h3><span data-l="es">Trayectoria docente', '<h3><span data-l="es">Recursos docentes abiertos',
         '<h3><span data-l="es">Proyectos de innovación y mejora', '<h3><span data-l="es">Trabajos fin de estudios', '<h3><span data-l="es">Tesis, innovación',
         '<h3><span data-l="es">Formación y cualificaciones']
pos = [doc.rfind('<h3', 0, doc.index(m.replace('<h3>', '')) + 1) for m in marks] + [doc.rindex('</section>')]
doc_head = doc[:pos[0]]
parts = {i: doc[pos[i]:pos[i + 1]] for i in range(len(marks))}
doc_home = (doc_head + parts[0] + parts[2] +
            f'<p class="more-cta"><a class="btn red" href="cv.html#docencia-completa">{bi("Trayectoria docente completa","Full teaching record")}</a></p></section>')
doc_cv = ('<section id="docencia-completa"><h2>' + bi("Docencia: trayectoria completa", "Teaching: full record") + '</h2>' +
          unwrap_details(parts[1] + parts[3] + parts[4] + parts[5] + parts[6]) + '</section>')
# En el CV la tabla de TFG va completa: se quita la selección de tres
doc_cv = re.sub(r'<ul class="doc" lang="es"><li>Modelo de indicadores.*?</ul>', '', doc_cv, flags=re.S)
doc_cv = doc_cv.replace(bi("8 trabajos fin de grado tutorizados entre 2020/21 y 2023/24, tres de ellos en tecnología sanitaria:",
                           "8 final-year projects supervised between 2020/21 and 2023/24, three of them on healthcare technology:"),
                        bi("8 trabajos fin de grado tutorizados entre 2020/21 y 2023/24.", "8 final-year projects supervised between 2020/21 and 2023/24."))

proy = section("proyectos")
fichas = re.findall(r'<article class="card" id="(impacto-[a-z]+)">(.*?)</article>', proy, flags=re.S)
mini = ""
for fid, body in fichas:
    kick = re.search(r'<p class="kick">.*?</p>', body, flags=re.S).group(0)
    h4 = re.search(r'<h4>.*?</h4>', body, flags=re.S).group(0)
    dato = re.search(r'<p><strong>.*?</strong></p>', body, flags=re.S).group(0)
    mini += (f'<article class="card">{kick}{h4}{dato}<p class="more-link"><a href="proyectos.html#{fid}">{bi("Ver la ficha","See the summary")}</a></p></article>')
proy_lead = re.search(r'<p class="lead">.*?</p>', proy, flags=re.S).group(0)
proy_home = (f'<section id="proyectos-resumen"><h2>{bi("Proyectos de I+D+i","R&amp;D&amp;I projects")}</h2>'
             f'<p class="lead">{bi("55 proyectos de investigación y transferencia desde 2000, con 6,3 M€ captados para la UCLM y 3,0 M€ como investigador principal o coprincipal. Cinco líneas explican mejor qué cambia gracias a ese trabajo:","55 research and knowledge-transfer projects since 2000, with €6.3M secured for UCLM and €3.0M as principal or co-principal investigator. Five lines best explain what changes thanks to that work:")}</p>'
             f'<div class="cards mini">{mini}</div>'
             f'<p class="more-cta"><a class="btn red" href="proyectos.html">{bi("Ver los proyectos de I+D+i","See the R&amp;D&amp;I projects")}</a></p></section>')
proy_page = proy.replace(proy_lead, "", 1)
proy_page = proy_page.replace(bi("Proyectos de I+D+i e impacto", "R&amp;D&amp;I projects and impact"), bi("Cinco líneas de impacto", "Five lines of impact"), 1)

gest = section("gestion")
g_lead_end = gest.index('<h3>')
gest_home = (gest[:g_lead_end].replace('<section id="gestion">', '<section id="gestion-resumen">') +
             f'<p class="more-cta"><a class="btn red" href="cv.html#gestion">{bi("Cargos y órganos colegiados","Positions and collegiate bodies")}</a></p></section>')
gest_cv = gest

divul, medios, contacto = section("divulgacion"), section("medios"), section("contacto")
priv = section("privacidad")
priv = re.sub(r'<h2>.*?</h2>', '', priv, count=1, flags=re.S)

# ---------- páginas ----------
P = {
 "index": dict(file="index.html", url=BASE, ogtype="profile", img=BASE + "img/og-cesar-sanchez.jpg", img_alt="César Sánchez Meléndez en una mesa de ponentes",
   t_es="César Sánchez Meléndez · Tecnología sanitaria y bioeconomía forestal", t_en="César Sánchez Meléndez · Healthcare technology and forest bioeconomy",
   d_es=re.search(r'<meta name="description" content="([^"]*)">', head).group(1),
   d_en="Engineer and associate professor at UCLM. Healthcare technology (assessment, regulation and management of medical devices) and forest bioeconomy: R&D&I projects, knowledge transfer and teaching.",
   o_es=re.search(r'<meta property="og:description" content="([^"]*)">', head).group(1),
   o_en="R&D&I and knowledge-transfer projects in healthcare technology and forest bioeconomy: 55 projects and €6.3M secured for UCLM.",
   ld=ld_blocks,
   body=hero + '<main id="contenido">' + intro + sobre + doc_home + proy_home + gest_home + divul + medios + contacto + '</main>', amounts=False),
 "proyectos": dict(file="proyectos.html", url=BASE + "proyectos.html", img=BASE + "img/og-proyectos.png", img_alt="55 proyectos de I+D+i y 6,3 M€ captados para la UCLM",
   t_es="Proyectos de I+D+i · César Sánchez Meléndez", t_en="R&D&I projects · César Sánchez Meléndez",
   d_es="55 proyectos de investigación y transferencia desde 2000 y 6,3 M€ captados para la UCLM: bioeconomía forestal, ingeniería biomédica, formación en electromedicina y contratos con la industria.",
   d_en="55 research and knowledge-transfer projects since 2000 and €6.3M secured for UCLM: forest bioeconomy, biomedical engineering, clinical engineering training and industry contracts.",
   o_es="55 proyectos de I+D+i y 6,3 M€ captados para la UCLM, 3,0 M€ como investigador principal: bioeconomía forestal, ingeniería biomédica y formación en electromedicina.",
   o_en="55 R&D&I projects and €6.3M secured for UCLM, €3.0M as principal investigator: forest bioeconomy, biomedical engineering and clinical engineering training.",
   body=pagehead("Proyectos de I+D+i", "R&amp;D&amp;I projects",
                 "55 proyectos de investigación y transferencia desde 2000, con 6,3 M€ captados para la UCLM y 3,0 M€ como investigador principal o coprincipal.",
                 "55 research and knowledge-transfer projects since 2000, with €6.3M secured for UCLM and €3.0M as principal or co-principal investigator.")
        + '<main id="contenido">' + proy_page + section("investigacion") + section("transferencia") + '</main>', amounts=True),
 "cv": dict(file="cv.html", url=BASE + "cv.html", img=BASE + "img/og-cesar-sanchez.jpg", img_alt="César Sánchez Meléndez en una mesa de ponentes",
   t_es="Currículo · César Sánchez Meléndez", t_en="CV · César Sánchez Meléndez",
   d_es="Trayectoria docente completa en la UCLM desde 1999, formación en electromedicina y gestión universitaria: cargos unipersonales y órganos colegiados.",
   d_en="Full teaching record at UCLM since 1999, clinical engineering training and university management: sole-office positions and collegiate bodies.",
   o_es="Trayectoria docente desde 1999 y gestión universitaria en la UCLM: diez cargos unipersonales y vicerrector desde 2020.",
   o_en="Teaching since 1999 and university management at UCLM: ten sole-office positions and vice-rector since 2020.",
   body=pagehead("Currículo", "CV",
                 "Trayectoria docente completa y gestión universitaria. Los proyectos están en Proyectos (I+D+i). Para obtener un PDF, usa el botón PDF del menú.",
                 "Full teaching record and university management. Projects are under Projects (R&amp;D&amp;I). To get a PDF, use the PDF button in the menu.")
        + '<main id="contenido">' + doc_cv + gest_cv + '</main>', amounts=False),
 "privacidad": dict(file="privacidad.html", url=BASE + "privacidad.html", robots="noindex, follow", img=BASE + "img/og-cesar-sanchez.jpg", img_alt="César Sánchez Meléndez",
   t_es="Política de privacidad · César Sánchez Meléndez", t_en="Privacy policy · César Sánchez Meléndez",
   d_es="Política de privacidad y uso de inteligencia artificial en la web personal de César Sánchez Meléndez.", d_en="Privacy policy and use of artificial intelligence on César Sánchez Meléndez's personal website.",
   o_es="Política de privacidad y uso de inteligencia artificial en la web personal de César Sánchez Meléndez.", o_en="Privacy policy and use of artificial intelligence on César Sánchez Meléndez's personal website.",
   body=pagehead("Política de privacidad", "Privacy policy",
                 "Cómo se tratan los datos de quienes visitan esta web o me escriben, y cómo se ha elaborado la web.",
                 "How the data of visitors and people who write to me are handled, and how the website was made.")
        + '<main id="contenido">' + priv + '</main>', amounts=False),
}

pages = {}
for key, p in P.items():
    html = (head_for(p) + '<body><a class="skip" href="#contenido">Saltar al contenido / Skip to content</a>' + nav(key) +
            p["body"] + footer(p["amounts"]) + script_for(p) + "</body></html>")
    pages[key] = html

# ---------- enlaces internos entre páginas ----------
ids = {k: set(re.findall(r'\bid="([^"]+)"', v)) for k, v in pages.items()}
broken = []
for k in pages:
    def fix(m):
        anchor = m.group(1)
        if anchor in ids[k]:
            return m.group(0)
        for other, s in ids.items():
            if anchor in s:
                return f'href="{P[other]["file"]}#{anchor}"'
        broken.append((k, anchor)); return m.group(0)
    pages[k] = re.sub(r'href="#([^"]+)"', fix, pages[k])
    # enlaces a otras páginas con ancla que no existe allí
    for f, a in re.findall(r'href="([a-z]+)\.html#([^"]+)"', pages[k]):
        tgt = [x for x in P if P[x]["file"] == f + ".html"][0]
        if a not in ids[tgt]:
            broken.append((k, f + ".html#" + a))
assert not broken, broken

os.makedirs(outdir, exist_ok=True)
for k, p in P.items():
    open(os.path.join(outdir, p["file"]), "w", encoding="utf-8").write(pages[k])
    print(p["file"], len(pages[k]))

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for k in ["index", "proyectos", "cv"]:
    sm += f'  <url><loc>{P[k]["url"]}</loc><lastmod>{FECHA}</lastmod></url>\n'
for herramienta in ["clasificaMD/", "buscaPICO/"]:  # se publican desde sus propios repositorios, bajo el mismo dominio
    sm += f'  <url><loc>{BASE}{herramienta}</loc><lastmod>{FECHA}</lastmod></url>\n'
sm += '</urlset>\n'
open(os.path.join(outdir, "sitemap.xml"), "w").write(sm)
open(os.path.join(outdir, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
print("sitemap y robots ok")
