"""
Decoradores de permisos personalizados según roles del equipo.
"""
import discord
from discord.ext import commands


def es_admin():
    """Solo Fundadores y Admins pueden usar este comando."""
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        admin_roles = ["Admin", "Fundador"]
        return any(role.name in admin_roles for role in ctx.author.roles)
    return commands.check(predicate)


def es_pm():
    """Project Managers, Fundadores y Admins."""
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        allowed = ["Admin", "Fundador", "Project Manager"]
        return any(role.name in allowed for role in ctx.author.roles)
    return commands.check(predicate)


def es_dev():
    """Cualquier rol de desarrollo o superior."""
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        dev_roles = [
            "Admin", "Fundador", "Project Manager",
            "Frontend Dev", "Backend Dev", "Mobile Dev",
            "QA / Tester", "UI/UX Designer"
        ]
        return any(role.name in dev_roles for role in ctx.author.roles)
    return commands.check(predicate)


def es_miembro():
    """Cualquier miembro con al menos un rol del equipo (excluye @everyone)."""
    async def predicate(ctx: commands.Context) -> bool:
        return len(ctx.author.roles) > 1  # Más que solo @everyone
    return commands.check(predicate)
