# 📄 Documento de Requisitos — YoRobot v2.0

> **Proyecto:** YoRobot — Bot de Discord para gestión de equipo de desarrollo
> **Versión:** 2.0
> **Fecha:** 25 de abril de 2026
> **Equipo:** Startup de desarrollo de apps de gestión

---

## 1. Visión del Producto

YoRobot es el asistente integral del servidor de Discord de la empresa. Funciona como
herramienta de productividad, gestión de proyectos, asistente IA inteligente y
entretenimiento para el equipo. El bot debe ser modular, escalable y profesional.

---

## 2. Usuarios y Roles

| Rol                             | Permisos | Descripción                                    |
| ------------------------------- | -------- | ---------------------------------------------- |
| 👑 Fundador / Admin              | Total    | Control absoluto del bot y servidor            |
| 🎯 Project Manager               | Alto     | Gestión de tareas, sprints, reportes           |
| 💻 Developer (Front/Back/Mobile) | Medio    | Tareas, IA, música, standups                   |
| 🧪 QA / Tester                   | Medio    | Tareas, reportes de bugs                       |
| 🎨 UI/UX Designer                | Medio    | Tareas, IA para diseño                         |
| 📚 Pasante / Nuevo               | Básico   | Acceso limitado, modo lectura en canales clave |

---

## 3. Módulos y Requisitos Funcionales

---

### 3.1 🤖 Módulo de Inteligencia Artificial (`cogs/ia.py`)

#### RF-IA-01: Chat con IA (texto)
- **Comando:** `/pregunta <texto>`
- **Descripción:** Envía una consulta de texto a la IA (Qwen) y recibe una respuesta.
- **Comportamiento:** El system prompt debe estar configurado con el contexto de la empresa.
- **Límite de respuesta:** Si excede 2000 caracteres, dividir en múltiples mensajes.
- **Estado:** ✅ Ya implementado (mejorar con system prompt de empresa)

#### RF-IA-02: Análisis de imágenes bajo demanda
- **Comando:** `/ia ver <imagen adjunta> [pregunta opcional]`
- **Descripción:** El usuario adjunta una imagen y opcionalmente una pregunta. La IA analiza la imagen y responde.
- **Comportamiento:**
  - Usa el modelo **Qwen-VL** (vision-language) para análisis de imágenes.
  - **Solo se activa cuando el usuario lo solicita explícitamente** con el comando, NO de forma automática.
  - Si no se proporciona pregunta, la IA describe lo que ve en la imagen.
  - Si se proporciona pregunta (ej: `/ia ver "¿Qué error tiene este código?"` + screenshot), responde en contexto.
- **Restricción de consumo:**
  - Límite configurable: **10 análisis de imagen por usuario por día** (default).
  - Aviso cuando quedan 2 usos: `"⚠️ Te quedan 2 análisis de imagen hoy."`
  - Reset a medianoche (hora local configurada).
- **Prioridad:** 🔴 Alta

#### RF-IA-03: Análisis de texto/código adjunto
- **Comando:** `/ia leer <archivo adjunto .txt/.py/.js/.ts/.json> [pregunta]`
- **Descripción:** El usuario sube un archivo de texto/código. La IA lee el contenido y responde.
- **Comportamiento:**
  - Extrae el texto del archivo adjunto.
  - Si no hay pregunta → code review automático.
  - Si hay pregunta → responde en contexto del archivo.
  - **Solo se activa bajo demanda**, no procesa archivos automáticamente.
