# YoRobot en asus

Sigue las convenciones de `/opt/apps/MANUAL.md` del servidor.

- Código y Compose: `/opt/apps/services/yorobot/`.
- Datos persistentes: `/opt/apps/data/yorobot/` (SQLite, cookies y log).
- Secretos: `/opt/apps/services/yorobot/.env`, permisos `600`.
- Contenedor sin privilegios: UID/GID `1000:1000`.
- Sin puertos publicados: Discord usa conexiones salientes.
- Reinicio automático: `unless-stopped`.

El archivo local `docker-compose.asus.yml` se copia al servidor con el nombre
`docker-compose.yml`. No combinarlo con el Compose local: es independiente.
El directorio de trabajo del contenedor es `/data` para persistir los archivos
que el bot abre por ruta relativa.

## Operación

```sh
ssh asus
cd /opt/apps/services/yorobot
sudo docker compose ps
sudo docker compose logs --tail=100 yorobot
sudo docker compose up -d --build
sudo docker compose stop
```

No sobrescribir la base de datos del servidor en futuras actualizaciones.
Las credenciales y cookies no se incluyen en la imagen Docker; `.dockerignore`
las excluye del contexto de construcción.

## Verificación en Discord

1. Invitar el bot con los scopes `bot` y `applications.commands`.
2. Permitir ver el canal, enviar mensajes, insertar enlaces, conectar y hablar.
3. El código actual solicita los intents privilegiados **Server Members** y
   **Message Content**: habilitar ambos en el Developer Portal.
4. Como dueño del bot, usar `!sync` en el servidor para registrar los comandos.
5. Entrar a un canal de voz y probar dos canciones con `/play`, el salto con
   `/skip` y la desconexión con `/stop`.

La prueba local del callback no sustituye una prueba real de voz en Discord.
YouTube puede bloquear la reproducción desde la IP del servidor; las cookies
pueden caducar o provocar HTTP 403. Por defecto no se usan cookies para canciones
públicas. Para activarlas explícitamente se puede definir `YOUTUBE_COOKIE_FILE`
en `.env`. El runtime Deno y los scripts EJS se instalan con las dependencias de
yt-dlp para soportar la extracción actual de YouTube.
La implementación actual comparte una sola cola y conexión de
voz, por lo que no soporta sesiones musicales simultáneas en varios servidores.
