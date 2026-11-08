# Posts Instagram — @alejandro.segura.asesor

Repositorio público que sirve de alojamiento de imágenes para programar posts en Metricool.

## Posicionamiento
Alejandro Segura es **asesor estratégico global de pymes** (Huelva): estrategia, organización, ventas, rentabilidad, equipo y crecimiento. Lema: Entender · Priorizar · Decidir.
NO es asesor financiero: el contenido no debe centrarse solo en caja y márgenes. Esos temas pueden aparecer, pero mezclados con estrategia, dirección, prioridades, equipo, ventas, crecimiento y toma de decisiones.

## Marca personal (desde el 8-nov, manda sobre todo lo demás)
- Base en el doc del proyecto claude/marca-personal.md: empezar ahora con 21 años, le encantan los números y las empresas, fracasar no es hacerlo mal, movimiento y libertad.
- Tres tipos de contenido: criterio para empresarios / lo que estoy construyendo / opiniones con postura.
- La materia prima sale de Alejandro (notas semanales). No inventar experiencias, casos ni cifras. Sin tono de misterio: puede hablar de sí mismo y de su camino, pero NUNCA mencionar su edad (no quiere que se sepa). "Éxito" solo con hechos reales, nunca lujo aparente.

## Flujo
1. Alejandro pide un post sobre un tema (o se le propone en la rutina del domingo a partir de sus notas de la semana).
2. Se enseña el borrador (3 diapositivas + pie de foto) y se espera su OK explícito.
3. Se generan las imágenes (1080×1350, JPG) y se suben a `NN-tema/1.jpg`, `2.jpg`, `3.jpg` (NN = número correlativo; el último usado es 10).
4. Se programan en Metricool (brand 7917252, Instagram) con las URLs
   `https://raw.githubusercontent.com/alextersm12/posts-instagram/main/NN-tema/N.jpg`.
   Nunca se publica sin su aprobación.

## Estilo
- Carrusel de 3 diapositivas, un solo color por post. Portadas alternas en la cuadrícula: azul / negro (tablero de ajedrez). El último programado (10-proximo-cliente) es negro, así que el siguiente va en azul. Plantilla con textura: `tools/render_carrusel_textura.py`.
- Azul eléctrico #1F4BFF, negro #0A0A0A, texto blanco; en posts azules la palabra destacada va en negro, en posts negros en azul. Tipografía Montserrat (500/700/800) — se obtiene de github.com/JulietaUla/Montserrat.
- Sin etiquetas ni nombre en las diapositivas; solo contador "N / 3" arriba a la derecha, flecha "→" abajo a la derecha en 1 y 2, "Escríbeme por privado" en la 3.
- 1: gancho (pregunta o frase que toca un dolor). 2: pista breve, sin contarlo todo. 3: toca el dolor e invita a escribir. Sin lema salvo en posts de método.
- Contenido dentro de la zona central (padding 190px arriba/abajo, 88px lados) para que se vea completo también en recorte cuadrado.
- Pie de foto corto y visual: 1-2 líneas con un emoji al inicio cada una, línea en blanco, pregunta con "👉", línea en blanco, #Huelva #pymes #empresarios.
- No prometer resultados ni inventar casos o cifras. No aparentar experiencia que no tiene.

## Ritmo y rutinas (agencia de redes)
- 2 carruseles por semana: lunes y jueves a las 10:00 (mejor hora según Metricool).
- Domingo: propuesta de los 2 carruseles de la semana para aprobar.
- Lunes: informe de la semana anterior + estudio de mejora + agenda de lo programado esta semana. Primer lunes de cada mes: además, estudio de competencia y revisión de estrategia.
- Métrica principal: conversaciones con empresarios iniciadas desde Instagram. Seguidores y "me gusta" son secundarios.

## Historias
- 2 por semana: martes y miércoles, ambas con caja de preguntas (no encuesta). Es una prueba de 4 semanas; en la revisión de diciembre se ajustan los días según las conversaciones que generen.
- 1080×1920. Martes: fondo negro con luz azul difusa, interrogación en contorno azul y rejilla que se desvanece. Miércoles: fondo azul en degradado con ondas finas negras. Ambos con grano fino. Plantilla: `historias/tools/render_story.py`.
- Solo la pregunta (centrada en el empresario, no en Alejandro), raya de color y @alejandro.segura.asesor abajo. Sin subtítulos tipo "Vota", "Responde", "Cuéntamelo". Sin frases de filosofía por ahora.
- Hueco libre en el centro: Alejandro añade la caja de preguntas desde el móvil (Metricool no puede poner stickers).
- Después: ver quién respondió; Claude redacta el mensaje para cada uno y Alejandro decide si lo envía. Apuntar las respuestas (dolores con sus palabras) cada semana.
- Imágenes en `historias/AAAA-MM-DD-dia.jpg`.

## Que no parezca hecho con IA (desde el 7-nov, para todos los posts nuevos)
- Nada de fondo plano liso: degradado con profundidad, luz difusa o viñeta suave, y grano fino (feTurbulence, opacidad 0.3-0.45) como en las historias.
- Un elemento gráfico con intención por post (contorno de un símbolo, ondas, rejilla que se desvanece, raya de color), nunca adornos de plantilla (puntos, corchetes).
- Variar la composición: no siempre el mismo bloque de título arriba a la izquierda; alternar título grande centrado, cifra o palabra gigante en contorno, frase partida en dos diapositivas.
- Cuando se pueda, meter algo real: foto de Huelva, de un escritorio, de unas manos con papeles (fotos propias de Alejandro, nunca de bancos de imágenes que parezcan genéricas).
- Mantener la paleta azul/negro y Montserrat; lo que cambia es la textura y la composición.

## Referente: Pedro Buerbaum (analizado el 7-nov-2026)
Copiar: ganchos cortos sobre un dolor concreto ("Ese descuento te está costando más de lo que crees"), un formato reconocible y repetido, mezcla de tipos de contenido, y que todo empuje a una acción concreta (él: webinar).
No copiar: estilo de vida aspiracional ni autoridad basada en experiencia que Alejandro aún no tiene. Detalle en el doc del proyecto claude/referente-pedro-buerbaum.md.