- **Formatos soportados:** `.txt`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`, `.md`, `.css`, `.html`, `.sql`
- **Límite de tamaño:** Máximo 50KB por archivo.
- **Límite diario:** 20 análisis por usuario por día.
- **Prioridad:** 🔴 Alta

#### RF-IA-04: Modo de conversación por hilo
- **Comando:** `/ia chat`
- **Descripción:** Abre un hilo (thread) de Discord donde la IA mantiene contexto de la conversación.
- **Comportamiento:**
  - Crea un thread automáticamente.
  - La IA recuerda los últimos 10 mensajes del hilo como contexto.
  - El hilo se archiva automáticamente después de 30 min sin actividad.
- **Prioridad:** 🟡 Media

#### RF-IA-05: Code review
- **Comando:** `/ia review`
- **Descripción:** El usuario pega código o adjunta archivo. La IA analiza calidad, bugs potenciales y sugiere mejoras.
- **Respuesta en embed:** Con secciones: Resumen, Problemas, Sugerencias, Puntuación (1-10).
- **Prioridad:** 🟡 Media

#### RF-IA-06: Generación de documentación
- **Comando:** `/ia docs <código>`
- **Descripción:** Genera docstrings/JSDoc/comentarios para el código proporcionado.
- **Prioridad:** 🟢 Baja

#### RF-IA-07: Dashboard de uso de IA
- **Comando:** `/ia stats`
- **Descripción:** Muestra estadísticas de uso: consultas hoy, imágenes analizadas, archivos leídos.
- **Solo visible para:** Admins y el propio usuario.
- **Prioridad:** 🟡 Media

#### RF-IA-08: System prompt contextualizado
- **Descripción:** La IA tiene un prompt de sistema específico de la empresa:
  ```
  Eres el asistente IA de [NombreEmpresa], una empresa de desarrollo
  de software enfocada en apps de gestión.
  Tu rol es ayudar al equipo con:
  - Dudas técnicas de programación
  - Revisión de código
  - Sugerencias de arquitectura
  - Documentación
  Responde de forma concisa y profesional.
  Contexto: El equipo usa React, Node.js, Python, Supabase.
  ```
- **Prioridad:** 🔴 Alta

---

### 3.2 🎵 Módulo de Música (`cogs/music.py`)

#### RF-MU-01: Reproducción básica
- **Comando:** `/play <búsqueda o URL>`
- **Descripción:** Busca y reproduce audio de YouTube.
- **Estado:** ✅ Ya implementado (mejorar)

#### RF-MU-02: Cola de reproducción
- **Comandos:**
  - `/queue` | `/cola` — Ver lista de canciones en cola.
  - `/skip` — Saltar a la siguiente canción.
  - `/pause` — Pausar reproducción.
  - `/resume` — Reanudar reproducción.
  - `/queue remove <posición>` — Quitar canción de la cola.
  - `/queue clear` — Limpiar toda la cola.
  - `/nowplaying` | `/np` — Canción actual con barra de progreso.
- **Prioridad:** 🔴 Alta

#### RF-MU-03: Creación de Mix manual
- **Comando:** `/mix crear <nombre> <canción1> <canción2> ... <canciónN>`
- **Descripción:** Crea un mix (playlist personalizada) con un nombre y lista de canciones.
- **Comportamiento:**
  - Guarda el mix en la base de datos asociado al usuario.
  - Máximo 30 canciones por mix.
  - Máximo 10 mixes por usuario.
- **Comandos adicionales:**
  - `/mix reproducir <nombre>` — Reproduce el mix completo.
  - `/mix listar` — Ver todos tus mixes.
  - `/mix eliminar <nombre>` — Eliminar un mix.
  - `/mix agregar <nombre> <canción>` — Agregar canción a un mix existente.
  - `/mix compartir <nombre>` — Comparte el mix como embed para que otros lo guarden.
- **Prioridad:** 🔴 Alta

#### RF-MU-04: Mix generado por IA 🤖🎵
- **Comando:** `/mix ia <descripción>`
- **Descripción:** La IA genera una playlist basada en la descripción del usuario.
- **Ejemplos de uso:**
  ```
  /mix ia "música para programar concentrado, lo-fi y chill"
  /mix ia "rock alternativo de los 2000s para un viernes de deploy"
  /mix ia "música motivacional para sprint final"
  /mix ia "jazz suave para pair programming nocturno"
  ```
- **Comportamiento:**
  1. La IA recibe la descripción y genera una lista de 8-12 canciones (artista + título).
  2. El bot muestra la playlist sugerida en un embed con botones:
     - ▶️ **Reproducir ahora** — Busca cada canción en YouTube y las encola.
     - 💾 **Guardar como mix** — Guarda la playlist en la DB del usuario.
     - 🔄 **Regenerar** — Pide a la IA otra selección.
  3. La búsqueda en YouTube es lazy (solo cuando se reproduce cada canción).
- **Restricción:** Máximo 5 generaciones por usuario por día.
- **Prioridad:** 🔴 Alta

#### RF-MU-05: Modo radio
- **Comando:** `/radio <género>`
- **Descripción:** Reproducción continua. Cuando termina una canción, la IA sugiere la siguiente.
- **Géneros:** `lofi`, `rock`, `jazz`, `electro`, `chill`, `motivacional`
- **Prioridad:** 🟢 Baja (futuro)

---

### 3.3 🏢 Módulo de Roles y Equipo (`cogs/roles.py`)

#### RF-RO-01: Auto-asignación de roles
- **Comando:** `/rol menu`
- **Descripción:** Embed interactivo con botones/select menu para elegir rol en la empresa.
- **Roles disponibles:**
  - 🎨 Frontend Developer
  - ⚙️ Backend Developer
  - 📱 Mobile Developer
  - 🎯 Project Manager
  - 🧪 QA / Tester
  - 🎨 UI/UX Designer
  - 📚 Pasante / Aprendiz
- **Restricción:** Máximo 2 roles de desarrollo por usuario.
- **Prioridad:** 🔴 Alta

#### RF-RO-02: Vista del equipo
- **Comando:** `/equipo`
- **Descripción:** Embed con la distribución actual del equipo por rol.
- **Prioridad:** 🔴 Alta

#### RF-RO-03: Gestión de roles (admin)
- **Comando:** `/rol asignar @user <rol>` | `/rol quitar @user <rol>`
- **Restricción:** Solo Admins y Fundadores.
- **Prioridad:** 🔴 Alta

---

### 3.4 📋 Módulo de Tareas/Tickets (`cogs/tareas.py`)

#### RF-TA-01: Crear tarea
- **Comando:** `/tarea crear <título> [asignado] [prioridad] [fecha_límite]`
- **Prioridades:** `baja`, `media`, `alta`, `crítica`
- **Estados:** `pendiente` → `en-progreso` → `revisión` → `completada`
- **Prioridad:** 🔴 Alta

#### RF-TA-02: Listar tareas
- **Comando:** `/tareas [filtro]`
- **Filtros:** `pendientes`, `mias`, `equipo`, `urgentes`, `vencidas`
- **Prioridad:** 🔴 Alta

#### RF-TA-03: Actualizar estado
- **Comando:** `/tarea estado <ID> <nuevo_estado>`
- **Notificación:** Cuando cambia a `revisión`, notifica al PM.
- **Prioridad:** 🔴 Alta

#### RF-TA-04: Mis tareas
- **Comando:** `/mis-tareas`
- **Descripción:** Vista rápida de tareas asignadas al usuario, ordenadas por prioridad.
- **Prioridad:** 🔴 Alta

#### RF-TA-05: Kanban visual
- **Comando:** `/tablero`
- **Descripción:** Embed tipo Kanban: Pendiente | En Progreso | Revisión | Done.
- **Prioridad:** 🟡 Media

---

### 3.5 🌅 Módulo de Standups Diarios (`cogs/standup.py`)

#### RF-ST-01: Standup diario
- **Comando:** `/standup`
- **Descripción:** Abre un modal (formulario) con 3 campos:
  1. ¿Qué hiciste ayer?
  2. ¿Qué harás hoy?
  3. ¿Tienes algún bloqueo?
- **Prioridad:** 🟡 Media

#### RF-ST-02: Recordatorio automático
- **Descripción:** El bot envía un recordatorio a las 9:00 AM (configurable) en `#standups`.
  ```
  🌅 ¡Buenos días, equipo! Hora del standup.
  Usa /standup para reportar tu progreso.
  ```
