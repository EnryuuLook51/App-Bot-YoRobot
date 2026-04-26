"""
YoRobot — Bot de Discord para gestión de equipo de desarrollo.
Versión 2.0
"""
import discord
from discord.ext import commands
import logging
import os

from config import DISCORD_TOKEN, BOT_PREFIX
from database import Database

# ─── Logging Profesional ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("YoRobot")

# ─── Intents ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class YoRobot(commands.Bot):
    """Clase principal del bot."""

    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=intents)
        self.db = Database()

    async def setup_hook(self):
        """Carga módulos y inicializa la base de datos."""
        # Inicializar DB
        await self.db.init()
        logger.info("📦 Base de datos inicializada.")

        # Cargar todos los cogs
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"⚙️  Módulo cargado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Error cargando {filename}: {e}")

    async def on_ready(self):
        logger.info("─" * 50)
        logger.info(f"✅ YoRobot v2.0 en línea | {self.user}")
        logger.info(f"📡 Servidores: {len(self.guilds)}")
        logger.info(f"👥 Usuarios: {len(self.users)}")
        logger.info("─" * 50)

        # Establecer status del bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="al equipo 🚀 | /help"
        )
        await self.change_presence(activity=activity)


# ─── Instanciar bot ──────────────────────────────────────────
bot = YoRobot()


# ─── Comando de sincronización (solo owner) ──────────────────
@bot.command()
@commands.is_owner()
async def sync(ctx, modo: str = None):
    """Sincroniza los slash commands con Discord.
    !sync        → Sincroniza al servidor actual (INSTANTÁNEO)
    !sync global → Sincroniza globalmente (tarda hasta 1 hora)
    """
    if modo == "global":
        fmt = await bot.tree.sync()
        await ctx.send(f"✅ Sincronización **global**: {len(fmt)} comandos. (puede tardar hasta 1h)")
    else:
        # Sync al guild actual = INSTANTÁNEO
        bot.tree.copy_global_to(guild=ctx.guild)
        fmt = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Sincronización **local**: {len(fmt)} comandos registrados en este servidor. ¡Ya disponibles!")


# ─── Comando de recarga de cogs (solo owner) ─────────────────
@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str = None):
    """Recarga uno o todos los cogs en caliente."""
    if cog:
        try:
            await bot.reload_extension(f"cogs.{cog}")
            await ctx.send(f"🔄 Módulo `{cog}` recargado.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    else:
        reloaded = []
        for ext in list(bot.extensions):
            try:
                await bot.reload_extension(ext)
                reloaded.append(ext.split(".")[-1])
            except Exception as e:
                await ctx.send(f"❌ Error en {ext}: {e}")
        await ctx.send(f"🔄 Módulos recargados: {', '.join(reloaded)}")


# ─── Manejo global de errores ────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.NotOwner):
        await ctx.send("❌ Este comando solo lo puede usar el dueño del bot.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argumento inválido: {error}")
    else:
        logger.error(f"Error no manejado: {error}", exc_info=True)
        await ctx.send(f"❌ Ocurrió un error inesperado. Revisa los logs.")


# ─── Ejecutar ────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.critical("❌ DISCORD_TOKEN no encontrado en .env")
        exit(1)
    bot.run(DISCORD_TOKEN)