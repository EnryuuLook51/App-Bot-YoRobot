"""
Módulo de Tareas/Tickets — Sistema de gestión de tareas del equipo.
RF-TA-01 a RF-TA-05
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import TASK_STATES, TASK_PRIORITIES
from utils.embeds import task_embed, success_embed, error_embed, set_author
from utils.constants import Colors, TASK_STATE_EMOJIS, PRIORITY_EMOJIS

logger = logging.getLogger("cog.tareas")

class Tareas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tarea", description="Crea una nueva tarea")
    @app_commands.describe(
        titulo="Título de la tarea",
        asignado="Usuario asignado (opcional)",
        prioridad="baja, media, alta, crítica",
        fecha_limite="Fecha límite YYYY-MM-DD (opcional)"
    )
    async def crear_tarea(self, ctx, titulo: str, asignado: discord.Member = None,
                          prioridad: str = "media", fecha_limite: str = None):
        if prioridad not in TASK_PRIORITIES:
            return await ctx.send(embed=error_embed("Prioridad inválida", f"Opciones: {', '.join(TASK_PRIORITIES)}"))

        tarea_id = await self.bot.db.crear_tarea(
            guild_id=ctx.guild.id, titulo=titulo, creado_por=ctx.author.id,
            asignado_a=asignado.id if asignado else None,
            prioridad=prioridad, fecha_limite=fecha_limite
        )
        emoji_p = PRIORITY_EMOJIS.get(prioridad, "🔸")
        embed = success_embed("Tarea creada", f"**#{tarea_id}** — {titulo}")
        embed.add_field(name="Prioridad", value=f"{emoji_p} {prioridad}", inline=True)
        embed.add_field(name="Asignado", value=asignado.display_name if asignado else "Sin asignar", inline=True)
        embed.add_field(name="Estado", value=f"{TASK_STATE_EMOJIS['pendiente']} pendiente", inline=True)
        if fecha_limite:
            embed.add_field(name="📅 Fecha límite", value=fecha_limite, inline=True)
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="tareas", description="Lista las tareas del equipo")
    @app_commands.describe(filtro="pendientes, en-progreso, completadas, mias, urgentes, vencidas")
    async def listar_tareas(self, ctx, filtro: str = "pendientes"):
        tareas = await self.bot.db.obtener_tareas(ctx.guild.id, filtro=filtro, user_id=ctx.author.id)
        if not tareas:
            return await ctx.send(embed=task_embed("Sin tareas", f"No hay tareas con filtro: **{filtro}**"))

        lines = []
        for t in tareas[:15]:
            emoji_e = TASK_STATE_EMOJIS.get(t["estado"], "🔸")
            emoji_p = PRIORITY_EMOJIS.get(t["prioridad"], "")
            asignado = f"<@{t['asignado_a']}>" if t["asignado_a"] else "—"
            lines.append(f"{emoji_e} `#{t['id']}` {emoji_p} **{t['titulo']}** → {asignado}")

        if len(tareas) > 15:
            lines.append(f"\n*...y {len(tareas) - 15} más*")

        embed = task_embed(f"Tareas — {filtro}", "\n".join(lines))
        embed.set_footer(text=f"{len(tareas)} tareas encontradas")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="mistareas", description="Ver tus tareas asignadas")
    async def mis_tareas(self, ctx):
        tareas = await self.bot.db.obtener_tareas(ctx.guild.id, filtro="mias", user_id=ctx.author.id)
        if not tareas:
            return await ctx.send(embed=task_embed("Sin tareas", "No tienes tareas asignadas. ¡Buen trabajo! 🎉"))

        lines = []
        for t in tareas:
            emoji_e = TASK_STATE_EMOJIS.get(t["estado"], "🔸")
            emoji_p = PRIORITY_EMOJIS.get(t["prioridad"], "")
            lines.append(f"{emoji_e} `#{t['id']}` {emoji_p} **{t['titulo']}** [{t['estado']}]")

        embed = task_embed(f"Tareas de {ctx.author.display_name}", "\n".join(lines))
        embed.set_footer(text=f"{len(tareas)} tareas")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="tareaestado", description="Cambia el estado de una tarea")
    @app_commands.describe(tarea_id="ID de la tarea", estado="pendiente, en-progreso, revisión, completada")
    async def cambiar_estado(self, ctx, tarea_id: int, estado: str):
        if estado not in TASK_STATES:
            return await ctx.send(embed=error_embed("Estado inválido", f"Opciones: {', '.join(TASK_STATES)}"))

        tarea = await self.bot.db.obtener_tarea(tarea_id)
        if not tarea:
            return await ctx.send(embed=error_embed("No encontrada", f"No existe la tarea #{tarea_id}"))

        await self.bot.db.actualizar_estado_tarea(tarea_id, estado)
        emoji = TASK_STATE_EMOJIS.get(estado, "🔸")
        embed = success_embed("Estado actualizado", f"Tarea **#{tarea_id}** — {tarea['titulo']}\n{emoji} → **{estado}**")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="tablero", description="Vista kanban de tareas")
    async def tablero(self, ctx):
        embed = discord.Embed(title="📋 Tablero Kanban", color=Colors.TASK, timestamp=discord.utils.utcnow())
        for estado in TASK_STATES:
            tareas = await self.bot.db.obtener_tareas(ctx.guild.id, filtro=estado if estado != "en-progreso" else "en-progreso")
            # Filtro manual para estados exactos
            tareas_estado = [t for t in (await self.bot.db.fetchall(
                "SELECT * FROM tareas WHERE guild_id = ? AND estado = ? AND estado != 'completada' ORDER BY id DESC LIMIT 5",
                (ctx.guild.id, estado)
            ))]
            emoji = TASK_STATE_EMOJIS.get(estado, "🔸")
            if tareas_estado:
                val = "\n".join(f"`#{t['id']}` {t['titulo']}" for t in tareas_estado)
            else:
                val = "*Vacío*"
            embed.add_field(name=f"{emoji} {estado.upper()}", value=val, inline=True)
        set_author(embed, ctx)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tareas(bot))
