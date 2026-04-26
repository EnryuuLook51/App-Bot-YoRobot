"""
Constantes visuales compartidas: colores, emojis, mensajes.
"""

# ─── Colores de Embeds ───────────────────────────────────────
class Colors:
    BRAND    = 0x5865F2   # Azul Discord / corporativo
    SUCCESS  = 0x57F287   # Verde
    ERROR    = 0xED4245   # Rojo
    WARNING  = 0xFEE75C   # Amarillo
    INFO     = 0x5865F2   # Azul
    MUSIC    = 0xE91E9D   # Rosa/Magenta
    AI       = 0x00D4AA   # Verde turquesa
    TASK     = 0xF5A623   # Naranja
    STANDUP  = 0xFFD700   # Dorado

# ─── Emojis ──────────────────────────────────────────────────
class Emojis:
    # Estados de tareas
    PENDING     = "🔸"
    IN_PROGRESS = "🔵"
    IN_REVIEW   = "🟡"
    COMPLETED   = "✅"
    BLOCKED     = "🔴"

    # Prioridades
    PRIORITY_LOW      = "🟢"
    PRIORITY_MEDIUM   = "🟡"
    PRIORITY_HIGH     = "🟠"
    PRIORITY_CRITICAL = "🔴"

    # General
    SUCCESS = "✅"
    ERROR   = "❌"
    WARNING = "⚠️"
    INFO    = "📋"
    MUSIC   = "🎵"
    AI      = "🤖"
    CLOCK   = "🕒"
    CHART   = "📊"
    TEAM    = "👥"
    FIRE    = "🔥"
    TROPHY  = "🏆"
    PIN     = "📌"

# ─── Mapeos de estado/prioridad a emoji ──────────────────────
TASK_STATE_EMOJIS = {
    "pendiente":    Emojis.PENDING,
    "en-progreso":  Emojis.IN_PROGRESS,
    "revisión":     Emojis.IN_REVIEW,
    "completada":   Emojis.COMPLETED,
}

PRIORITY_EMOJIS = {
    "baja":     Emojis.PRIORITY_LOW,
    "media":    Emojis.PRIORITY_MEDIUM,
    "alta":     Emojis.PRIORITY_HIGH,
    "crítica":  Emojis.PRIORITY_CRITICAL,
}
