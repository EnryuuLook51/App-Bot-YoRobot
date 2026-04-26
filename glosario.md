# 📖 Glosario de Comandos — YoRobot v2.0

> Referencia rápida de todos los comandos disponibles.
> Prefijo: `!` (comandos clásicos) o `/` (slash commands)

---

## 🤖 Inteligencia Artificial

| Comando              | Descripción                                                       | Ejemplo                                             |
| -------------------- | ----------------------------------------------------------------- | --------------------------------------------------- |
| `/pregunta <texto>`  | Hazle cualquier pregunta a la IA                                  | `/pregunta ¿Cómo centro un div en CSS?`             |
| `/iaver [pregunta]`  | Analiza una imagen adjunta (bajo demanda)                         | `/iaver ¿Qué error tiene este código?` + imagen     |
| `/ialeer [pregunta]` | Lee y analiza un archivo de código adjunto                        | `/ialeer ¿Cómo puedo optimizar esto?` + archivo .py |
| `/iachat`            | Abre un hilo con la IA que recuerda el contexto (últimos 10 msgs) | `/iachat`                                           |
| `/iareview <código>` | Code review: bugs, mejoras y puntuación del 1 al 10               | `/iareview function sum(a,b){return a-b}`           |
| `/iadocs <código>`   | Genera documentación (docstrings/JSDoc) para tu código            | `/iadocs def calcular_total(items):`                |
| `/iastats`           | Ver tu consumo de IA del día (texto, imágenes, archivos, mixes)   | `/iastats`                                          |

**Límites diarios por usuario:**
- 💬 Texto: ilimitado (con logging)
- 🖼️ Imágenes: 10/día
- 📄 Archivos: 20/día
- 🎵 Mixes IA: 5/día

---

## 🎵 Música

### Reproducción

| Comando            | Descripción                                           | Ejemplo                    |
| ------------------ | ----------------------------------------------------- | -------------------------- |
| `/play <búsqueda>` | Reproduce o encola una canción de YouTube             | `/play lofi hip hop radio` |
| `/cola`            | Muestra la cola de reproducción actual                | `/cola`                    |
| `/skip`            | Salta a la siguiente canción en la cola               | `/skip`                    |
| `/pause`           | Pausa la canción actual                               | `/pause`                   |
| `/resume`          | Reanuda la reproducción pausada                       | `/resume`                  |
| `/np`              | Muestra la canción que se está reproduciendo ahora    | `/np`                      |
| `/stop`            | Detiene la música, limpia la cola y desconecta al bot | `/stop`                    |

### Mixes (Playlists)

| Comando                           | Descripción                                                | Ejemplo                                                 |
| --------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------- |
| `/mix crear <nombre>`             | Crea un mix vacío                                          | `/mix crear CodingNight`                                |
| `/mix agregar <nombre> <canción>` | Agrega una canción a un mix existente                      | `/mix agregar CodingNight Daft Punk - Around the World` |
| `/mix reproducir <nombre>`        | Reproduce todas las canciones de un mix                    | `/mix reproducir CodingNight`                           |
| `/mix listar`                     | Ver todos tus mixes guardados                              | `/mix listar`                                           |
| `/mix eliminar <nombre>`          | Elimina un mix permanentemente                             | `/mix eliminar CodingNight`                             |
| `/mix ia <descripción>`           | La IA genera un mix personalizado con botones interactivos | `/mix ia jazz suave para programar de noche`            |

**Límites de mixes:**
- Máximo 30 canciones por mix
- Máximo 10 mixes por usuario
- Máximo 5 generaciones de mix IA por día

---

## 🏢 Roles del Equipo

| Comando                       | Descripción                                    | Permiso | Ejemplo                        |
| ----------------------------- | ---------------------------------------------- | ------- | ------------------------------ |
| `/rolmenu`                    | Muestra el menú interactivo para elegir tu rol | Todos   | `/rolmenu`                     |
| `/equipo`                     | Ver la distribución del equipo por rol         | Todos   | `/equipo`                      |
| `/rolasignar <usuario> <rol>` | Asigna un rol a un usuario                     | Admin   | `/rolasignar @Carlos frontend` |
| `/rolquitar <usuario> <rol>`  | Quita un rol a un usuario                      | Admin   | `/rolquitar @Carlos frontend`  |

**Roles disponibles:**
| Clave      | Rol             | Emoji |
| ---------- | --------------- | ----- |
| `frontend` | Frontend Dev    | 🎨     |
| `backend`  | Backend Dev     | ⚙️     |
| `mobile`   | Mobile Dev      | 📱     |
| `pm`       | Project Manager | 🎯     |
| `qa`       | QA / Tester     | 🧪     |
| `uiux`     | UI/UX Designer  | 🎨     |
| `pasante`  | Pasante         | 📚     |

---

## 📋 Tareas / Tickets