- **Notifica si alguien no reportó** al final del día.
- **Prioridad:** 🟡 Media

#### RF-ST-03: Resumen semanal de standups
- **Comando:** `/standup resumen [semana]`
- **Descripción:** Resumen consolidado de todos los standups de la semana.
- **Prioridad:** 🟢 Baja

---

### 3.6 ⏰ Módulo de Recordatorios (`cogs/recordatorios.py`)

#### RF-RE-01: Recordatorio personal
- **Comando:** `/recordar <mensaje> <tiempo>`
- **Formatos de tiempo:** `30m`, `2h`, `1d`, `lunes 15:00`
- **Prioridad:** 🟡 Media

#### RF-RE-02: Deadline de proyecto
- **Comando:** `/deadline <nombre> <fecha>`
- **Descripción:** Deadline visible para todo el equipo. Notifica 24h y 1h antes.
- **Prioridad:** 🟡 Media

---

### 3.7 📊 Módulo de Reportes (`cogs/reportes.py`)

#### RF-RP-01: Reporte semanal automático
- **Trigger:** Cada viernes a las 18:00 (configurable).
- **Contenido:**
  ```
  📊 Reporte Semanal — Semana 17

  Tareas completadas:  12 ✅
  Tareas pendientes:    5 🔸
  Tareas bloqueadas:    1 🔴

  🏆 MVP de la semana: @Carlos (5 tareas)
  📌 Próximo deadline: Beta v1.0 (20 mayo)
  ```
