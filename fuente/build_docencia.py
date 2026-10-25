"""Actualiza la docencia de la fuente de una página a partir de docencia_actualizable.xlsx
y añade a la fuente las reglas de impresión del botón PDF.

Uso:  python build_docencia.py docencia_actualizable.xlsx fuente-una-pagina.html
Luego: python build_pages.py fuente-una-pagina.html dist

Regenera estas tablas (solo las filas con «Mostrar en la web = Sí»):
  - Asignaturas de los últimos cinco cursos        (hoja «Asignaturas últimos cursos»)
  - Trayectoria docente                            (hoja «Trayectoria docente»)
  - Proyectos de innovación y mejora docente       (hoja «Innovación docente»)
  - Trabajos fin de estudios tutorizados           (hoja «TFG y TFM tutorizados»)
Los textos y cifras de alrededor no se tocan: si ya no coinciden con el Excel, el script avisa.
Se puede ejecutar varias veces: el resultado es el mismo.
"""
import sys, re, html
import openpyxl

xlsx, fuente = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(xlsx, data_only=True)
S = open(fuente, encoding="utf-8").read()
avisos = []

ROL_EN = {"Participante": "Participant", "Subdirector": "Deputy director", "Director": "Director",
          "Coordinador": "Coordinator", "Investigador principal": "Principal investigator",
          "Tutor": "Supervisor", "Tutora": "Supervisor", "Cotutor": "Co-supervisor"}
ESTADO_EN = {"En curso": "Ongoing", "Finalizado": "Completed"}


def e(t):
    return html.escape(str(t).strip(), quote=False)


def bi(es, en):
    return f'<span data-l="es">{es}</span><span data-l="en">{en}</span>'


def si(v):
    return str(v or "").strip().lower() in ("sí", "si", "s", "yes")


def curso(v):
    return str(v).strip().replace("-", "/")


def traducido(valor, tabla, que):
    v = str(valor or "").strip()
    if v in tabla:
        return bi(e(v), tabla[v])
    avisos.append(f"Sin traducción al inglés para {que} «{v}»: se usa el texto en español.")
    return bi(e(v), e(v))


def filas(hoja):
    """Filas de datos (desde la fila 3), saltando las vacías."""
    ws = wb[hoja]
    return [r for r in ws.iter_rows(min_row=3, values_only=True) if any(c not in (None, "") for c in r)]


def reemplaza_tbody(marca, nuevo):
    global S
    i = S.find(marca)
    if i < 0:
        avisos.append(f"No encuentro en la fuente el apartado «{marca}»: no se ha actualizado.")
        return
    a = S.index("<tbody>", i)
    b = S.index("</tbody>", a) + len("</tbody>")
    S = S[:a] + "<tbody>" + nuevo + "</tbody>" + S[b:]


def tr(*celdas):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in celdas) + "</tr>"


# ---------- Asignaturas de los últimos cursos ----------
m = re.search(r"Asignaturas de los últimos cinco cursos \((\d{4})/\d{2} a (\d{4})/\d{2}\)", S)
if not m:
    sys.exit("No encuentro el título «Asignaturas de los últimos cinco cursos (aaaa/aa a aaaa/aa)» en la fuente.")
desde, hasta = int(m.group(1)), int(m.group(2))

grupos = {}
for i, r in enumerate(filas("Asignaturas últimos cursos")):
    cur, tit, asig, mostrar = r[0], r[1], r[2], r[3]
    if not (cur and asig and si(mostrar)):
        continue
    c = curso(cur)
    try:
        ini = int(c[:4])
    except ValueError:
        avisos.append(f"Curso no válido en «Asignaturas últimos cursos»: {cur!r}")
        continue
    if not desde <= ini <= hasta:
        continue
    g = grupos.setdefault((str(asig).strip(), str(tit).strip()), dict(cursos={}, orden=i))
    g["cursos"][ini] = c


def formato_cursos(cursos):
    años = sorted(cursos)
    tramos, actual = [], [años[0]]
    for a in años[1:]:
        if a == actual[-1] + 1:
            actual.append(a)
        else:
            tramos.append(actual)
            actual = [a]
    tramos.append(actual)
    partes = []
    for t in tramos:
        if len(t) >= 3:
            partes.append(f"{cursos[t[0]]} a {cursos[t[-1]]}")
        else:
            partes.extend(cursos[a] for a in t)
    return ", ".join(partes)


