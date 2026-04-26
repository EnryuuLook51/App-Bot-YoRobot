"""
Gestor de base de datos async con aiosqlite.
Maneja todas las tablas del bot de forma no-bloqueante.
"""
import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger("database")


class Database:
    """Gestiona la conexión y operaciones con SQLite de forma async."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init(self):
        """Inicializa todas las tablas de la base de datos."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                -- Configuración del servidor
                CREATE TABLE IF NOT EXISTS guild_config (
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
                CREATE TABLE IF NOT EXISTS tareas (
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
                CREATE TABLE IF NOT EXISTS standups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    ayer TEXT NOT NULL,
                    hoy TEXT NOT NULL,
                    bloqueos TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Mixes de música
                CREATE TABLE IF NOT EXISTS mixes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id, nombre)
                );

                CREATE TABLE IF NOT EXISTS mix_canciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mix_id INTEGER NOT NULL,
                    artista TEXT,
                    titulo TEXT NOT NULL,
                    posicion INTEGER NOT NULL,
                    FOREIGN KEY (mix_id) REFERENCES mixes(id) ON DELETE CASCADE
                );

                -- Recordatorios
                CREATE TABLE IF NOT EXISTS recordatorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    mensaje TEXT NOT NULL,
                    fecha_recordatorio TIMESTAMP NOT NULL,
                    completado BOOLEAN DEFAULT 0
                );

                -- Deadlines de proyecto
                CREATE TABLE IF NOT EXISTS deadlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    fecha TIMESTAMP NOT NULL,
                    creado_por INTEGER NOT NULL,
                    notificado_24h BOOLEAN DEFAULT 0,
                    notificado_1h BOOLEAN DEFAULT 0
                );

                -- Control de uso de IA
                CREATE TABLE IF NOT EXISTS ia_uso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tokens_usados INTEGER DEFAULT 0
                );
            """)
            await db.commit()
            logger.info("✅ Base de datos inicializada correctamente.")

    # ─── Helpers genéricos ───────────────────────────────────

    async def execute(self, query: str, params: tuple = ()):
        """Ejecuta una query sin retorno (INSERT, UPDATE, DELETE)."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid

    async def fetchone(self, query: str, params: tuple = ()):
        """Retorna una sola fila."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()):
        """Retorna todas las filas."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            return await cursor.fetchall()

    # ─── Tareas ──────────────────────────────────────────────

    async def crear_tarea(self, guild_id, titulo, creado_por, asignado_a=None,
                          descripcion=None, proyecto=None, prioridad="media", fecha_limite=None):
        """Crea una nueva tarea y retorna su ID."""
        return await self.execute(
            """INSERT INTO tareas (guild_id, titulo, descripcion, asignado_a, creado_por, proyecto, prioridad, fecha_limite)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (guild_id, titulo, descripcion, asignado_a, creado_por, proyecto, prioridad, fecha_limite)
        )

    async def obtener_tareas(self, guild_id, filtro=None, user_id=None):
        """Obtiene tareas con filtro opcional."""
        query = "SELECT * FROM tareas WHERE guild_id = ?"
        params = [guild_id]

        if filtro == "mias" and user_id:
            query += " AND asignado_a = ?"
            params.append(user_id)
        elif filtro == "pendientes":
            query += " AND estado = 'pendiente'"
        elif filtro == "en-progreso":
            query += " AND estado = 'en-progreso'"
        elif filtro == "completadas":
            query += " AND estado = 'completada'"
        elif filtro == "urgentes":
            query += " AND prioridad IN ('alta', 'crítica') AND estado != 'completada'"
        elif filtro == "vencidas":
            query += " AND fecha_limite < CURRENT_TIMESTAMP AND estado != 'completada'"

        query += " ORDER BY CASE prioridad WHEN 'crítica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 WHEN 'baja' THEN 4 END"
        return await self.fetchall(query, tuple(params))

    async def actualizar_estado_tarea(self, tarea_id, nuevo_estado):
        """Actualiza el estado de una tarea."""
        extra = ", fecha_completada = CURRENT_TIMESTAMP" if nuevo_estado == "completada" else ""
        await self.execute(
            f"UPDATE tareas SET estado = ?{extra} WHERE id = ?",
            (nuevo_estado, tarea_id)
        )

    async def obtener_tarea(self, tarea_id):
        """Obtiene una tarea por ID."""
        return await self.fetchone("SELECT * FROM tareas WHERE id = ?", (tarea_id,))

    # ─── Standups ────────────────────────────────────────────

    async def guardar_standup(self, guild_id, user_id, ayer, hoy, bloqueos=None):
        """Guarda un standup diario."""
        return await self.execute(
            "INSERT INTO standups (guild_id, user_id, ayer, hoy, bloqueos) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, ayer, hoy, bloqueos)
        )

    async def obtener_standups_hoy(self, guild_id):
        """Obtiene los standups de hoy."""
        return await self.fetchall(
            "SELECT * FROM standups WHERE guild_id = ? AND DATE(fecha) = DATE('now') ORDER BY fecha",
            (guild_id,)
        )

    async def obtener_standups_semana(self, guild_id):
        """Obtiene los standups de la semana actual."""
        return await self.fetchall(
            """SELECT * FROM standups WHERE guild_id = ?
               AND fecha >= DATE('now', 'weekday 0', '-7 days')
               ORDER BY fecha""",
            (guild_id,)
        )

    # ─── Mixes ───────────────────────────────────────────────

    async def crear_mix(self, guild_id, user_id, nombre):
        """Crea un mix vacío y retorna su ID."""
        return await self.execute(
            "INSERT INTO mixes (guild_id, user_id, nombre) VALUES (?, ?, ?)",
            (guild_id, user_id, nombre)
        )

    async def agregar_cancion_mix(self, mix_id, titulo, artista=None, posicion=None):
        """Agrega una canción al mix."""
        if posicion is None:
            row = await self.fetchone(
                "SELECT COALESCE(MAX(posicion), 0) + 1 as next_pos FROM mix_canciones WHERE mix_id = ?",
                (mix_id,)
            )
            posicion = row["next_pos"] if row else 1
        return await self.execute(
            "INSERT INTO mix_canciones (mix_id, artista, titulo, posicion) VALUES (?, ?, ?, ?)",
            (mix_id, artista, titulo, posicion)
        )

    async def obtener_mixes(self, guild_id, user_id):
        """Obtiene los mixes de un usuario."""
        return await self.fetchall(
            "SELECT * FROM mixes WHERE guild_id = ? AND user_id = ? ORDER BY nombre",
            (guild_id, user_id)
        )

    async def obtener_canciones_mix(self, mix_id):
        """Obtiene las canciones de un mix."""
        return await self.fetchall(
            "SELECT * FROM mix_canciones WHERE mix_id = ? ORDER BY posicion",
            (mix_id,)
        )

    async def obtener_mix_por_nombre(self, guild_id, user_id, nombre):
        """Obtiene un mix por nombre."""
        return await self.fetchone(
            "SELECT * FROM mixes WHERE guild_id = ? AND user_id = ? AND nombre = ?",
            (guild_id, user_id, nombre)
        )

    async def eliminar_mix(self, mix_id):
        """Elimina un mix y sus canciones (CASCADE)."""
        await self.execute("DELETE FROM mixes WHERE id = ?", (mix_id,))

    async def contar_mixes(self, guild_id, user_id):
        """Cuenta los mixes de un usuario."""
        row = await self.fetchone(
            "SELECT COUNT(*) as count FROM mixes WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        return row["count"] if row else 0

    # ─── Recordatorios ───────────────────────────────────────

    async def crear_recordatorio(self, guild_id, user_id, channel_id, mensaje, fecha_recordatorio):
        """Crea un recordatorio."""
        return await self.execute(
            """INSERT INTO recordatorios (guild_id, user_id, channel_id, mensaje, fecha_recordatorio)
               VALUES (?, ?, ?, ?, ?)""",
            (guild_id, user_id, channel_id, mensaje, fecha_recordatorio)
        )

    async def obtener_recordatorios_pendientes(self):
        """Obtiene recordatorios que ya deben dispararse."""
        return await self.fetchall(
            "SELECT * FROM recordatorios WHERE completado = 0 AND fecha_recordatorio <= CURRENT_TIMESTAMP"
        )

    async def completar_recordatorio(self, recordatorio_id):
        """Marca un recordatorio como completado."""
        await self.execute(
            "UPDATE recordatorios SET completado = 1 WHERE id = ?",
            (recordatorio_id,)
        )

    # ─── Deadlines ───────────────────────────────────────────

    async def crear_deadline(self, guild_id, nombre, fecha, creado_por):
        """Crea un deadline de proyecto."""
        return await self.execute(
            "INSERT INTO deadlines (guild_id, nombre, fecha, creado_por) VALUES (?, ?, ?, ?)",
            (guild_id, nombre, fecha, creado_por)
        )

    async def obtener_deadlines_activos(self, guild_id):
        """Obtiene deadlines no vencidos."""
        return await self.fetchall(
            "SELECT * FROM deadlines WHERE guild_id = ? AND fecha > CURRENT_TIMESTAMP ORDER BY fecha",
            (guild_id,)
        )

    # ─── Control de uso IA ───────────────────────────────────

    async def registrar_uso_ia(self, guild_id, user_id, tipo, tokens=0):
        """Registra un uso de la IA."""
        await self.execute(
            "INSERT INTO ia_uso (guild_id, user_id, tipo, tokens_usados) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, tipo, tokens)
        )

    async def contar_uso_ia_hoy(self, user_id, tipo):
        """Cuenta los usos de IA de hoy para un usuario y tipo."""
        row = await self.fetchone(
            "SELECT COUNT(*) as count FROM ia_uso WHERE user_id = ? AND tipo = ? AND DATE(fecha) = DATE('now')",
            (user_id, tipo)
        )
        return row["count"] if row else 0

    async def obtener_stats_ia(self, user_id=None):
        """Obtiene stats de uso de IA (hoy). Si user_id es None, stats globales."""
        where = "WHERE DATE(fecha) = DATE('now')"
        params = ()
        if user_id:
            where += " AND user_id = ?"
            params = (user_id,)
        return await self.fetchall(
            f"SELECT tipo, COUNT(*) as count FROM ia_uso {where} GROUP BY tipo",
            params
        )

    # ─── Reportes ────────────────────────────────────────────

    async def obtener_stats_tareas_semana(self, guild_id):
        """Estadísticas de tareas de la semana para reportes."""
        completadas = await self.fetchone(
            """SELECT COUNT(*) as count FROM tareas WHERE guild_id = ?
               AND estado = 'completada' AND fecha_completada >= DATE('now', 'weekday 0', '-7 days')""",
            (guild_id,)
        )
        pendientes = await self.fetchone(
            "SELECT COUNT(*) as count FROM tareas WHERE guild_id = ? AND estado IN ('pendiente', 'en-progreso')",
            (guild_id,)
        )
        bloqueadas = await self.fetchone(
            "SELECT COUNT(*) as count FROM tareas WHERE guild_id = ? AND prioridad = 'crítica' AND estado != 'completada'",
            (guild_id,)
        )
        # MVP: usuario que más tareas completó esta semana
        mvp = await self.fetchone(
            """SELECT asignado_a, COUNT(*) as count FROM tareas WHERE guild_id = ?
               AND estado = 'completada' AND fecha_completada >= DATE('now', 'weekday 0', '-7 days')
               AND asignado_a IS NOT NULL
               GROUP BY asignado_a ORDER BY count DESC LIMIT 1""",
            (guild_id,)
        )
        return {
            "completadas": completadas["count"] if completadas else 0,
            "pendientes": pendientes["count"] if pendientes else 0,
            "bloqueadas": bloqueadas["count"] if bloqueadas else 0,
            "mvp_user_id": mvp["asignado_a"] if mvp else None,
            "mvp_count": mvp["count"] if mvp else 0,
        }