- **Prioridad:** 🟢 Baja

#### RF-RP-02: Reporte bajo demanda
- **Comando:** `/reporte [semanal|mensual]`
- **Restricción:** Solo PMs y Admins.
- **Prioridad:** 🟢 Baja

---

### 3.8 📶 Módulo de Monitoreo (`cogs/monitor.py`)

#### RF-MO-01: Status del sistema
- **Comando:** `/status`
- **Info:** Latencia, CPU, RAM, uptime real del bot.
- **Estado:** ✅ Ya implementado (mejorar con uptime real)

#### RF-MO-02: Logs de actividad
- **Descripción:** Registra en `#logs`: roles asignados, tareas creadas/completadas, errores.
- **Prioridad:** 🟡 Media

---

### 3.9 👋 Módulo de Bienvenida (`cogs/bienvenida.py`)

#### RF-BI-01: Embed de bienvenida
- **Trigger:** `on_member_join`
- **Estado:** ✅ Ya implementado

#### RF-BI-02: Onboarding completo
- **Descripción:** Después de la bienvenida, enviar DM con:
  - Link a canales importantes.
  - Instrucción para elegir su rol con `/rol menu`.
  - Reglas del servidor.
- **Prioridad:** 🟡 Media

---

## 4. Requisitos No Funcionales

| ID     | Categoría      | Requisito                                                               |
| ------ | -------------- | ----------------------------------------------------------------------- |
| RNF-01 | Rendimiento    | Respuesta a comandos < 3s (excluyendo IA/YouTube)                       |
| RNF-02 | Rendimiento    | Timeout de IA: 30s. Timeout de YouTube: 20s. Feedback con `ctx.defer()` |
| RNF-03 | Disponibilidad | Bot online 24/7 con reconexión automática                               |
| RNF-04 | Seguridad      | Tokens NUNCA en código fuente. `.gitignore` obligatorio                 |
| RNF-05 | Seguridad      | Permisos basados en roles de Discord para cada comando                  |
| RNF-06 | Seguridad      | Rate limiting por usuario para comandos costosos                        |
| RNF-07 | Mantenibilidad | Arquitectura modular con cogs independientes                            |
| RNF-08 | Mantenibilidad | Código documentado con docstrings                                       |
| RNF-09 | Mantenibilidad | Logging centralizado (archivo + consola)                                |
| RNF-10 | Mantenibilidad | Base de datos async (aiosqlite)                                         |
| RNF-11 | Escalabilidad  | Soportar hasta 50 usuarios concurrentes                                 |
| RNF-12 | Escalabilidad  | DB debe manejar hasta 10,000 tareas sin degradación                     |
| RNF-13 | Costos API     | IA texto: sin límite hard, pero logging de uso                          |
| RNF-14 | Costos API     | IA imagen: máx 10/usuario/día (configurable)                            |
| RNF-15 | Costos API     | IA archivos: máx 20/usuario/día                                         |
| RNF-16 | Costos API     | IA mix gen: máx 5/usuario/día                                           |

---

## 5. Modelo de Datos

```sql
-- Configuración del servidor
CREATE TABLE guild_config (
    guild_id INTEGER PRIMARY KEY,
    welcome_channel_id INTEGER,
    standup_channel_id INTEGER,
    logs_channel_id INTEGER,
    prefix TEXT DEFAULT '!',
    timezone TEXT DEFAULT 'America/Lima',
    standup_time TEXT DEFAULT '09:00',
    report_day TEXT DEFAULT 'friday'
);

-- Tareas / Tickets
CREATE TABLE tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    asignado_a INTEGER,
    creado_por INTEGER NOT NULL,
    proyecto TEXT,
    estado TEXT DEFAULT 'pendiente',
    prioridad TEXT DEFAULT 'media',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_limite TIMESTAMP,
    fecha_completada TIMESTAMP
);

-- Standups
CREATE TABLE standups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    ayer TEXT NOT NULL,
    hoy TEXT NOT NULL,
    bloqueos TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mixes de música
CREATE TABLE mixes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id, nombre)
);

CREATE TABLE mix_canciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mix_id INTEGER NOT NULL,
    artista TEXT,
    titulo TEXT NOT NULL,
    posicion INTEGER NOT NULL,
    FOREIGN KEY (mix_id) REFERENCES mixes(id) ON DELETE CASCADE
);

-- Recordatorios
CREATE TABLE recordatorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    mensaje TEXT NOT NULL,
    fecha_recordatorio TIMESTAMP NOT NULL,
    completado BOOLEAN DEFAULT FALSE
);

-- Deadlines de proyecto
CREATE TABLE deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    creado_por INTEGER NOT NULL,
    notificado_24h BOOLEAN DEFAULT FALSE,
    notificado_1h BOOLEAN DEFAULT FALSE
);

-- Control de uso de IA
CREATE TABLE ia_uso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,  -- 'texto', 'imagen', 'archivo', 'mix'
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_usados INTEGER DEFAULT 0
);
```