| Comando                                                 | Descripción                              | Ejemplo                                        |
| ------------------------------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| `/tarea <título> [asignado] [prioridad] [fecha_limite]` | Crea una nueva tarea                     | `/tarea Diseñar login @Carlos alta 2026-05-01` |
| `/tareas [filtro]`                                      | Lista tareas del equipo con filtro       | `/tareas urgentes`                             |
| `/mistareas`                                            | Ver solo tus tareas asignadas            | `/mistareas`                                   |
| `/tareaestado <ID> <estado>`                            | Cambia el estado de una tarea            | `/tareaestado 5 en-progreso`                   |
| `/tablero`                                              | Vista tipo Kanban con todas las columnas | `/tablero`                                     |

**Filtros disponibles para `/tareas`:**
| Filtro        | Descripción              |
| ------------- | ------------------------ |
| `pendientes`  | Tareas sin comenzar      |
| `en-progreso` | Tareas en desarrollo     |
| `completadas` | Tareas terminadas        |
| `mias`        | Solo tus tareas          |
| `urgentes`    | Prioridad alta o crítica |
| `vencidas`    | Pasaron su fecha límite  |

**Estados de una tarea:**
`pendiente` 🔸 → `en-progreso` 🔵 → `revisión` 🟡 → `completada` ✅

**Prioridades:**
`baja` 🟢 · `media` 🟡 · `alta` 🟠 · `crítica` 🔴

---

## 🌅 Standups Diarios

| Comando           | Descripción                                                  | Ejemplo           |
| ----------------- | ------------------------------------------------------------ | ----------------- |
| `/standup`        | Abre el formulario de standup diario (modal con 3 preguntas) | `/standup`        |
| `/standups`       | Ver todos los standups reportados hoy                        | `/standups`       |
| `/standupresumen` | Resumen semanal: quién reportó y cuántos días                | `/standupresumen` |

**Preguntas del standup:**
1. ¿Qué hiciste ayer?
2. ¿Qué harás hoy?
3. ¿Tienes algún bloqueo?

**Automático:** El bot envía recordatorio a las **9:00 AM** en el canal `#standups` o `#general`.

---

## ⏰ Recordatorios y Deadlines

| Comando                        | Descripción                             | Ejemplo                          |
| ------------------------------ | --------------------------------------- | -------------------------------- |
| `/recordar <tiempo> <mensaje>` | Crea un recordatorio personal           | `/recordar 2h Entregar mockups`  |
| `/deadline <fecha> <nombre>`   | Crea un deadline visible para el equipo | `/deadline 2026-05-15 Beta v1.0` |
| `/deadlines`                   | Ver todos los deadlines activos         | `/deadlines`                     |

**Formatos de tiempo para `/recordar`:**
| Formato | Significado |
| ------- | ----------- |
| `30m`   | 30 minutos  |
| `2h`    | 2 horas     |
| `1d`    | 1 día       |

**Automático:** Los deadlines notifican al equipo **24 horas** y **1 hora** antes.

---

## 📊 Reportes

| Comando    | Descripción                            | Permiso    | Ejemplo    |
| ---------- | -------------------------------------- | ---------- | ---------- |
| `/reporte` | Genera el reporte semanal bajo demanda | PM / Admin | `/reporte` |

**Automático:** El bot envía el reporte semanal cada **viernes a las 18:00** en `#reportes` o `#general`.

**Contenido del reporte:**
- ✅ Tareas completadas esta semana
- 🔸 Tareas pendientes
- 🔴 Tareas críticas
- 🏆 MVP de la semana (más tareas completadas)
- 🌅 Total de standups
- 📌 Próximo deadline

---

## 📶 Monitoreo

| Comando   | Descripción                                                      | Ejemplo   |
| --------- | ---------------------------------------------------------------- | --------- |
| `/status` | Estado del sistema: latencia, CPU, RAM, uptime, módulos cargados | `/status` |

---

## 👋 Bienvenida

Sin comandos manuales. Funciona automáticamente:
- **Cuando alguien se une:** Envía embed de bienvenida en `#bienvenida` o `#general`
- **DM de onboarding:** Instrucciones para elegir rol, usar el bot, y reportar standups

---

## 🔧 Administración del Bot (Solo Owner)

| Comando         | Descripción                               | Ejemplo                  |
| --------------- | ----------------------------------------- | ------------------------ |
| `!sync`         | Sincroniza los slash commands con Discord | `!sync`                  |
| `!reload [cog]` | Recarga un módulo o todos en caliente     | `!reload ia` / `!reload` |

---

## ⚡ Referencia Rápida

```
🤖 IA:       /pregunta  /iaver  /ialeer  /iachat  /iareview  /iadocs  /iastats
🎵 Música:   /play  /cola  /skip  /pause  /resume  /np  /stop
🎵 Mixes:    /mix crear  /mix agregar  /mix reproducir  /mix listar  /mix eliminar  /mix ia
🏢 Roles:    /rolmenu  /equipo  /rolasignar  /rolquitar
📋 Tareas:   /tarea  /tareas  /mistareas  /tareaestado  /tablero
🌅 Standup:  /standup  /standups  /standupresumen
⏰ Remind:   /recordar  /deadline  /deadlines
📊 Reportes: /reporte
📶 Monitor:  /status
🔧 Admin:    !sync  !reload
```
