import discord
from discord.ext import commands
import google.genai as genai
from google.genai import types
import os
import asyncio
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime

# --- TOKENS ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configura o Gemini
client_ai = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Você é a Makima, um bot para o servidor da kota. Você fala com calma, e mais direta. E fale de um jeito mais normal sem as respostas com muita coisa mas não muito curtas também"
    "não precisa ser formal, tenha respeito com todos os membros e converse com eles. "
    "Você é muito inteligente e educada. Seu criador é o Administrador gamer ali, e a criadora do servidor e a Kota."
    "Tente falar de um jeito mais direto e respostas medias ou curtas, sem ser grandes."
)

# IDs
CANAL_BOAS_VINDAS = 1476447063154757732
CARGO_REVIVER = 1429476218771869786
WEBHOOK_SAIDA = "https://discord.com/api/webhooks/1522392947071651943/jpS662kBWCjuUNAu81Aj8Z_ymsgvk7DTR5PkMB7my3fabJ065gGYWbLKBujh_0TWBco3"

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

def verificar_intencao(texto):
    resposta = client_ai.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[{"role": "user", "parts": [{"text": texto}]}],
        config=types.GenerateContentConfig(
            system_instruction="Você analisa se uma mensagem é um pedido para entrar em canal de voz, sair de canal de voz, ou nenhum dos dois. Responda APENAS com: ENTRAR, SAIR ou NADA.",
            temperature=0,
            max_output_tokens=10,
        )
    )
    return resposta.text.strip().upper()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot Makima online como {bot.user}!")
    await bot.change_presence(
        activity=discord.CustomActivity(name="Não sou grossa. So não me usem como parceira para crimes.")
    )

@bot.event
async def on_member_join(member):
    canal = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal:
        await canal.send(f"Olá {member.mention} Bem vindo(a) espero que goste do servidor se precisar de alguma coisa, estarei a disposição! <:emoji_32:1517687772754739250>")

@bot.event
async def on_member_remove(member):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_SAIDA, session=session)
        await webhook.send(f"**O Usuario {member.mention} saiu do servidor! Data e Hora da saida:** <t:{int(datetime.utcnow().timestamp())}:f>")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    mencionou = bot.user.mentioned_in(message)

    respondeu_ao_bot = False
    if message.reference is not None:
        try:
            ref = message.reference.resolved
            if ref is None:
                ref = await message.channel.fetch_message(message.reference.message_id)
            if ref is not None and ref.author == bot.user:
                respondeu_ao_bot = True
        except:
            pass

    cargo_mencionado = any(role.id == CARGO_REVIVER for role in message.role_mentions)

    if cargo_mencionado and not mencionou:
        await message.channel.send("Eai. Ativou o chat eu apareci!")
        return

    if not (mencionou or respondeu_ao_bot):
        return

    prompt = message.content
    for mention in message.mentions:
        if mention != bot.user:
            prompt = prompt.replace(mention.mention, f"@{mention.display_name}")
    prompt = prompt.replace(bot.user.mention, "").strip()

    if not prompt:
        prompt = "Olá!"

    # --- Gemini interpreta a intenção de call ---
    intencao = await asyncio.to_thread(verificar_intencao, prompt)

    if intencao == "ENTRAR":
        canal_voz = message.author.voice.channel if message.author.voice else None
        if canal_voz is None:
            await message.reply("Você precisa entrar em um canal de voz primeiro para eu poder ir.")
        else:
            try:
                if message.guild.voice_client is not None:
                    await message.guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(1)
                await canal_voz.connect(self_deaf=True)
                await message.reply(f"**Entrei na call {canal_voz.name}**")
            except Exception as e:
                print(f"Erro ao entrar na call: {e}")
                await message.reply(f"Erro ao entrar na call: {e}")
        return

    if intencao == "SAIR":
        if message.guild.voice_client is not None:
            await message.guild.voice_client.disconnect(force=True)
            await message.reply("**Saí da call**")
        else:
            await message.reply("Não estou em nenhum canal de voz.")
        return

    # Passa o nome de quem tá falando pro Gemini
    nome_autor = message.author.display_name
    prompt_com_contexto = f"[Quem está falando comigo agora: {nome_autor}]\n{prompt}"

    try:
        async with message.channel.typing():
            resposta = await asyncio.to_thread(
                perguntar_gemini, message.author.id, prompt_com_contexto
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
