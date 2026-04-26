"""
Configuración centralizada del bot YoRobot.
Todas las constantes y settings se definen aquí.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Discord ────────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = "!"

# ─── IA (Qwen) ──────────────────────────────────────────────
API_QWEN = os.getenv("API_QWEN")
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL_TEXT = "qwen-plus"
QWEN_MODEL_VISION = "qwen-vl-plus"

# System prompt de la empresa
COMPANY_NAME = "YoRobot Dev Team"
SYSTEM_PROMPT = f"""Eres el asistente IA de {COMPANY_NAME}, una empresa de desarrollo de software enfocada en apps de gestión y sitios web.

Tu rol es ayudar al equipo con:
- Dudas técnicas de programación
- Revisión de código (code review)
- Sugerencias de arquitectura de software
- Generación de documentación
- Resolución de bugs y debugging

Responde de forma concisa, profesional y en español.
Contexto técnico: El equipo usa React, Next.js, Node.js, Python, Supabase, PostgreSQL.
Cuando respondas sobre código, usa bloques de código con el lenguaje apropiado.
"""

# ─── Límites de uso de IA (por usuario por día) ─────────────
IA_LIMIT_TEXT = 50          # Consultas de texto
IA_LIMIT_IMAGE = 10         # Análisis de imágenes
IA_LIMIT_FILE = 20          # Análisis de archivos
IA_LIMIT_MIX = 100          # Generaciones de mix por IA (Aumentado para pruebas)
IA_WARNING_THRESHOLD = 2    # Avisar cuando quedan N usos

# ─── Música ──────────────────────────────────────────────────
MAX_SONGS_PER_MIX = 30
MAX_MIXES_PER_USER = 10
MIX_IA_SONGS_COUNT = 10     # Canciones a generar por mix IA
YOUTUBE_TIMEOUT = 20         # Segundos de timeout para yt-dlp

# ─── Tareas ──────────────────────────────────────────────────
TASK_STATES = ["pendiente", "en-progreso", "revisión", "completada"]
TASK_PRIORITIES = ["baja", "media", "alta", "crítica"]

# ─── Base de Datos ───────────────────────────────────────────
DB_PATH = "bot_database.db"

# ─── Timezone ────────────────────────────────────────────────
DEFAULT_TIMEZONE = "America/Lima"
STANDUP_TIME = "09:00"
REPORT_DAY = "friday"

# ─── Roles del equipo ───────────────────────────────────────
TEAM_ROLES = {
    "frontend":  {"name": "Frontend Dev",   "emoji": "🎨", "color": 0x61DAFB},
    "backend":   {"name": "Backend Dev",    "emoji": "⚙️", "color": 0x68A063},
    "mobile":    {"name": "Mobile Dev",     "emoji": "📱", "color": 0x3DDC84},
    "pm":        {"name": "Project Manager","emoji": "🎯", "color": 0xF5A623},
    "qa":        {"name": "QA / Tester",    "emoji": "🧪", "color": 0x9B59B6},
    "uiux":      {"name": "UI/UX Designer", "emoji": "🎨", "color": 0xE91E63},
    "pasante":   {"name": "Pasante",        "emoji": "📚", "color": 0x95A5A6},
}
MAX_DEV_ROLES = 2

# ─── Archivos permitidos para IA ─────────────────────────────
ALLOWED_FILE_EXTENSIONS = [
    ".txt", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".md", ".css", ".html", ".sql",
    ".java", ".cpp", ".c", ".go", ".rs", ".rb",
]
MAX_FILE_SIZE_KB = 50
