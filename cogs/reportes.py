"""
Módulo de Reportes — Reportes semanales automáticos y bajo demanda.
RF-RP-01 a RF-RP-02
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
from datetime import datetime
from utils.embeds import info_embed, set_author
from utils.checks import es_pm
from utils.constants import Colors

logger = logging.getLogger("cog.reportes")

class Reportes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_report.start()

    def cog_unload(self):
        self.weekly_report.cancel()

    async def _build_report(self, guild_id: int, guild) -> discord.Embed:
        stats = await self.bot.db.obtener_stats_tareas_semana(guild_id)
        week_num = datetime.utcnow().isocalendar()[1]

        embed = discord.Embed(
            title=f"📊 Reporte Semanal — Semana {week_num}",
            color=Colors.BRAND, timestamp=datetime.utcnow())

        embed.add_field(name="✅ Completadas", value=f"**{stats['completadas']}**", inline=True)
        embed.add_field(name="🔸 Pendientes", value=f"**{stats['pendientes']}**", inline=True)
        embed.add_field(name="🔴 Críticas", value=f"**{stats['bloqueadas']}**", inline=True)

        if stats["mvp_user_id"]:
            user = self.bot.get_user(stats["mvp_user_id"])
            name = user.display_name if user else f"User #{stats['mvp_user_id']}"
            embed.add_field(name="🏆 MVP de la semana",
                value=f"**{name}** ({stats['mvp_count']} tareas completadas)", inline=False)

        # Standups de la semana
        standups = await self.bot.db.obtener_standups_semana(guild_id)
        embed.add_field(name="🌅 Standups", value=f"**{len(standups)}** reportes esta semana", inline=True)

        # Deadlines próximos
        deadlines = await self.bot.db.obtener_deadlines_activos(guild_id)
        if deadlines:
            dl = deadlines[0]
            ts = int(datetime.fromisoformat(dl["fecha"]).timestamp())
            embed.add_field(name="📌 Próximo deadline", value=f"**{dl['nombre']}** — <t:{ts}:R>", inline=True)

        embed.set_footer(text="Reporte generado automáticamente por YoRobot")
        return embed

    @commands.hybrid_command(name="reporte", description="Genera el reporte semanal del equipo")
    @es_pm()
    async def reporte(self, ctx):
        await ctx.defer()
        embed = await self._build_report(ctx.guild.id, ctx.guild)
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def weekly_report(self):
        """Envía reporte semanal automático los viernes a las 18:00."""
        now = datetime.utcnow()
        local_hour = (now.hour - 5) % 24  # UTC-5
        if now.weekday() != 4 or local_hour != 18:  # Viernes
            return
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="reportes")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")
            if channel:
                try:
                    embed = await self._build_report(guild.id, guild)
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Error reporte {guild.name}: {e}")

    @weekly_report.before_loop
    async def before_report(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reportes(bot))
