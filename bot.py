import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os
import json
from flask import Flask
from threading import Thread

# 🌐 Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Bot Online 24/7!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- PERSISTÊNCIA DE DADOS ---
ARQUIVO_DADOS = "fila_dados.json"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r") as f:
            data = json.load(f)
            return data.get("fila_fazenda", []), data.get("fila_ids", [])
    return [], []

def salvar_dados():
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump({"fila_fazenda": fila_fazenda, "fila_ids": fila_ids}, f)

fila_fazenda, fila_ids = carregar_dados()

# --- CLASSES ---
class LembreteFilaView(View):
    def __init__(self, canal):
        super().__init__(timeout=None)
        self.canal = canal

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="btn_entrar_lembrete")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        global fila_fazenda, fila_ids
        if interaction.user.id not in fila_ids:
            fila_fazenda.append(interaction.user.display_name)
            fila_ids.append(interaction.user.id)
            salvar_dados()
            await interaction.response.send_message("✅ Você entrou na fila!", ephemeral=True)
            try: await interaction.message.delete()
            except: pass
            
            # Atualiza o Painel onde quer que ele esteja
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    async for message in channel.history(limit=100):
                        if message.author == bot.user and message.embeds and "FILA DA FAZENDA" in message.embeds[0].title:
                            await message.edit(content="||@here||", embed=PainelFilaView().gerar_embed(), view=PainelFilaView())
        else:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def gerar_embed(self):
        embed = discord.Embed(title="🌾 FILA DA FAZENDA GOMES GIRARDI 🌾", description="Clique nos botões abaixo!", color=discord.Color.brand_green())
        if fila_fazenda:
            lista = "\n".join([f"🥇 **{nome}** *(Próximo!)*" if i == 0 else f"{i+1}. {nome}" for i, nome in enumerate(fila_fazenda)])
            embed.add_field(name="Jogadores na Fila", value=lista, inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila.*", inline=False)
        embed.set_footer(text=f"Total: {len(fila_fazenda)}")
        return embed

    async def atualizar(self, interaction: discord.Interaction):
        salvar_dados()
        await interaction.response.edit_message(content="||@here||", embed=self.gerar_embed(), view=self)
        ping = await interaction.channel.send("||@here||")
        await asyncio.sleep(0.5)
        await ping.delete()

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id not in fila_ids:
            fila_fazenda.append(interaction.user.display_name)
            fila_ids.append(interaction.user.id)
            await self.atualizar(interaction)
        else: await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in fila_ids:
            idx = fila_ids.index(interaction.user.id)
            fila_fazenda.pop(idx); fila_ids.pop(idx)
            await self.atualizar(interaction)
        else: await interaction.response.send_message("⚠️ Você não está na fila!", ephemeral=True)

    @discord.ui.button(label="Liberar Vaga", style=discord.ButtonStyle.blurple, custom_id="liberar_vaga")
    async def avancar(self, interaction: discord.Interaction, button: Button):
        if not fila_fazenda: return await interaction.response.send_message("Fila vazia!", ephemeral=True)
        removido_nome = fila_fazenda.pop(0); removido_ids = fila_ids.pop(0)
        await self.atualizar(interaction)
        await interaction.followup.send(f"✅ Vaga de {removido_nome} liberada!", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    bot.add_view(LembreteFilaView(None))
    print(f"✅ {bot.user.name} online!")

@bot.event
async def on_guild_channel_create(channel):
    if "ticket-" in channel.name.lower():
        await asyncio.sleep(3)
        await channel.send(embed=discord.Embed(title="Fila da Fazenda", description="Clique abaixo para entrar:", color=discord.Color.green()), view=LembreteFilaView(channel))

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.message.delete()
    view = PainelFilaView()
    await ctx.send(content="||@here||", embed=view.gerar_embed(), view=view)

bot.run(os.environ['DISCORD_TOKEN'])
