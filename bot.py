import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os
from flask import Flask
from threading import Thread

# 🌐 Configuração do Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Bot Online 24/7!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONFIGURAÇÃO ---
ID_CANAL_PAINEL = 1477880103039144127

# --- View com o botão de LINK (Para a mensagem da imagem) ---
class BotaoLinkView(View):
    def __init__(self, url):
        super().__init__(timeout=None)
        # Botão conforme solicitado em image_66ae3e.png
        self.add_item(discord.ui.Button(label="Ir para o Painel", style=discord.ButtonStyle.link, url=url))

# --- Classe do Painel ---
class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    # ... (Mantenha aqui todo o seu código original de gerar_embed, entrar, sair, avançar) ...
    # (O código das funções entrar, sair e avancar permanece igual ao que você já tem)

# --- EVENTO DE CRIAÇÃO DE CANAL ---
@bot.event
async def on_guild_channel_create(channel):
    if "ticket-" in channel.name.lower():
        await asyncio.sleep(5) # Tempo para garantir que o bot processe o canal
        
        url = f"https://discord.com/channels/{channel.guild.id}/{ID_CANAL_PAINEL}"
        
        # Embed solicitado em image_66ae3e.png
        embed = discord.Embed(
            title="Fila da Fazenda Gomes Girardi",
            description="Olá! Notamos que abriu uma Pasta. Para mantermos a ordem na Fazenda, trabalhamos com uma fila de espera. Clique no Botão Abaixo para ir direto pro Painel.",
            color=discord.Color.brand_green()
        )
        
        # Envia apenas a mensagem da imagem
        await channel.send(embed=embed, view=BotaoLinkView(url))

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    print(f"✅ {bot.user.name} online!")

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.message.delete()
    view = PainelFilaView()
    await ctx.send(content="||@here||", embed=view.gerar_embed(), view=view)

bot.run(os.environ['DISCORD_TOKEN'])
