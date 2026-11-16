"""
Módulo de Música — Reproductor de música con cola, mixes y mixes IA.
RF-MU-01 a RF-MU-04: Play, cola, mixes manuales, mix generado por IA.
"""
import discord
from discord.ext import commands
from discord import app_commands, ui
import yt_dlp
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from openai import OpenAI

from config import (
    API_QWEN, QWEN_BASE_URL, QWEN_MODEL_TEXT,
    MAX_SONGS_PER_MIX, MAX_MIXES_PER_USER,
    YOUTUBE_TIMEOUT, IA_LIMIT_MIX
)
from utils.embeds import music_embed, error_embed, success_embed, warning_embed, set_author

logger = logging.getLogger("cog.music")

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "socket_timeout": 10,
}

# Las canciones públicas no necesitan una sesión de YouTube. Las cookies
# pueden forzar un cliente cuyo stream sea rechazado con HTTP 403.
if os.getenv("YOUTUBE_COOKIE_FILE"):
    YDL_OPTIONS["cookiefile"] = os.environ["YOUTUBE_COOKIE_FILE"]

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class MixIAView(ui.View):
    """Botones interactivos para mixes generados por IA."""

    def __init__(self, cog, ctx, songs: list, description: str, timeout=120):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.ctx = ctx
        self.songs = songs
        self.description = description

    @ui.button(label="▶️ Reproducir", style=discord.ButtonStyle.green)
    async def play_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Solo quien pidió el mix puede usarlo.", ephemeral=True)

        # Verificar que el usuario está en un canal de voz
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Debes estar en un canal de voz.", ephemeral=True)

        await interaction.response.defer()

        # Conectar al canal de voz si no está conectado
        try:
            if not self.cog.voice_client or not self.cog.voice_client.is_connected():
                self.cog.voice_client = await interaction.user.voice.channel.connect()
            elif self.cog.voice_client.channel != interaction.user.voice.channel:
                await self.cog.voice_client.move_to(interaction.user.voice.channel)
        except Exception as e:
            return await interaction.followup.send(f"❌ No pude conectarme al canal de voz: {e}")

        self.cog._cancel_disconnect()

        for song in self.songs:
            query = f"{song['artista']} - {song['titulo']}"
            self.cog.queue.append({"query": query, "title": query, "requested_by": interaction.user.display_name,
                                   "requested_by_id": interaction.user.id})

        await interaction.followup.send(f"🎵 Mix encolado: **{len(self.songs)} canciones**. ¡Reproduciendo!")

        if not self.cog.voice_client.is_playing():
            await self.cog._play_next(self.ctx)

        self.stop()

    @ui.button(label="💾 Guardar Mix", style=discord.ButtonStyle.blurple)
    async def save_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Solo quien pidió el mix puede guardarlo.", ephemeral=True)

        await interaction.response.defer()

        # Verificar límite de mixes
        count = await self.cog.bot.db.contar_mixes(self.ctx.guild.id, self.ctx.author.id)
        if count >= MAX_MIXES_PER_USER:
            return await interaction.followup.send(f"❌ Ya tienes {MAX_MIXES_PER_USER} mixes. Elimina uno primero.")

        # Generar nombre del mix
        mix_name = self.description[:50].replace(" ", "-").lower()
        try:
            mix_id = await self.cog.bot.db.crear_mix(self.ctx.guild.id, self.ctx.author.id, mix_name)
            for i, song in enumerate(self.songs):
                await self.cog.bot.db.agregar_cancion_mix(mix_id, song["titulo"], song.get("artista"), i + 1)
            await interaction.followup.send(f"💾 Mix **{mix_name}** guardado con {len(self.songs)} canciones.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error al guardar: {e}")

        self.stop()

    @ui.button(label="🔄 Regenerar", style=discord.ButtonStyle.grey)
    async def regen_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Solo quien pidió el mix puede regenerar.", ephemeral=True)

        await interaction.response.defer()
        self.stop()
        # Regenerar
        await self.cog._generate_ai_mix(self.ctx, self.description)


