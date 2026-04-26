"""
Módulo de Monitoreo — Status del sistema y uptime real.
RF-MO-01 a RF-MO-02
"""
import discord
from discord.ext import commands
import psutil
import time
import logging
from datetime import datetime
from utils.embeds import info_embed, set_author
from utils.constants import Colors

logger = logging.getLogger("cog.monitor")

class Monitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="status", description="Muestra el estado del sistema y el bot")
    async def status(self, ctx):
        latency = round(self.bot.latency * 1000)
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        uptime_secs = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_secs, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="📊 Estado del Sistema — YoRobot v2.0",
            color=Colors.BRAND, timestamp=datetime.utcnow())

        embed.add_field(name="📶 Latencia", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="💻 CPU", value=f"`{cpu}%`", inline=True)
        embed.add_field(name="🧠 RAM", value=f"`{ram.percent}%` ({ram.used // (1024**2)}MB/{ram.total // (1024**2)}MB)", inline=True)
        embed.add_field(name="🕒 Uptime", value=f"`{hours}h {minutes}m {seconds}s`", inline=True)
        embed.add_field(name="📡 Servidores", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="⚙️ Módulos", value=f"`{len(self.bot.cogs)}`", inline=True)

        # Listar cogs cargados
        cogs_list = ", ".join(f"`{name}`" for name in self.bot.cogs.keys())
        embed.add_field(name="🔧 Módulos activos", value=cogs_list, inline=False)

        set_author(embed, ctx)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Monitor(bot))