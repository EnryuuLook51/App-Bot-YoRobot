import tempfile
import sqlite3
import unittest
from pathlib import Path

from database import Database


class MusicHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "bot.db")
        self.db = Database(self.path)
        await self.db.init()

    async def test_history_persists_and_is_isolated_by_guild(self):
        await self.db.registrar_reproduccion(1, 42, "tester", "Song", "https://youtube.com/watch?v=test", 100)
        await self.db.registrar_reproduccion(2, 43, "other", "Private song")
        reopened = Database(self.path)
        await reopened.init()  # Schema creation remains idempotent.
        rows = await reopened.obtener_historial_musica(1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["titulo"], "Song")
        self.assertEqual(rows[0]["user_id"], 42)
        self.assertEqual(rows[0]["duracion"], 100)
        self.assertTrue(rows[0]["fecha"])

    async def test_newest_first_and_paginated(self):
        for i in range(12):
            await self.db.registrar_reproduccion(1, 42, "tester", f"Song {i}")
        first = await self.db.obtener_historial_musica(1)
        second = await self.db.obtener_historial_musica(1, pagina=2)
        self.assertEqual(len(first), 11)  # Extra row signals the next page.
        self.assertEqual(first[0]["titulo"], "Song 11")
        self.assertEqual([r["titulo"] for r in second], ["Song 1", "Song 0"])
        self.assertEqual(await self.db.obtener_historial_musica(2), [])
        with self.assertRaises(ValueError):
            await self.db.obtener_historial_musica(1, pagina=0)

    async def test_random_mix_has_ten_unique_songs_and_is_saved(self):
        for i in range(15):
            await self.db.registrar_reproduccion(1, 42, "tester", f"Song {i}", f"https://youtube.com/watch?v={i}")
        for _ in range(20):
            await self.db.registrar_reproduccion(1, 42, "tester", "Song 0", "https://youtube.com/watch?v=0")
        await self.db.registrar_reproduccion(2, 42, "tester", "Other server")
        songs = await self.db.crear_mix_aleatorio(1, 42, "Random", 10)
        self.assertEqual(len(songs), 10)
        self.assertEqual(len({s["titulo"] for s in songs}), 10)
        self.assertNotIn("Other server", [s["titulo"] for s in songs])
        mix = await self.db.obtener_mix_por_nombre(1, 42, "Random")
        saved = await self.db.obtener_canciones_mix(mix["id"])
        self.assertEqual([r["titulo"] for r in saved], [s["titulo"] for s in songs])
        self.assertEqual([r["posicion"] for r in saved], list(range(1, 11)))

    async def test_random_mix_empty_small_history_and_errors(self):
        self.assertEqual(await self.db.crear_mix_aleatorio(1, 42, "Empty", 10), [])
        self.assertEqual(await self.db.contar_mixes(1, 42), 0)
        for title in ["Song", "song", " Song ", "Another"]:
            await self.db.registrar_reproduccion(1, 42, "tester", title)
        songs = await self.db.crear_mix_aleatorio(1, 42, "Small", 10)
        self.assertEqual(len(songs), 2)
        with self.assertRaises(sqlite3.IntegrityError):
            await self.db.crear_mix_aleatorio(1, 42, "Small", 10)
        with self.assertRaises(ValueError):
            await self.db.crear_mix_aleatorio(1, 42, "Over limit", 1)
        self.assertEqual(await self.db.contar_mixes(1, 42), 1)