class Music(commands.Cog):
    """Módulo de música con cola, mixes, y mixes IA."""

    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.voice_client = None
        self.current_song = None
        self.is_playing = False
        self.disconnect_task = None  # Timer de auto-desconexión
        self.ai_client = OpenAI(api_key=API_QWEN, base_url=QWEN_BASE_URL)

    # ─── Helpers ─────────────────────────────────────────────

    async def _ensure_voice(self, ctx) -> bool:
        """Asegura que el usuario está en un canal de voz y el bot conectado."""
        if not ctx.author.voice:
            embed = error_embed("Sin canal de voz", "Debes estar en un canal de voz para usar este comando.")
            await ctx.send(embed=embed)
            return False

        if not self.voice_client or not self.voice_client.is_connected():
            self.voice_client = await ctx.author.voice.channel.connect()
        elif self.voice_client.channel != ctx.author.voice.channel:
            await self.voice_client.move_to(ctx.author.voice.channel)

        return True

    async def _search_youtube(self, query: str) -> dict | None:
        """Busca una canción en YouTube de forma async."""
        loop = asyncio.get_event_loop()

        def extract():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                return ydl.extract_info(f"ytsearch:{query}", download=False)

        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(None, extract),
                timeout=YOUTUBE_TIMEOUT
            )
            if info and "entries" in info and info["entries"]:
                entry = info["entries"][0]
                return {
                    "url": entry["url"],
                    "title": entry.get("title", query),
                    "duration": entry.get("duration", 0),
                    "thumbnail": entry.get("thumbnail"),
                    "webpage_url": entry.get("webpage_url"),
                }
        except asyncio.TimeoutError:
            logger.warning(f"Timeout buscando: {query}")
        except Exception as e:
            logger.error(f"Error YouTube: {e}")
        return None

    async def _auto_disconnect(self, ctx):
        """Espera 60 segundos y desconecta el bot si no hay música."""
        await asyncio.sleep(60)
        if self.voice_client and self.voice_client.is_connected() and not self.voice_client.is_playing():
            await self.voice_client.disconnect()
            self.voice_client = None
            self.is_playing = False
            self.current_song = None
            try:
                await ctx.send("👋 Me desconecté por inactividad (1 min sin música).")
            except Exception:
                pass

    def _cancel_disconnect(self):
        """Cancela el timer de auto-desconexión si existe."""
        if self.disconnect_task and not self.disconnect_task.done():
            self.disconnect_task.cancel()
            self.disconnect_task = None

    async def _play_next(self, ctx):
        """Reproduce la siguiente canción de la cola."""
        if not self.queue:
            self.is_playing = False
            self.current_song = None
            # Iniciar timer de auto-desconexión (1 minuto)
            self._cancel_disconnect()
            self.disconnect_task = asyncio.create_task(self._auto_disconnect(ctx))
            return

        if not self.voice_client or not self.voice_client.is_connected():
            return

        song = self.queue.pop(0)
        query = song.get("query") or song.get("title")

        result = await self._search_youtube(query)
        if not result:
            await ctx.send(f"⏩ No se encontró: **{query}**. Saltando...")
            await self._play_next(ctx)
            return

        self.current_song = {**result, "requested_by": song.get("requested_by", "?")}
        self.is_playing = True
        self._cancel_disconnect()  # Cancelar auto-desconexión si hay música

        try:
            source = await discord.FFmpegOpusAudio.from_probe(result["url"], **FFMPEG_OPTIONS)
            loop = asyncio.get_running_loop()

            def playback_done(future):
                try:
                    future.result()
                except Exception:
                    logger.exception("Error avanzando la cola de reproducción")

            def after_play(error):
                if error:
                    logger.error(f"Error reproducción: {error}")
                future = asyncio.run_coroutine_threadsafe(self._play_next(ctx), loop)
                future.add_done_callback(playback_done)

            self.voice_client.play(source, after=after_play)

            # Un fallo al persistir no debe interrumpir el audio ni saltar de pista.
            try:
                await self.bot.db.registrar_reproduccion(
                    ctx.guild.id, song.get("requested_by_id"),
                    song.get("requested_by", "?"), result["title"],
                    result.get("webpage_url"), result.get("duration")
                )
            except Exception:
                logger.exception("No se pudo guardar la reproducción en el historial")

            embed = music_embed("Reproduciendo ahora", f"**{result['title']}**")
            if result.get("duration"):
                mins, secs = divmod(result["duration"], 60)
                embed.add_field(name="⏱️ Duración", value=f"`{mins}:{secs:02d}`", inline=True)
            embed.add_field(name="👤 Pedido por", value=song.get("requested_by", "?"), inline=True)
            if len(self.queue) > 0:
                embed.add_field(name="📋 En cola", value=f"`{len(self.queue)}` canciones", inline=True)
            if result.get("thumbnail"):
                embed.set_thumbnail(url=result["thumbnail"])
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error FFmpeg: {e}")
            await ctx.send(f"❌ Error al reproducir: {e}")
            await self._play_next(ctx)

    # ─── RF-MU-01: Play ──────────────────────────────────────

    @commands.hybrid_command(name="play", description="Reproduce música de YouTube")
    @app_commands.describe(busqueda="Nombre de la canción o URL")
    async def play(self, ctx, *, busqueda: str):
        if busqueda.lower().startswith("busqueda:"):
            busqueda = busqueda[9:].strip()

        await ctx.defer()

        if not await self._ensure_voice(ctx):
            return

        # Si ya está reproduciendo, agregar a la cola
        if self.voice_client.is_playing() or self.is_playing:
            self.queue.append({
                "query": busqueda,
                "title": busqueda,
                "requested_by": ctx.author.display_name,
                "requested_by_id": ctx.author.id,
            })
            embed = music_embed("Agregado a la cola", f"**{busqueda}**\nPosición: `#{len(self.queue)}`")
            set_author(embed, ctx)
            return await ctx.send(embed=embed)

        # Reproducir directamente
        self.queue.append({
            "query": busqueda,
            "title": busqueda,
            "requested_by": ctx.author.display_name,
            "requested_by_id": ctx.author.id,
        })
        await self._play_next(ctx)

    # ─── RF-MU-02: Cola de reproducción ──────────────────────

    @commands.hybrid_command(name="cola", description="Ver la cola de reproducción")
    async def cola(self, ctx):
        if not self.queue and not self.current_song:
            embed = music_embed("Cola vacía", "No hay canciones en cola. Usa `/play` para agregar.")
            return await ctx.send(embed=embed)

        lines = []
        if self.current_song:
            lines.append(f"▶️ **Ahora:** {self.current_song['title']}")
            lines.append("")

        for i, song in enumerate(self.queue[:15]):
            lines.append(f"`{i+1}.` {song['title']}")

        if len(self.queue) > 15:
            lines.append(f"\n*...y {len(self.queue) - 15} más*")

        embed = music_embed("Cola de reproducción", "\n".join(lines))
        embed.set_footer(text=f"{len(self.queue)} canciones en cola")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="historial", description="Ver las últimas canciones reproducidas en este servidor")
    @commands.guild_only()
    @app_commands.describe(pagina="Página del historial (10 canciones por página)")
    async def historial(self, ctx, pagina: int = 1):
        if pagina < 1 or pagina > 1000000:
            return await ctx.send("❌ Usa una página entre 1 y 1000000.")
        await ctx.defer()
        rows = await self.bot.db.obtener_historial_musica(ctx.guild.id, pagina)
        if not rows:
            return await ctx.send(embed=music_embed(
                "Sin historial", "No hay reproducciones en esta página. El historial se guarda desde su activación."
            ))

        lines = []
        for i, row in enumerate(rows[:10], start=(pagina - 1) * 10 + 1):
            title = discord.utils.escape_markdown(row["titulo"][:150])
            name = discord.utils.escape_markdown(row["solicitado_por"][:80])
            timestamp = int(datetime.fromisoformat(row["fecha"]).replace(tzinfo=timezone.utc).timestamp())
            lines.append(f"**{i}. {title}**\nPedido por {name} · <t:{timestamp}:f>")
        embed = music_embed("Historial de música", "\n\n".join(lines))
        footer = f"Página {pagina} · Más recientes primero"
        if len(rows) > 10:
            footer += f" · Siguiente: /historial pagina:{pagina + 1}"
        embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="skip", description="Salta a la siguiente canción")
    async def skip(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("⏩ Canción saltada.")
        else:
            await ctx.send("❌ No hay nada reproduciéndose.")

    @commands.hybrid_command(name="pause", description="Pausa la reproducción")
    async def pause(self, ctx):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("⏸️ Reproducción pausada.")
        else:
            await ctx.send("❌ No hay nada reproduciéndose.")

    @commands.hybrid_command(name="resume", description="Reanuda la reproducción")
    async def resume(self, ctx):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada.")
        else:
            await ctx.send("❌ No hay nada pausado.")

    @commands.hybrid_command(name="np", description="Muestra la canción actual")
    async def nowplaying(self, ctx):
        if not self.current_song:
            return await ctx.send("❌ No hay nada reproduciéndose.")

        embed = music_embed("Reproduciendo ahora", f"**{self.current_song['title']}**")
        embed.add_field(name="👤 Pedido por", value=self.current_song.get("requested_by", "?"), inline=True)
        embed.add_field(name="📋 En cola", value=f"`{len(self.queue)}`", inline=True)
        if self.current_song.get("thumbnail"):
            embed.set_thumbnail(url=self.current_song["thumbnail"])
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stop", description="Detiene la música y desconecta al bot")
    async def stop(self, ctx):
        if self.voice_client:
            self.queue.clear()
            self.current_song = None
            self.is_playing = False
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("🛑 Música detenida, cola limpiada y bot desconectado.")
        else:
            await ctx.send("❌ El bot no está conectado a ningún canal.")

    # ─── RF-MU-03: Mixes manuales ───────────────────────────

    @commands.hybrid_group(name="mix", fallback="info", description="Gestión de mixes/playlists")
    async def mix_group(self, ctx):
        embed = music_embed(
            "Mixes — Comandos",
            "**`/mix crear <nombre>`** — Crear un mix vacío\n"
            "**`/mix agregar <nombre> <canción>`** — Agregar canción\n"
            "**`/mix reproducir <nombre>`** — Reproducir mix\n"
            "**`/mix listar`** — Ver tus mixes\n"
            "**`/mix eliminar <nombre>`** — Eliminar un mix\n"
            "**`/mix aleatorio <nombre>`** — Guardar 10 canciones al azar del historial\n"
            "**`/mix ia <descripción>`** — Generar mix con IA 🤖"
        )
        await ctx.send(embed=embed)

    @mix_group.command(name="crear", description="Crea un nuevo mix")
    @app_commands.describe(nombre="Nombre del mix")
    async def mix_crear(self, ctx, *, nombre: str):
        count = await self.bot.db.contar_mixes(ctx.guild.id, ctx.author.id)
        if count >= MAX_MIXES_PER_USER:
            return await ctx.send(embed=error_embed("Límite de mixes", f"Ya tienes {MAX_MIXES_PER_USER} mixes. Elimina uno primero."))

        try:
            await self.bot.db.crear_mix(ctx.guild.id, ctx.author.id, nombre)
            embed = success_embed("Mix creado", f"Mix **{nombre}** creado. Usa `/mix agregar {nombre} <canción>` para agregar canciones.")
            set_author(embed, ctx)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(embed=error_embed("Mix duplicado", f"Ya tienes un mix llamado **{nombre}**."))

    @mix_group.command(name="aleatorio", description="Crea una playlist de 10 canciones al azar del historial del servidor")
    @commands.guild_only()
    @app_commands.describe(nombre="Nombre para guardar la playlist aleatoria")
    async def mix_aleatorio(self, ctx, *, nombre: str):
        nombre = nombre.strip()
        if not nombre or len(nombre) > 50:
            return await ctx.send(embed=error_embed("Nombre inválido", "Usa un nombre de 1 a 50 caracteres."))
        await ctx.defer()
        try:
            songs = await self.bot.db.crear_mix_aleatorio(
                ctx.guild.id, ctx.author.id, nombre, MAX_MIXES_PER_USER
            )
        except ValueError:
            return await ctx.send(embed=error_embed("Límite de mixes", f"Ya tienes {MAX_MIXES_PER_USER} mixes. Elimina uno primero."))
        except sqlite3.IntegrityError:
            return await ctx.send(embed=error_embed("Mix duplicado", "Ya tienes un mix con ese nombre. Elige otro."))
        if not songs:
            return await ctx.send(embed=music_embed("Sin historial", "Primero reproduce canciones con `/play` para crear un historial."))

        lines = [f"`{i}.` {discord.utils.escape_markdown(song['titulo'][:150])}"
                 for i, song in enumerate(songs, start=1)]
        description = f"**{discord.utils.escape_markdown(nombre)}** — {len(songs)} canciones sin repetir.\n\n" + "\n".join(lines)
        if len(songs) < 10:
            description += "\n\nTodavía hay menos de 10 canciones distintas en el historial; usé todas las disponibles."
        description += f"\n\n▶️ Reproduce con `/mix reproducir nombre:{nombre}`."
        await ctx.send(embed=music_embed("Playlist aleatoria guardada", description))

    @mix_group.command(name="agregar", description="Agrega una canción a un mix")
    @app_commands.describe(nombre="Nombre del mix", cancion="Nombre de la canción a agregar")
    async def mix_agregar(self, ctx, nombre: str, *, cancion: str):
        mix = await self.bot.db.obtener_mix_por_nombre(ctx.guild.id, ctx.author.id, nombre)
        if not mix:
            return await ctx.send(embed=error_embed("Mix no encontrado", f"No tienes un mix llamado **{nombre}**."))

        canciones = await self.bot.db.obtener_canciones_mix(mix["id"])
        if len(canciones) >= MAX_SONGS_PER_MIX:
            return await ctx.send(embed=error_embed("Mix lleno", f"Este mix ya tiene {MAX_SONGS_PER_MIX} canciones."))

        await self.bot.db.agregar_cancion_mix(mix["id"], cancion)
        embed = success_embed("Canción agregada", f"**{cancion}** → Mix **{nombre}** (#{len(canciones)+1})")
        await ctx.send(embed=embed)

    @mix_group.command(name="listar", description="Ver todos tus mixes")
    async def mix_listar(self, ctx):
        mixes = await self.bot.db.obtener_mixes(ctx.guild.id, ctx.author.id)
        if not mixes:
            return await ctx.send(embed=music_embed("Sin mixes", "No tienes mixes. Crea uno con `/mix crear <nombre>`."))

        lines = []
        for m in mixes:
            canciones = await self.bot.db.obtener_canciones_mix(m["id"])
            lines.append(f"🎵 **{m['nombre']}** — `{len(canciones)}` canciones")

        embed = music_embed("Tus Mixes", "\n".join(lines))
        embed.set_footer(text=f"{len(mixes)}/{MAX_MIXES_PER_USER} mixes")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

    @mix_group.command(name="reproducir", description="Reproduce un mix completo")
    @app_commands.describe(nombre="Nombre del mix")
    async def mix_reproducir(self, ctx, *, nombre: str):
        await ctx.defer()

        if not await self._ensure_voice(ctx):
            return

        mix = await self.bot.db.obtener_mix_por_nombre(ctx.guild.id, ctx.author.id, nombre)
        if not mix:
            return await ctx.send(embed=error_embed("Mix no encontrado", f"No tienes un mix llamado **{nombre}**."))

        canciones = await self.bot.db.obtener_canciones_mix(mix["id"])
        if not canciones:
            return await ctx.send(embed=error_embed("Mix vacío", "Este mix no tiene canciones."))

        for c in canciones:
            query = f"{c['artista']} - {c['titulo']}" if c["artista"] else c["titulo"]
            self.queue.append({"query": query, "title": query, "requested_by": ctx.author.display_name,
                               "requested_by_id": ctx.author.id})

        embed = music_embed("Mix encolado", f"**{nombre}** — `{len(canciones)}` canciones agregadas a la cola.")
        set_author(embed, ctx)
        await ctx.send(embed=embed)

        if not self.voice_client.is_playing() and not self.is_playing:
            await self._play_next(ctx)

    @mix_group.command(name="eliminar", description="Elimina un mix")
    @app_commands.describe(nombre="Nombre del mix a eliminar")
    async def mix_eliminar(self, ctx, *, nombre: str):
        mix = await self.bot.db.obtener_mix_por_nombre(ctx.guild.id, ctx.author.id, nombre)
        if not mix:
            return await ctx.send(embed=error_embed("Mix no encontrado", f"No tienes un mix llamado **{nombre}**."))

        await self.bot.db.eliminar_mix(mix["id"])
        embed = success_embed("Mix eliminado", f"Mix **{nombre}** eliminado permanentemente.")
        await ctx.send(embed=embed)

    # ─── RF-MU-04: Mix generado por IA ──────────────────────

    @mix_group.command(name="ia", description="Genera un mix con IA basado en tu descripción")
    @app_commands.describe(
        descripcion="Describe el tipo de música que quieres",
        cantidad="Número de canciones (3-30, por defecto 10)"
    )
    @commands.cooldown(3, 60, commands.BucketType.user)
    async def mix_ia(self, ctx, cantidad: int = 10, *, descripcion: str):
        await ctx.defer()

        # Validar cantidad
        cantidad = max(3, min(30, cantidad))

        # Verificar límite
        count = await self.bot.db.contar_uso_ia_hoy(ctx.author.id, "mix")
        if count >= IA_LIMIT_MIX:
            return await ctx.send(embed=warning_embed(
                "Límite alcanzado",
                f"Has alcanzado tu límite de {IA_LIMIT_MIX} generaciones de mix por día."
            ))

        await self._generate_ai_mix(ctx, descripcion, cantidad)

    async def _generate_ai_mix(self, ctx, descripcion: str, cantidad: int = 10):
        """Genera un mix con IA."""
        loop = asyncio.get_event_loop()

        def _request():
            return self.ai_client.chat.completions.create(
                model=QWEN_MODEL_TEXT,
                messages=[
                    {"role": "system", "content": "Eres un experto en música. Genera playlists personalizadas."},
                    {"role": "user", "content": f"""Genera una playlist de {cantidad} canciones basada en esta descripción: "{descripcion}".

Responde ÚNICAMENTE con un JSON array válido, sin explicaciones ni texto adicional.
Formato: [{{"artista": "nombre del artista", "titulo": "nombre de la canción"}}]
Elige canciones reales y populares que se puedan encontrar en YouTube."""}
                ],
            )

        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _request),
                timeout=30.0
            )
            content = response.choices[0].message.content.strip()

            # Limpiar posibles backticks de markdown
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            songs = json.loads(content)

            if not isinstance(songs, list) or len(songs) == 0:
                return await ctx.send(embed=error_embed("Error IA", "La IA no generó una playlist válida. Intenta con otra descripción."))

            # Registrar uso
            await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "mix")

            # Mostrar el mix
            lines = []
            for i, song in enumerate(songs):
                lines.append(f"`{i+1}.` **{song.get('artista', '?')}** — {song.get('titulo', '?')}")

            embed = music_embed(
                f"Mix generado por IA 🤖 ({len(songs)} canciones)",
                f"*\"{descripcion}\"*\n\n" + "\n".join(lines)
            )
            embed.set_footer(text="Usa los botones para reproducir, guardar o regenerar")
            set_author(embed, ctx)

            view = MixIAView(self, ctx, songs, descripcion)
            await ctx.send(embed=embed, view=view)

        except json.JSONDecodeError:
            await ctx.send(embed=error_embed("Error de formato", "La IA no devolvió un formato válido. Intenta de nuevo."))
        except asyncio.TimeoutError:
            await ctx.send(embed=error_embed("Timeout", "La IA tardó demasiado. Intenta de nuevo."))
        except Exception as e:
            logger.error(f"Error mix IA: {e}")
            await ctx.send(embed=error_embed("Error", f"Error generando mix: {e}"))

    @mix_ia.error
    async def mix_ia_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            segundos = round(error.retry_after)
            await ctx.send(embed=warning_embed(
                "Cooldown activo",
                f"Para evitar abusos durante tus pruebas, el límite es de **3 veces por minuto**.\n"
                f"Podrás usarlo de nuevo en **{segundos} segundos**."
            ), ephemeral=True)
        else:
            logger.error(f"Error en mix_ia: {error}")


async def setup(bot):
    await bot.add_cog(Music(bot))
