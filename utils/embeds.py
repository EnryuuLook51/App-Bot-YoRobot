"""
Fábrica de Embeds corporativos para respuestas consistentes del bot.
"""
import discord
from datetime import datetime
from utils.constants import Colors


def success_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de éxito (verde)."""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=Colors.SUCCESS,
        timestamp=datetime.utcnow()
    )
    return embed


def error_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de error (rojo)."""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=Colors.ERROR,
        timestamp=datetime.utcnow()
    )
    return embed


def warning_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de advertencia (amarillo)."""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=Colors.WARNING,
        timestamp=datetime.utcnow()
    )
    return embed


def info_embed(title: str, description: str = "") -> discord.Embed:
    """Embed informativo (azul corporativo)."""
    embed = discord.Embed(
        title=f"📋 {title}",
        description=description,
        color=Colors.INFO,
        timestamp=datetime.utcnow()
    )
    return embed


def music_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de música (rosa/magenta)."""
    embed = discord.Embed(
        title=f"🎵 {title}",
        description=description,
        color=Colors.MUSIC,
        timestamp=datetime.utcnow()
    )
    return embed


def ai_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de IA (turquesa)."""
    embed = discord.Embed(
        title=f"🤖 {title}",
        description=description,
        color=Colors.AI,
        timestamp=datetime.utcnow()
    )
    return embed


def task_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de tareas (naranja)."""
    embed = discord.Embed(
        title=f"📋 {title}",
        description=description,
        color=Colors.TASK,
        timestamp=datetime.utcnow()
    )
    return embed


def standup_embed(title: str, description: str = "") -> discord.Embed:
    """Embed de standup (dorado)."""
    embed = discord.Embed(
        title=f"🌅 {title}",
        description=description,
        color=Colors.STANDUP,
        timestamp=datetime.utcnow()
    )
    return embed


def set_author(embed: discord.Embed, ctx) -> discord.Embed:
    """Agrega info del autor al embed."""
    avatar = ctx.author.avatar.url if ctx.author.avatar else None
    embed.set_footer(
        text=f"Solicitado por {ctx.author.display_name}",
        icon_url=avatar
    )
    return embed
