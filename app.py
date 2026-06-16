import discord
from discord.ext import commands
import google.genai as genai
from google.genai import types
import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- TOKENS ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configura o Gemini
client_ai = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Você é a Makima, um bot para o servidor da kota. Você fala com calma, e mais direta "
    "não precisa ser formal, tenha respeito com todos os membros e converse com eles. "
    "Você é muito inteligente e educada. Seu criador é o Administrador gamer ali, "
    "e o criador do servidor é a Kota. Tente falar de um jeito mais direto e respostas medias ou curtas, sem ser grandes"
)

historico_usuarios = {}

def perguntar_gemini(usuario_id, prompt):
    if usuario_id not in historico_usuarios:
        historico_usuarios[usuario_id] = []

    historico_usuarios[usuario_id].append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    response = client_ai.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=historico_usuarios[usuario_id],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=1,
            max_output_tokens=2048,
        )
    )

    resposta_texto = response.text

    historico_usuarios[usuario_id].append({
        "role": "model",
        "parts": [{"text": resposta_texto}]
    })

    return resposta_texto

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot Makima online como {bot.user}!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    mencionou = bot.user.mentioned_in(message)
    respondeu_ao_bot = (
        message.reference is not None
        and message.reference.resolved is not None
        and message.reference.resolved.author == bot.user
    )

    if not (mencionou or respondeu_ao_bot):
        return

    prompt = message.content
    for mention in message.mentions:
        prompt = prompt.replace(mention.mention, "").strip()

    if not prompt:
        prompt = "Olá!"

    try:
        async with message.channel.typing():
            resposta = await asyncio.to_thread(
                perguntar_gemini, message.author.id, prompt
            )
        await message.reply(resposta)
    except Exception as e:
        print(f"❌ Erro: {e}")
        await message.reply("Ocorreu um erro, tenta de novo!")

    await bot.process_commands(message)

# Servidor HTTP simples pra satisfazer o Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Makima rodando!")
    def log_message(self, format, *args):
        pass

def rodar_servidor():
    porta = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", porta), Handler).serve_forever()

threading.Thread(target=rodar_servidor, daemon=True).start()

bot.run(DISCORD_TOKEN)
