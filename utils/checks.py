"""
Decoradores de permisos personalizados según roles del equipo.
"""
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
