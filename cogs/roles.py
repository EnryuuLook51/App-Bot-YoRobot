"""
Módulo de Roles — Auto-asignación de roles del equipo con menú interactivo.
RF-RO-01 a RF-RO-03
"""
import discord
from discord.ext import commands
from discord import app_commands, ui
import logging
from config import TEAM_ROLES, MAX_DEV_ROLES
from utils.embeds import success_embed, error_embed, set_author
from utils.checks import es_admin
from utils.constants import Colors

logger = logging.getLogger("cog.roles")

class RoleSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=d["name"], value=k, emoji=d["emoji"])
            for k, d in TEAM_ROLES.items()
        ]
        super().__init__(placeholder="Selecciona tu rol...", min_values=1, max_values=MAX_DEV_ROLES, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild, member = interaction.guild, interaction.user
        # Remover roles de equipo actuales
        for k, d in TEAM_ROLES.items():
            r = discord.utils.get(guild.roles, name=d["name"])
            if r and r in member.roles:
                await member.remove_roles(r)
        # Agregar seleccionados
        added = []
        for sel in self.values:
            d = TEAM_ROLES[sel]
            r = discord.utils.get(guild.roles, name=d["name"])
            if not r:
                r = await guild.create_role(name=d["name"], color=discord.Color(d["color"]), mentionable=True)
            await member.add_roles(r)
            added.append(f"{d['emoji']} {d['name']}")
        embed = success_embed("Roles actualizados", f"**{member.display_name}**:\n" + "\n".join(added))
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="rolmenu", description="Menú para elegir tu rol en el equipo")
    async def rol_menu(self, ctx):
        embed = discord.Embed(title="🏢 Roles del Equipo", color=Colors.BRAND,
            description=f"Selecciona hasta **{MAX_DEV_ROLES}** roles:\n\n" +
            "\n".join(f"{d['emoji']} **{d['name']}**" for d in TEAM_ROLES.values()))
        await ctx.send(embed=embed, view=RoleView())

    @commands.hybrid_command(name="equipo", description="Ver distribución del equipo")
    async def equipo(self, ctx):
        embed = discord.Embed(title="👥 Equipo", color=Colors.BRAND, timestamp=discord.utils.utcnow())
        total = 0
        for k, d in TEAM_ROLES.items():
            r = discord.utils.get(ctx.guild.roles, name=d["name"])
            if r:
                ms = [m.display_name for m in r.members]
                total += len(ms)
                val = "\n".join(f"• {m}" for m in ms) if ms else "*Vacío*"
            else:
                val = "*Sin crear*"
            embed.add_field(name=f"{d['emoji']} {d['name']}", value=val, inline=True)
        embed.set_footer(text=f"Total: {total} miembros")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rolasignar", description="Asigna un rol (Admin)")
    @app_commands.describe(usuario="Usuario", rol="Rol (frontend, backend, mobile, pm, qa, uiux, pasante)")
    @es_admin()
    async def rol_asignar(self, ctx, usuario: discord.Member, rol: str):
        if rol.lower() not in TEAM_ROLES:
            return await ctx.send(embed=error_embed("Rol inválido", f"Disponibles: {', '.join(TEAM_ROLES.keys())}"))
        d = TEAM_ROLES[rol.lower()]
        r = discord.utils.get(ctx.guild.roles, name=d["name"]) or \
            await ctx.guild.create_role(name=d["name"], color=discord.Color(d["color"]), mentionable=True)
        await usuario.add_roles(r)
        await ctx.send(embed=success_embed("Rol asignado", f"{d['emoji']} **{d['name']}** → **{usuario.display_name}**"))

    @commands.hybrid_command(name="rolquitar", description="Quita un rol (Admin)")
    @app_commands.describe(usuario="Usuario", rol="Nombre del rol")
    @es_admin()
    async def rol_quitar(self, ctx, usuario: discord.Member, rol: str):
        if rol.lower() not in TEAM_ROLES:
            return await ctx.send(embed=error_embed("Rol inválido", "Usa un nombre válido."))
        d = TEAM_ROLES[rol.lower()]
        r = discord.utils.get(ctx.guild.roles, name=d["name"])
        if r and r in usuario.roles:
            await usuario.remove_roles(r)
            await ctx.send(embed=success_embed("Rol removido", f"**{d['name']}** quitado de **{usuario.display_name}**"))
        else:
            await ctx.send(embed=error_embed("Sin rol", f"{usuario.display_name} no tiene ese rol."))

async def setup(bot):
    await bot.add_cog(Roles(bot))
