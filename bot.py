import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os
import json
from flask import Flask
from threading import Thread

# 🌐 Configuração Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Bot Online 24/7!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- PERSISTÊNCIA ---
FILE_NAME = "fila_dados.json"

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f: return json.load(f)
    return {"fila": [], "ids": []}

def save_data(data):
    with open(FILE_NAME, "w") as f: json.dump(data, f)

# --- PAINEL PRINCIPAL ---
class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_embed(self):
        data = load_data()
        embed = discord.Embed(title="🌾 FILA DA FAZENDA GOMES GIRARDI 🌾", color=discord.Color.brand_green())
        if data["fila"]:
            lista = "\n".join([f"🥇 **{nome}**" if i == 0 else f"{i+1}. {nome}" for i, nome in enumerate(data["fila"])])
            embed.add_field(name="Jogadores na Fila", value=lista, inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila.*", inline=False)
        embed.set_footer(text=f"Total: {len(data['fila'])}")
        return embed

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        if interaction.user.id not in data["ids"]:
            data["fila"].append(interaction.user.display_name)
            data["ids"].append(interaction.user.id)
            save_data(data)
            await interaction.response.edit_message(content="||@here||", embed=self.get_embed(), view=self)
        else: await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        if interaction.user.id in data["ids"]:
            idx = data["ids"].index(interaction.user.id)
            data["fila"].pop(idx); data["ids"].pop(idx)
            save_data(data)
            await interaction.response.edit_message(content="||@here||", embed=self.get_embed(), view=self)
        else: await interaction.response.send_message("⚠️ Você não está na fila!", ephemeral=True)

# --- LEMBRETE NO TICKET ---
class LembreteFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="btn_entrar_lembrete")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        if interaction.user.id not in data["ids"]:
            data["fila"].append(interaction.user.display_name)
            data["ids"].append(interaction.user.id)
            save_data(data)
            await interaction.response.send_message("✅ Você entrou na fila!", ephemeral=True)
            try: await interaction.message.delete()
            except: pass
        else: await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    bot.add_view(LembreteFilaView())
    print(f"✅ {bot.user.name} online!")

@bot.event
async def on_guild_channel_create(channel):
    if "ticket-" in channel.name.lower():
        await asyncio.sleep(3)
        await channel.send("Clique para entrar na fila da Fazenda:", view=LembreteFilaView())

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.message.delete()
    view = PainelFilaView()
    await ctx.send(content="||@here||", embed=view.get_embed(), view=view)

bot.run(os.environ['DISCORD_TOKEN'])
