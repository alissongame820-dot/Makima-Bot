import discord
from discord.ext import commands
from google import genai
import os
import asyncio

# Puxando os tokens de forma segura direto do servidor da Koyeb
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inicializa o cliente moderno do Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

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

    # Responde quando for mencionado
    if bot.user.mentioned_in(message):
        try:
            # Limpa as menções do texto
            prompt = message.content
            for mention in message.mentions:
                prompt = prompt.replace(mention.mention, "")
            prompt = prompt.strip()
            
            if not prompt:
                prompt = "Olá!"

            # Chamada moderna usando o modelo Flash Lite super rápido
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=(
                        "Você é a Makima, um bot para o servidor da kota. Você fala com calma, "
                        "não precisa ser formal, tenha respeito com todos os membros e converse com eles. "
                        "Você é muito inteligente e educada. Seu criador é o Administrador gamer ali, "
                        "e o criador do servidor é a Kota. Tente falar de um jeito mais normal."
                    ),
                    temperature=1.0,
                    max_output_tokens=2048
                )
            )
            
            await message.reply(response.text)
            
        except Exception as e:
            print(f"❌ Erro ao gerar resposta no Gemini: {e}")

async def main():
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Erro crítico no bot do Discord: {e}")

if __name__ == "__main__":
    asyncio.run(main())
