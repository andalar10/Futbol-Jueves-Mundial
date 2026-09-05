# Changelog

Histórico de **funcionalidades** de la app (no de mensajes de commit técnicos).
Cada entrada describe qué puede hacer ahora el usuario que no podía antes.

## [Sin publicar]

### Añadido
- **Catálogo de jugadores** (tabla `jugadores`, puramente aditiva): guarda los
  nicks/apodos reales del grupo para poder reutilizarlos de forma consistente
  en toda la app, en vez de escribir el nombre suelto cada vez. Se sembró con
  todos los nombres distintos que ya existían en el histórico, sin tocar ni
  fusionar nada de lo guardado.
- **Selector de jugador con autocomplete**: al escribir un nombre en el editor
  de alineación (nuevo partido, edición en el historial, o al elegir quién
  entra en una sustitución) aparece un desplegable con las coincidencias del
  catálogo, para poder distinguir jugadores con nombres parecidos (p. ej. dos
  personas apodadas "Iván", una de ellas con icono ⚡). Si no hay ninguna
  coincidencia, permite dar de alta un jugador nuevo en el momento sin salir
  del formulario.
- **Sustituciones con selectores en vez de editar toda la plantilla**: el
  botón "🔁 Sustitución" ahora muestra un desplegable para elegir a quién se
  saca (limitado a quien está en el campo en ese momento) y un autocomplete
  para quién entra, en vez de obligar a borrar una fila y crear otra a mano.
  Admite varias sustituciones encadenadas en una misma tanda (p. ej. A sale y
  entra B, y a continuación B sale y entra C).
- **Corrección retroactiva de sustituciones** ("✏️ Editar sustituciones" en
  cada versión del historial): permite reabrir y corregir la lista de
  sustituciones ya guardada de una alineación (añadir, quitar o cambiar
  filas), recalculando la plantilla de esa versión a partir de la anterior.
  Pensado para arreglar sustituciones que quedaron mal registradas o
  incompletas.
- Los minutos automáticos de un jugador ya no se reparten por tramos según el
  número de versiones de la alineación: ahora una sustitución de este grupo se
  entiende como una baja **antes** del partido (para organizar quién viene a
  jugar), así que el jugador que sale cuenta siempre 0 minutos y el que entra
  60, salvo que se editen a mano desde "⚽ Editar minutos, goles y tarjetas".

### Corregido (datos)
- Partido del 2026-09-03: la sustitución de Guiem por Dani R. no había quedado
  registrada (solo se guardó la baja de Guiem sin el sustituto). Se corrigió
  el registro para reflejar "Guiem → Dani R." Los minutos de ese partido ya
  estaban bien ajustados a mano y no se han tocado.

## 2026-08-20 — Estadísticas de goles y tarjetas
- Botón para registrar goles, tarjetas amarillas/rojas y minutos jugados por
  jugador y partido (tabla `estadisticas_partido_jugador`), con valores
  automáticos por defecto si no se editan a mano.
- Estadísticas de "Máximos goleadores" y "Tarjetas" en la pestaña de
  Estadísticas.
- Botón para registrar una sustitución reutilizando la misma foto (primera
  versión, sustituida ahora por el editor de pares con selectores).
- Ajustes de maquetación en escritorio y arreglo de cómo se pintan los emojis
  (tanto en la app como en el PDF generado).

## 2026-08-19 — Sustituciones y estadísticas de jugadores
- Registrar una sustitución sin volver a subir foto (crea una nueva versión
  reutilizando la imagen de la anterior).
- Estadísticas por jugador (partidos jugados, victorias/empates/derrotas) vía
  vista `estadisticas_jugadores`.

## 2026-08-18 — Primera versión
- Alta de partido: fecha, texto de convocatoria, foto con lectura automática
  por IA (visión), resultado opcional.
- Detección automática de bajas/altas al guardar una nueva versión de un
  partido ya existente.
- Historial de partidos con badges de qué datos tiene cada uno, edición de
  convocatoria/resultado a posteriori, edición manual de jugadores por
  versión, reprocesado con IA, borrado de una versión o del día completo.
- Exportar/Importar JSON de todo el histórico.
- Generar libro en PDF (una página por partido: fecha, resultado,
  convocatoria, foto, bloque de bajas/sustituciones).
- Migración de todo el modelo de datos a Supabase (Postgres), con trigger que
  invalida automáticamente la versión anterior de una alineación al guardar
  una nueva.

---

## Funciones/rutinas clave a vigilar en cada cambio

Antes de dar por cerrado un cambio en `index.html`, comprobar con `grep` que
estas funciones siguen existiendo y no se han eliminado sin querer (todas
deben aparecer, cada una definida una sola vez):

`cargarDesdeSupabase`, `cargarJugadoresCatalogo`, `crearComboboxJugador`,
`asegurarJugadorExiste`, `crearEditorSustituciones`, `iniciarSustitucion`,
`guardarSustitucion`, `pintarCambiosVersion`, `editarCambiosVersion`,
`guardarEdicionCambios`, `entrarModoEdicion`, `crearEditorEquiposHistorial`,
`guardarJugadoresVersion`, `reprocesarVersion`, `extraerAlineacion`,
`llamarExtraccion`, `chequearVersionAnterior`, `calcularMinutosAutomaticos`,
`jugadoresUnicosPartido`, `estadisticasEfectivasPartido`,
`pintarEstadisticasPartido`, `renderHistorial`, `renderStats`,
`renderStatsJugadores`, `renderStatsGolesTarjetas`, `eliminarVersion`,
`eliminarDia`, `generarLibroPDF`.

Ejemplo rápido:

```bash
for fn in cargarDesdeSupabase generarLibroPDF renderHistorial calcularMinutosAutomaticos; do
  echo "$fn: $(grep -c "function $fn(" index.html)"
done
```

Cada una debe salir con recuento `1`. Un `0` significa que se perdió esa
función; un número mayor que `1` significa que quedó duplicada.
