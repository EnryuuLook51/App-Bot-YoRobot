"""
Módulo de Recordatorios — Reminders personales y deadlines de proyecto.
RF-RE-01 a RF-RE-02
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import re
from datetime import datetime, timedelta
from utils.embeds import success_embed, info_embed, error_embed, set_author
from utils.constants import Colors

logger = logging.getLogger("cog.recordatorios")

def parse_time(time_str: str) -> timedelta | None:
    """Parsea '30m', '2h', '1d' a timedelta."""
    match = re.match(r"(\d+)\s*(m|min|h|hora|horas|d|dia|dias)$", time_str.lower().strip())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if unit in ("m", "min"):
        return timedelta(minutes=value)
    elif unit in ("h", "hora", "horas"):
        return timedelta(hours=value)
    elif unit in ("d", "dia", "dias"):
        return timedelta(days=value)
    return None

class Recordatorios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @commands.hybrid_command(name="recordar", description="Crea un recordatorio personal")
    @app_commands.describe(mensaje="Qué recordar", tiempo="Cuándo (ej: 30m, 2h, 1d)")
    async def recordar(self, ctx, tiempo: str, *, mensaje: str):
        delta = parse_time(tiempo)
        if not delta:
            return await ctx.send(embed=error_embed("Formato inválido",
                "Usa: `30m`, `2h`, `1d`\nEjemplo: `/recordar 2h Entregar mockups`"))

        fecha = datetime.utcnow() + delta
        await self.bot.db.crear_recordatorio(ctx.guild.id, ctx.author.id, ctx.channel.id, mensaje, fecha.isoformat())
        embed = success_embed("Recordatorio creado",
            f"⏰ Te recordaré en **{tiempo}**:\n\n📝 *{mensaje}*")
        embed.add_field(name="🕒 Hora estimada", value=f"<t:{int(fecha.timestamp())}:R>", inline=False)
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deadline", description="Crea un deadline de proyecto visible para el equipo")
    @app_commands.describe(nombre="Nombre del deadline", fecha="Fecha YYYY-MM-DD")
    async def deadline(self, ctx, fecha: str, *, nombre: str):
        try:
            deadline_date = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return await ctx.send(embed=error_embed("Formato inválido", "Usa: `YYYY-MM-DD` (ej: 2026-05-15)"))

        await self.bot.db.crear_deadline(ctx.guild.id, nombre, deadline_date.isoformat(), ctx.author.id)
        embed = success_embed("Deadline creado",
            f"📌 **{nombre}**\n📅 Fecha: **{fecha}**\n⏰ Se notificará 24h y 1h antes.")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deadlines", description="Ver deadlines activos del equipo")
    async def ver_deadlines(self, ctx):
        deadlines = await self.bot.db.obtener_deadlines_activos(ctx.guild.id)
        if not deadlines:
            return await ctx.send(embed=info_embed("Sin deadlines", "No hay deadlines activos."))

        lines = []
        for dl in deadlines:
            ts = int(datetime.fromisoformat(dl["fecha"]).timestamp())
            lines.append(f"📌 **{dl['nombre']}** — <t:{ts}:D> (<t:{ts}:R>)")

        embed = info_embed("Deadlines del equipo", "\n".join(lines))
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @tasks.loop(minutes=5)
    async def check_reminders(self):
        """Revisa y envía recordatorios pendientes."""
        try:
            reminders = await self.bot.db.obtener_recordatorios_pendientes()
            for r in reminders:
                try:
                    channel = self.bot.get_channel(r["channel_id"])
                    if channel:
                        user = self.bot.get_user(r["user_id"])
                        mention = user.mention if user else f"<@{r['user_id']}>"
                        embed = discord.Embed(
                            title="⏰ ¡Recordatorio!",
                            description=f"{mention}\n\n📝 {r['mensaje']}",
                            color=Colors.WARNING, timestamp=datetime.utcnow())
                        await channel.send(content=mention, embed=embed)
                    await self.bot.db.completar_recordatorio(r["id"])
                except Exception as e:
                    logger.error(f"Error enviando recordatorio {r['id']}: {e}")
        except Exception as e:
            logger.error(f"Error check_reminders: {e}")

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Recordatorios(bot))
