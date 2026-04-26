"""
Módulo de Standups — Daily standups automatizados con modal.
RF-ST-01 a RF-ST-03
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import logging
from datetime import datetime
from utils.embeds import standup_embed, success_embed, set_author
from utils.constants import Colors

logger = logging.getLogger("cog.standup")

class StandupModal(ui.Modal, title="🌅 Standup Diario"):
    ayer = ui.TextInput(label="¿Qué hiciste ayer?", style=discord.TextStyle.paragraph, max_length=500)
    hoy = ui.TextInput(label="¿Qué harás hoy?", style=discord.TextStyle.paragraph, max_length=500)
    bloqueos = ui.TextInput(label="¿Tienes algún bloqueo?", style=discord.TextStyle.paragraph,
                            required=False, max_length=300, placeholder="Ninguno")

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await self.bot.db.guardar_standup(
            interaction.guild.id, interaction.user.id,
            self.ayer.value, self.hoy.value, self.bloqueos.value or "Ninguno"
        )
        embed = standup_embed(f"Standup — {interaction.user.display_name}")
        embed.add_field(name="📌 Ayer", value=self.ayer.value, inline=False)
        embed.add_field(name="🎯 Hoy", value=self.hoy.value, inline=False)
        embed.add_field(name="🚧 Bloqueos", value=self.bloqueos.value or "Ninguno", inline=False)
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.utcnow()
        await interaction.response.send_message(embed=embed)

class Standup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.standup_reminder.start()

    def cog_unload(self):
        self.standup_reminder.cancel()

    @commands.hybrid_command(name="standup", description="Registra tu standup diario")
    async def standup(self, ctx):
        await ctx.interaction.response.send_modal(StandupModal(self.bot))

    @commands.hybrid_command(name="standups", description="Ver standups de hoy")
    async def ver_standups(self, ctx):
        standups = await self.bot.db.obtener_standups_hoy(ctx.guild.id)
        if not standups:
            return await ctx.send(embed=standup_embed("Sin standups hoy", "Nadie ha reportado aún. Usa `/standup`."))

        embed = standup_embed(f"Standups — Hoy ({len(standups)} reportes)")
        for s in standups[:10]:
            user = self.bot.get_user(s["user_id"])
            name = user.display_name if user else f"User #{s['user_id']}"
            embed.add_field(
                name=f"👤 {name}",
                value=f"**Ayer:** {s['ayer'][:100]}\n**Hoy:** {s['hoy'][:100]}\n**Bloqueos:** {s['bloqueos'][:80] if s['bloqueos'] else 'Ninguno'}",
                inline=False
            )
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="standupresumen", description="Resumen semanal de standups")
    async def resumen_semanal(self, ctx):
        standups = await self.bot.db.obtener_standups_semana(ctx.guild.id)
        if not standups:
            return await ctx.send(embed=standup_embed("Sin datos", "No hay standups esta semana."))

        user_counts = {}
        for s in standups:
            user_counts[s["user_id"]] = user_counts.get(s["user_id"], 0) + 1

        lines = []
        for uid, count in sorted(user_counts.items(), key=lambda x: -x[1]):
            user = self.bot.get_user(uid)
            name = user.display_name if user else f"User #{uid}"
            bar = "█" * count + "░" * (5 - count)
            lines.append(f"`{bar}` **{name}** — {count}/5 días")

        embed = standup_embed("Resumen Semanal", "\n".join(lines))
        embed.set_footer(text=f"Total: {len(standups)} standups de {len(user_counts)} miembros")
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def standup_reminder(self):
        """Envía recordatorio de standup a las 9 AM."""
        now = datetime.utcnow()
        # Ajustar a hora local (UTC-5 para Peru/Colombia)
        local_hour = (now.hour - 5) % 24
        if local_hour != 9:
            return
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="standups")
            if not channel:
                channel = discord.utils.get(guild.text_channels, name="general")
            if channel:
                embed = standup_embed("¡Buenos días, equipo! ☀️",
                    "Es hora del standup diario.\nUsa **`/standup`** para reportar tu progreso.\n\n"
                    "1️⃣ ¿Qué hiciste ayer?\n2️⃣ ¿Qué harás hoy?\n3️⃣ ¿Tienes algún bloqueo?")
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

    @standup_reminder.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Standup(bot))