---

## 6. Stack Tecnológico

| Componente        | Tecnología          | Versión      |
| ----------------- | ------------------- | ------------ |
| Runtime           | Python              | 3.11+        |
| Framework Bot     | discord.py          | 2.4+         |
| IA (texto)        | Qwen via OpenAI SDK | qwen-plus    |
| IA (visión)       | Qwen-VL             | qwen-vl-plus |
| Base de Datos     | SQLite (aiosqlite)  | 3.x          |
| Audio YouTube     | yt-dlp + FFmpeg     | latest       |
| Audio Discord     | PyNaCl              | 1.5+         |
| Monitoreo         | psutil              | 5.9+         |
| Variables Entorno | python-dotenv       | 1.0+         |

---

## 7. Dependencias (`requirements.txt`)

```
discord.py==2.4.0
python-dotenv==1.0.1
openai==1.52.0
psutil==5.9.8
yt-dlp==2024.12.23
PyNaCl==1.5.0
aiosqlite==0.20.0
```

---

## 8. Roadmap de Implementación

### Fase 1 — Fundamentos (Semana 1)
- [ ] Seguridad: `.gitignore`, regenerar tokens
- [ ] `config.py` centralizado
- [ ] `utils/embeds.py` — Embeds corporativos
- [ ] `utils/checks.py` — Sistema de permisos
- [ ] Base de datos async (aiosqlite) con todas las tablas
- [ ] Logging profesional

### Fase 2 — Gestión de Equipo (Semana 2)
- [ ] `cogs/roles.py` — Auto-roles interactivos
- [ ] Mejorar `cogs/bienvenida.py` — Onboarding + DM
- [ ] `/equipo` — Vista del equipo

### Fase 3 — IA Profesional (Semana 3)
- [ ] IA con visión de imágenes (Qwen-VL)
- [ ] IA lectura de archivos/código
- [ ] IA hilos con contexto
- [ ] System prompt de empresa
- [ ] Dashboard de uso `/ia stats`

### Fase 4 — Música Profesional (Semana 4)
- [ ] Cola de reproducción completa
- [ ] Mixes manuales (CRUD)
- [ ] Mix generado por IA con botones interactivos

### Fase 5 — Productividad (Semana 5)
- [ ] Sistema de tareas/tickets
- [ ] Daily standups automatizados
- [ ] Recordatorios y deadlines

### Fase 6 — Reportes y Pulido (Semana 6)
- [ ] Reportes semanales automáticos
- [ ] Logs de actividad
- [ ] Tests unitarios
- [ ] Documentación README.md
- [ ] Deploy en VPS / Docker

---

## 9. Criterios de Aceptación Globales

- [ ] Todos los comandos usan Slash Commands (`hybrid_command`)
- [ ] Todos los comandos costosos usan `ctx.defer()` para feedback visual
- [ ] Toda respuesta del bot es un Embed estilizado, NO texto plano
- [ ] Cada cog puede cargarse y descargarse independientemente
- [ ] Errores se loggean en archivo y se muestran al usuario de forma amigable
- [ ] Rate limits son por usuario y configurables
- [ ] La base de datos usa operaciones async (aiosqlite)
- [ ] El bot funciona en múltiples servidores simultáneamente

---

## 10. Ideas Futuras (Post v2.0)

| Idea                 | Descripción                                         |
| -------------------- | --------------------------------------------------- |
| GitHub Integration   | Notificaciones de PRs, issues y commits en Discord  |
| Time Tracking        | `/clock-in` y `/clock-out` para registrar horas     |
| Knowledge Base       | `/docs buscar [tema]` — busca en docs internos      |
| Deploy Notifications | El bot anuncia cuando sale una nueva versión        |
| Code Snippets        | Guardar y compartir snippets con `/snippet guardar` |
| Modo Radio           | Reproducción continua con IA sugiriendo canciones   |