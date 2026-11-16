import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from cogs.music import Music


class MusicPlaybackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = SimpleNamespace(registrar_reproduccion=AsyncMock())

    async def test_after_callback_advances_queue_from_audio_thread(self):
        # No connection to Discord, YouTube or Qwen is made by this test.
        with patch("cogs.music.OpenAI"):
            cog = Music(SimpleNamespace(db=self.db))  # Deliberately has no bot.loop.
        cog.queue = [{"query": "first", "requested_by": "tester", "requested_by_id": 42}]
        cog.voice_client = Mock()
        cog.voice_client.is_connected.return_value = True
        cog._search_youtube = AsyncMock(return_value={"url": "https://example.test/audio", "title": "first"})
        ctx = SimpleNamespace(send=AsyncMock(), guild=SimpleNamespace(id=1))

        with patch("cogs.music.discord.FFmpegOpusAudio.from_probe", new_callable=AsyncMock):
            await cog._play_next(ctx)
        self.db.registrar_reproduccion.assert_awaited_once_with(1, 42, "tester", "first", None, None)

        callback = cog.voice_client.play.call_args.kwargs["after"]
        advanced = asyncio.Event()

        async def next_song(context):
            self.assertIs(context, ctx)
            advanced.set()

        cog._play_next = AsyncMock(side_effect=next_song)
        thread = threading.Thread(target=callback, args=(None,))
        thread.start()
        await asyncio.wait_for(advanced.wait(), timeout=2)
        thread.join(timeout=2)
        cog._play_next.assert_awaited_once_with(ctx)

    async def test_queue_plays_second_song_then_starts_idle_timer(self):
        with patch("cogs.music.OpenAI"):
            cog = Music(SimpleNamespace(db=self.db))
        cog.queue = [{"query": "first"}, {"query": "second"}]
        cog.voice_client = Mock()
        cog.voice_client.is_connected.return_value = True
        cog._search_youtube = AsyncMock(side_effect=[
            {"url": "https://example.test/first", "title": "first"},
            {"url": "https://example.test/second", "title": "second"},
        ])
        ctx = SimpleNamespace(send=AsyncMock(), guild=SimpleNamespace(id=1))

        async def finish_track():
            callback = cog.voice_client.play.call_args.kwargs["after"]
            # Await the Future returned by the actual thread-safe scheduler.
            scheduled = []
            schedule = asyncio.run_coroutine_threadsafe

            def capture(coro, loop):
                future = schedule(coro, loop)
                scheduled.append(future)
                return future

            with patch("cogs.music.asyncio.run_coroutine_threadsafe", side_effect=capture):
                await asyncio.to_thread(callback, None)
            await asyncio.wrap_future(scheduled[0])

        try:
            with patch("cogs.music.discord.FFmpegOpusAudio.from_probe", new_callable=AsyncMock):
                await cog._play_next(ctx)
                self.assertEqual(cog.current_song["title"], "first")
                await finish_track()
                self.assertEqual(cog.current_song["title"], "second")
                self.assertEqual(cog.voice_client.play.call_count, 2)
                await finish_track()
            self.assertIsNone(cog.current_song)
            self.assertFalse(cog.is_playing)
            self.assertIsNotNone(cog.disconnect_task)
            self.assertEqual(self.db.registrar_reproduccion.await_count, 2)
        finally:
            task = cog.disconnect_task
            cog._cancel_disconnect()
            if task:
                await asyncio.gather(task, return_exceptions=True)

    async def test_history_failure_does_not_skip_playing_song(self):
        self.db.registrar_reproduccion.side_effect = RuntimeError("database unavailable")
        with patch("cogs.music.OpenAI"):
            cog = Music(SimpleNamespace(db=self.db))
        cog.queue = [{"query": "first"}, {"query": "second"}]
        cog.voice_client = Mock()
        cog.voice_client.is_connected.return_value = True
        cog._search_youtube = AsyncMock(return_value={"url": "https://example.test/audio", "title": "first"})
        ctx = SimpleNamespace(send=AsyncMock(), guild=SimpleNamespace(id=1))
        with patch("cogs.music.discord.FFmpegOpusAudio.from_probe", new_callable=AsyncMock):
            with self.assertLogs("cog.music", level="ERROR"):
                await cog._play_next(ctx)
        self.assertEqual(cog.voice_client.play.call_count, 1)
        self.assertEqual(len(cog.queue), 1)
        self.assertEqual(cog.current_song["title"], "first")

    async def test_failed_playback_is_not_recorded(self):
        with patch("cogs.music.OpenAI"):
            cog = Music(SimpleNamespace(db=self.db))
        cog.queue = [{"query": "first"}]
        cog.voice_client = Mock()
        cog.voice_client.is_connected.return_value = True
        cog._search_youtube = AsyncMock(return_value={"url": "https://example.test/audio", "title": "first"})
        ctx = SimpleNamespace(send=AsyncMock(), guild=SimpleNamespace(id=1))
        try:
            with patch("cogs.music.discord.FFmpegOpusAudio.from_probe", new_callable=AsyncMock) as probe:
                probe.side_effect = RuntimeError("FFmpeg unavailable")
                with self.assertLogs("cog.music", level="ERROR"):
                    await cog._play_next(ctx)
            self.db.registrar_reproduccion.assert_not_awaited()
        finally:
            task = cog.disconnect_task
            cog._cancel_disconnect()
            if task:
                await asyncio.gather(task, return_exceptions=True)

    async def test_historial_uses_current_guild_and_limits_display(self):
        self.db.obtener_historial_musica = AsyncMock(return_value=[{
            "titulo": "Song", "solicitado_por": "tester", "fecha": "2026-10-19 00:00:00",
        } for _ in range(11)])
        with patch("cogs.music.OpenAI"):
            cog = Music(SimpleNamespace(db=self.db))
        ctx = SimpleNamespace(send=AsyncMock(), defer=AsyncMock(), guild=SimpleNamespace(id=9))
        await Music.historial.callback(cog, ctx, pagina=2)
        self.db.obtener_historial_musica.assert_awaited_once_with(9, 2)
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertEqual(embed.description.count("Song"), 10)
        self.assertIn("pagina:3", embed.footer.text)
        ctx.send.reset_mock()
        self.db.obtener_historial_musica.reset_mock()
        await Music.historial.callback(cog, ctx, pagina=0)
        self.db.obtener_historial_musica.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
