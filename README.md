# César Sánchez Meléndez · web personal

Código fuente de https://www.cesarsanchezmelendez.es/: tecnología sanitaria y bioeconomía forestal, proyectos de I+D+i, transferencia, docencia y gestión universitaria.

- `index.html`: portada (sobre mí, docencia, resumen de proyectos y de gestión, divulgación, medios y contacto).
- `proyectos.html`: Proyectos (I+D+i), con las cinco fichas de impacto y las tablas de investigación y transferencia.
- `cv.html`: trayectoria docente completa y gestión universitaria, pensada para imprimir como PDF.
- `privacidad.html`: política de privacidad y apartado «Sobre esta web y uso de inteligencia artificial».
- `sitemap.xml`: mapa del sitio para Google Search Console.

Cada página tiene dos versiones con URL propia: en español en la raíz y en inglés en la carpeta `en/` (https://www.cesarsanchezmelendez.es/en/). Las dos se enlazan entre sí con `hreflang` y el botón ES/EN lleva a la página equivalente del otro idioma. Comparten estilos y menú y no usan dependencias externas ni cookies. Los enlaces antiguos con `?lang=en` llevan a la versión inglesa.
- `en/`: versión inglesa de las cuatro páginas (se genera sola; no se edita).
- `img/`: fotografía y vista previa para redes sociales.

- `robots.txt`: indica a los buscadores dónde está el mapa del sitio.

La web se publica con dominio propio en https://www.cesarsanchezmelendez.es/. Las dos herramientas enlazadas desde Docencia viven en sus propios repositorios y se publican bajo el mismo dominio: el [Clasificador MDR/IVDR](https://github.com/csmelendez/clasificaMD) en https://www.cesarsanchezmelendez.es/clasificaMD/ y el [Buscador de evidencia PICO](https://github.com/csmelendez/buscaPICO) en https://www.cesarsanchezmelendez.es/buscaPICO/. La web las enlaza con las rutas `/clasificaMD/` y `/buscaPICO/`, así que los tres repositorios deben estar bajo el mismo usuario de GitHub, con esos nombres exactos.

## Cómo se actualiza

Las páginas no se editan a mano: se generan desde la carpeta `fuente` con los datos de la carpeta `datos`.

- `datos/docencia_actualizable.xlsx`: asignaturas, trayectoria docente, innovación docente y TFG.
- `datos/linkedin_actualizable.xlsx`: publicaciones de LinkedIn y entrevistas y prensa.
- `fuente/fuente-una-pagina.html`: la web completa en una sola página, de donde salen los textos fijos.
- `fuente/build_*.py`: los scripts que rellenan la fuente con los Excel y la dividen en páginas.
- `fuente/build_idiomas.py`: separa cada página en su versión española y su versión inglesa, con sus metadatos, datos estructurados y `hreflang`, y genera el `sitemap.xml`.

Para actualizar, sube el Excel modificado a la carpeta `datos` (*Add file → Upload files*). La GitHub Action «Publicar la web» (`.github/workflows/publicar.yml`) ejecuta los scripts, sube las páginas nuevas y la web cambia en uno o dos minutos. Los avisos de los scripts, como una traducción que falta, aparecen en la pestaña *Actions*, en el resumen de cada ejecución. Si algo falla, la web no cambia y GitHub avisa por correo.

Las carpetas `datos` y `fuente` no se publican en la web (lo indica `_config.yml`), pero el repositorio es público, así que cualquiera puede ver su contenido en GitHub, incluidas las columnas de observaciones de los Excel.

## Modo borrador

Los datos pendientes (resultados de las fichas, lista de vídeos, enlaces de prensa) están marcados en amarillo y **ocultos en la web pública**. Para verlos, abre la web con `?borrador`:

https://www.cesarsanchezmelendez.es/?borrador

## Uso de inteligencia artificial

La web se ha elaborado con ayuda de un asistente de inteligencia artificial generativa (Claude, de Anthropic) en el diseño, el código, la redacción de los textos a partir de los datos del autor y la traducción al inglés. El autor ha verificado los datos y revisado todo el contenido, y es responsable de él. El detalle está en https://www.cesarsanchezmelendez.es/privacidad.html#sobre-esta-web.

## Derechos

© 2026 César Sánchez Meléndez. Todos los derechos reservados sobre los textos, datos curriculares y fotografías de esta web. Esta web es personal y no representa a la Universidad de Castilla-La Mancha.