def rango_titulacion(tit):
    if tit.startswith("Grado en Ingeniería Biomédica"):
        return 0
    return 1 if tit.startswith("Grado") else 2


orden = sorted(grupos.items(), key=lambda kv: (-max(kv[1]["cursos"]), rango_titulacion(kv[0][1]), kv[1]["orden"]))
reemplaza_tbody(m.group(0),
                "".join(tr(e(asig), e(tit), formato_cursos(g["cursos"])) for (asig, tit), g in orden))
print(f"Asignaturas {desde}-{hasta}: {len(orden)} filas")

# ---------- Trayectoria docente ----------
def tramo(d, h):
    d, h = str(d).strip(), str(h).strip()
    if h.lower() == "actualidad":
        return f"desde {d}"
    return d if d == h else f"{d} – {h}"


tray = {}
for r in filas("Trayectoria docente"):
    asig, tit, d, h, _car, mostrar = r[:6]
    if not (asig and d and h and si(mostrar)):
        continue
    tray.setdefault((str(asig).strip(), str(tit).strip()), []).append(tramo(d, h))
reemplaza_tbody('<h3><span data-l="es">Trayectoria docente</span>',
                "".join(tr(e(a), e(t), " y ".join(ts)) for (a, t), ts in tray.items()))
print(f"Trayectoria: {len(tray)} asignaturas")
if f"{len(tray)} asignaturas desde" not in S:
    avisos.append(f"La trayectoria tiene {len(tray)} asignaturas, pero el texto «Ver la trayectoria completa: N asignaturas desde…» de la fuente dice otra cifra: corrígelo.")

# ---------- Proyectos de innovación y mejora docente ----------
inn = []
for r in filas("Innovación docente"):
    conv, proy, rol, estado, mostrar = r[:5]
    if not (proy and si(mostrar)):
        continue
    inn.append(tr(e(conv), e(proy), traducido(rol, ROL_EN, "el rol"), traducido(estado, ESTADO_EN, "el estado")))
reemplaza_tbody('<h3><span data-l="es">Proyectos de innovación y mejora docente', "".join(inn))
print(f"Innovación docente: {len(inn)} proyectos")

# ---------- Trabajos fin de estudios tutorizados ----------
tfg = []
for r in filas("TFG y TFM tutorizados"):
    cur, titulo, tit, rol = r[:4]
    if not titulo:
        continue
    tfg.append(tr(curso(cur), e(titulo), e(tit), traducido(rol, ROL_EN, "el rol")))
reemplaza_tbody('<h3><span data-l="es">Trabajos fin de estudios tutorizados', "".join(tfg))
print(f"TFG y TFM: {len(tfg)} trabajos")
if f"{len(tfg)} trabajos fin de grado tutorizados" not in S:
    avisos.append(f"Hay {len(tfg)} trabajos fin de estudios en el Excel, pero la fuente dice otra cifra en «N trabajos fin de grado tutorizados…» (texto, cifra destacada y años): corrígelo.")

# ---------- Impresión (botón PDF) ----------
PRINT_CSS = (
    "/* impresion-v2 */@page{margin:14mm}"
    "@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}"
    ".hero .lead,.hero .sub,.hero .eyebrow,.pagehead .sub{color:#000!important;opacity:1}"
    "footer{background:#fff;color:#222;border-top:2px solid var(--red)}footer a{color:var(--red)}"
    ".card,.post,.featured,.li-featured,.news li,.kpis div,.impact .res-line,tr,figure,img{break-inside:avoid;page-break-inside:avoid}"
    "h2,h3,h4{break-after:avoid;page-break-after:avoid}thead{display:table-header-group}}"
)
if "/* impresion-v2 */" not in S:
    S = S.replace("</style>", PRINT_CSS + "</style>", 1)
    print("Reglas de impresión añadidas.")

open(fuente, "w", encoding="utf-8").write(S)
for a in avisos:
    print("AVISO:", a)
