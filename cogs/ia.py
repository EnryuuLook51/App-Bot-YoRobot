"""
Módulo de IA — Asistente inteligente del equipo.
RF-IA-01 a RF-IA-08: Chat, visión de imágenes, lectura de archivos,
hilos con contexto, code review, generación de docs, stats de uso.
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
import logging
from openai import OpenAI

from config import (
    API_QWEN, QWEN_BASE_URL, QWEN_MODEL_TEXT, QWEN_MODEL_VISION,
    SYSTEM_PROMPT, IA_LIMIT_IMAGE, IA_LIMIT_FILE, IA_LIMIT_MIX,
    IA_WARNING_THRESHOLD, ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_KB
)
from utils.embeds import ai_embed, error_embed, warning_embed, set_author
from utils.constants import Colors

logger = logging.getLogger("cog.ia")


class IA(commands.Cog):
    """Módulo de Inteligencia Artificial con Qwen."""

    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(
            api_key=API_QWEN,
            base_url=QWEN_BASE_URL,
        )
        # Historial de conversaciones por hilo
        self.thread_histories = {}

    # ─── Helpers ─────────────────────────────────────────────

    async def _check_limit(self, ctx, tipo: str, limit: int) -> bool:
        """Verifica si el usuario excedió su límite diario. Retorna True si puede continuar."""
        count = await self.bot.db.contar_uso_ia_hoy(ctx.author.id, tipo)
        remaining = limit - count

        if remaining <= 0:
            embed = warning_embed(
                "Límite alcanzado",
                f"Has alcanzado tu límite diario de **{limit}** usos de IA ({tipo}).\nSe reinicia a medianoche."
            )
            await ctx.send(embed=embed)
            return False

        if remaining <= IA_WARNING_THRESHOLD:
            await ctx.send(f"⚠️ Te quedan **{remaining}** análisis de {tipo} hoy.")

        return True

    async def _call_ai(self, messages: list, model: str = None) -> str:
        """Llama a la IA en un hilo separado para no bloquear."""
        model = model or QWEN_MODEL_TEXT
        loop = asyncio.get_event_loop()

        def _request():
            return self.client.chat.completions.create(
                model=model,
                messages=messages,
            )

        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _request),
                timeout=30.0
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            return "❌ La IA tardó demasiado en responder. Intenta de nuevo."
        except Exception as e:
            logger.error(f"Error IA: {e}")
            return f"❌ Error al conectar con la IA: {e}"

    async def _send_long_response(self, ctx, content: str, embed_title: str = None):
        """Envía respuestas largas divididas en partes, con embed para la primera."""
        if embed_title:
            if len(content) <= 4000:
                embed = ai_embed(embed_title, content)
                set_author(embed, ctx)
                await ctx.send(embed=embed)
                return

        # Dividir en partes de 1900 caracteres
        parts = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for i, part in enumerate(parts):
            if i == 0 and embed_title:
                embed = ai_embed(embed_title, part)
                set_author(embed, ctx)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"```\n{part}\n```" if "```" not in part else part)

    # ─── RF-IA-01: Chat con IA ──────────────────────────────

    @commands.hybrid_command(name="pregunta", description="Hazle una pregunta a la IA")
    @app_commands.describe(consulta="Tu pregunta o consulta")
    async def pregunta(self, ctx, *, consulta: str):
        await ctx.defer()

        await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "texto")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": consulta}
        ]
        answer = await self._call_ai(messages)
        await self._send_long_response(ctx, answer, "Respuesta IA")

    # ─── RF-IA-02: Análisis de imágenes ─────────────────────

    @commands.hybrid_command(name="iaver", description="Analiza una imagen adjunta con IA")
    @app_commands.describe(pregunta="Pregunta sobre la imagen (opcional)")
    async def ia_ver(self, ctx, *, pregunta: str = None):
        """Analiza una imagen adjunta. Solo se activa bajo demanda."""
        await ctx.defer()

        # Verificar límite
        if not await self._check_limit(ctx, "imagen", IA_LIMIT_IMAGE):
            return

        # Buscar imagen adjunta
        image_url = None
        if ctx.message.attachments:
            for att in ctx.message.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    image_url = att.url
                    break

        if not image_url:
            embed = error_embed("Sin imagen", "Adjunta una imagen al mensaje para que la IA la analice.")
            return await ctx.send(embed=embed)

        # Construir prompt
        user_prompt = pregunta or "Describe detalladamente lo que ves en esta imagen."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": user_prompt}
            ]}
        ]

        answer = await self._call_ai(messages, model=QWEN_MODEL_VISION)
        await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "imagen")
        await self._send_long_response(ctx, answer, "Análisis de Imagen")

    # ─── RF-IA-03: Lectura de archivos ──────────────────────

    @commands.hybrid_command(name="ialeer", description="Analiza un archivo de código adjunto con IA")
    @app_commands.describe(pregunta="Pregunta sobre el archivo (opcional)")
    async def ia_leer(self, ctx, *, pregunta: str = None):
        """Lee un archivo de texto/código adjunto y lo analiza."""
        await ctx.defer()

        if not await self._check_limit(ctx, "archivo", IA_LIMIT_FILE):
            return

        # Buscar archivo adjunto
        file_att = None
        if ctx.message.attachments:
            for att in ctx.message.attachments:
                ext = os.path.splitext(att.filename)[1].lower()
                if ext in ALLOWED_FILE_EXTENSIONS:
                    file_att = att
                    break

        if not file_att:
            exts = ", ".join(ALLOWED_FILE_EXTENSIONS[:8]) + "..."
            embed = error_embed(
                "Sin archivo válido",
                f"Adjunta un archivo de código o texto.\n**Formatos:** {exts}\n**Máx:** {MAX_FILE_SIZE_KB}KB"
            )
            return await ctx.send(embed=embed)

        # Verificar tamaño
        if file_att.size > MAX_FILE_SIZE_KB * 1024:
            embed = error_embed("Archivo muy grande", f"Máximo permitido: {MAX_FILE_SIZE_KB}KB. Tu archivo: {file_att.size // 1024}KB")
            return await ctx.send(embed=embed)

        # Leer contenido
        file_content = (await file_att.read()).decode("utf-8", errors="replace")
        ext = os.path.splitext(file_att.filename)[1].lstrip(".")

        if pregunta:
            user_msg = f"Archivo `{file_att.filename}`:\n```{ext}\n{file_content}\n```\n\nPregunta: {pregunta}"
        else:
            user_msg = f"Haz un code review detallado del siguiente archivo `{file_att.filename}`:\n```{ext}\n{file_content}\n```\n\nAnaliza: calidad, bugs potenciales, mejoras sugeridas, y da una puntuación del 1 al 10."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ]
        answer = await self._call_ai(messages)
        await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "archivo")
        await self._send_long_response(ctx, answer, f"Análisis: {file_att.filename}")

    # ─── RF-IA-04: Modo conversación por hilo ────────────────

    @commands.hybrid_command(name="iachat", description="Abre un hilo de conversación con la IA")
    async def ia_chat(self, ctx):
        """Crea un thread donde la IA mantiene contexto."""
        thread = await ctx.message.create_thread(
            name=f"💬 Chat IA — {ctx.author.display_name}",
            auto_archive_duration=30
        )
        self.thread_histories[thread.id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        embed = ai_embed(
            "Chat con IA iniciado",
            "Escribe tus mensajes en este hilo y la IA recordará el contexto.\n"
            "📝 La IA recuerda los últimos **10 mensajes**.\n"
            "⏰ El hilo se archiva tras 30 min de inactividad."
        )
        await thread.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Escucha mensajes en hilos de IA para mantener contexto."""
        if message.author.bot:
            return

        # Solo responder en hilos de chat IA
        if not isinstance(message.channel, discord.Thread):
            return
        if message.channel.id not in self.thread_histories:
            return

        async with message.channel.typing():
            history = self.thread_histories[message.channel.id]
            history.append({"role": "user", "content": message.content})

            # Mantener solo los últimos 10 mensajes + system prompt
            if len(history) > 21:  # 1 system + 20 (10 user + 10 assistant)
                history = [history[0]] + history[-20:]
                self.thread_histories[message.channel.id] = history

            answer = await self._call_ai(history)
            history.append({"role": "assistant", "content": answer})

            await self.bot.db.registrar_uso_ia(
                message.guild.id, message.author.id, "texto"
            )

            # Enviar respuesta
            if len(answer) > 2000:
                parts = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
                for part in parts:
                    await message.channel.send(part)
            else:
                await message.channel.send(answer)

    # ─── RF-IA-05: Code Review ───────────────────────────────

    @commands.hybrid_command(name="iareview", description="Haz un code review con IA")
    @app_commands.describe(codigo="El código a revisar")
    async def ia_review(self, ctx, *, codigo: str):
        """Analiza código pegado directamente."""
        await ctx.defer()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Haz un code review profesional del siguiente código:

```
{codigo}
```

Responde con este formato exacto:
## 📋 Resumen
(resumen breve)

## 🐛 Problemas encontrados
(lista de problemas)

## 💡 Sugerencias de mejora
(lista de sugerencias)

## ⭐ Puntuación: X/10
(justificación)"""}
        ]

        answer = await self._call_ai(messages)
        await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "texto")
        await self._send_long_response(ctx, answer, "Code Review")

    # ─── RF-IA-06: Generar documentación ─────────────────────

    @commands.hybrid_command(name="iadocs", description="Genera documentación para código")
    @app_commands.describe(codigo="El código a documentar")
    async def ia_docs(self, ctx, *, codigo: str):
        """Genera docstrings/JSDoc para el código proporcionado."""
        await ctx.defer()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Genera documentación completa (docstrings/JSDoc según el lenguaje) para el siguiente código. Devuelve el código con la documentación incluida:\n\n```\n{codigo}\n```"}
        ]

        answer = await self._call_ai(messages)
        await self.bot.db.registrar_uso_ia(ctx.guild.id, ctx.author.id, "texto")
        await self._send_long_response(ctx, answer, "Documentación Generada")

    # ─── RF-IA-07: Stats de uso ──────────────────────────────

    @commands.hybrid_command(name="iastats", description="Ver estadísticas de uso de la IA")
    async def ia_stats(self, ctx):
        """Muestra consumo de IA del usuario hoy."""
        stats = await self.bot.db.obtener_stats_ia(ctx.author.id)

        embed = ai_embed("Estadísticas de IA — Hoy")
        embed.description = f"Uso de IA de **{ctx.author.display_name}**:\n"

        tipo_limits = {
            "texto": ("💬 Texto", "∞"),
            "imagen": ("🖼️ Imágenes", str(IA_LIMIT_IMAGE)),
            "archivo": ("📄 Archivos", str(IA_LIMIT_FILE)),
            "mix": ("🎵 Mixes IA", str(IA_LIMIT_MIX)),
        }

        stats_dict = {row["tipo"]: row["count"] for row in stats} if stats else {}

        for tipo, (label, limit) in tipo_limits.items():
            used = stats_dict.get(tipo, 0)
            embed.add_field(name=label, value=f"`{used}` / `{limit}`", inline=True)

        set_author(embed, ctx)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(IA(bot))
