import discord
from discord.ext import commands
import os
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime

# --- TOKENS ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# IDs
CANAL_BOAS_VINDAS = 1476447063154757732
WEBHOOK_SAIDA = "https://discord.com/api/webhooks/1522392947071651943/jpS662kBWCjuUNAu81Aj8Z_ymsgvk7DTR5PkMB7my3fabJ065gGYWbLKBujh_0TWBco3"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot Makima online como {bot.user}!")
    await bot.change_presence(
        activity=discord.CustomActivity(name="Apenas fazendo meu trabalho. ")
    )

@bot.event
async def on_member_join(member):
    canal = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal:
        await canal.send(f"Olá {member.mention} Bem vindo(a) espero que goste do servidor <:emoji_32:1517687772754739250>")

@bot.event
async def on_member_remove(member):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_SAIDA, session=session)
        await webhook.send(f"**O Usuario {member.display_name} saiu do servidor! Data e Hora da saida:** <t:{int(datetime.utcnow().timestamp())}:f>")

# Servidor HTTP simples pra satisfazer o Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot Makima rodando!")
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
    def log_message(self, format, *args):
        pass

def rodar_servidor():
    porta = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", porta), Handler).serve_forever()

threading.Thread(target=rodar_servidor, daemon=True).start()

bot.run(DISCORD_TOKEN)
