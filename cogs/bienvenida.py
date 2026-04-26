"""
Módulo de Bienvenida — Onboarding de nuevos miembros.
RF-BI-01 a RF-BI-02
"""
import discord
from discord.ext import commands
import logging
from utils.constants import Colors

logger = logging.getLogger("cog.bienvenida")

class Bienvenida(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Embed en canal general/bienvenida
        channel = discord.utils.get(member.guild.text_channels, name="bienvenida") or \
                  discord.utils.get(member.guild.text_channels, name="general")
        if channel:
            embed = discord.Embed(
                title=f"¡Bienvenido/a, {member.display_name}! 🎉",
                description=(
                    f"Es genial tenerte en **{member.guild.name}**.\n\n"
                    "🚀 Usa `/rolmenu` para elegir tu rol en el equipo.\n"
                    "📋 Usa `/help` para ver todos los comandos.\n"
                    "🤖 Usa `/pregunta` para hablar con la IA."
                ),
                color=Colors.SUCCESS
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"Miembro #{member.guild.member_count}")
            await channel.send(embed=embed)

        # DM de onboarding
        try:
            dm_embed = discord.Embed(
                title=f"¡Bienvenido/a a {member.guild.name}! 🏢",
                description=(
                    "Aquí tienes lo que necesitas saber:\n\n"
                    "**1.** Elige tu rol con `/rolmenu` en el servidor\n"
                    "**2.** Revisa los canales de tu área\n"
                    "**3.** Reporta tu progreso diario con `/standup`\n"
                    "**4.** Consulta a la IA con `/pregunta`\n\n"
                    "¡Mucho éxito! 💪"
                ),
                color=Colors.BRAND
            )
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            logger.info(f"No se pudo enviar DM a {member.display_name}")

async def setup(bot):
    await bot.add_cog(Bienvenida(bot))