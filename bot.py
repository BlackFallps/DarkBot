import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os
from flask import Flask
from threading import Thread

# Configuração Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Bot Online 24/7!"
def run(): app.run(host='0.0.0.0', port=8080)
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

fila_fazenda = []

class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def gerar_embed(self):
        embed = discord.Embed(
            title="🚜 FILA DA FAZENDA GOMES GIRARDI 🌾",
            description="Clique nos botões abaixo para gerenciar sua vaga na fila!",
            color=discord.Color.brand_green()
        )
        embed.set_thumbnail(url="https://r2.fivemanage.com/W9vFnvRHli5f57dMM8AKy/FazendaGomes.png")
        
        if fila_fazenda:
            lista_nomes = "\n".join([f"🥇 **{nome}** *(Próximo!)*" if i == 0 else f"{i+1}. {nome}" for i, nome in enumerate(fila_fazenda)])
            embed.add_field(name="Jogadores na Fila", value=lista_nomes, inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila por enquanto.*", inline=False)
        
        embed.set_footer(text=f"Total: {len(fila_fazenda)}")
        return embed

    async def atualizar(self, interaction: discord.Interaction):
        # Edita a mensagem do painel
        await interaction.response.edit_message(content="||@here||", embed=self.gerar_embed(), view=self)
        
        # Envia um ping fantasma para garantir a notificação
        ping = await interaction.channel.send("||@here||")
        await asyncio.sleep(0.5)
        await ping.delete()

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        usuario = interaction.user.display_name
        if usuario in fila_fazenda:
            await interaction.response.send_message(f"⚠️ Você já está na fila, {usuario}!", ephemeral=True)
        else:
            fila_fazenda.append(usuario)
            await self.atualizar(interaction)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        usuario = interaction.user.display_name
        if usuario in fila_fazenda:
            fila_fazenda.remove(usuario)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Você não está na fila!", ephemeral=True)

    @discord.ui.button(label="Avançar Fila (Mod)", style=discord.ButtonStyle.blurple, custom_id="avancar_fila")
    async def avancar(self, interaction: discord.Interaction, button: Button):
        if fila_fazenda:
            removido = fila_fazenda.pop(0)
            await self.atualizar(interaction)
            await interaction.channel.send(f"🔔 **{removido}**, sua vaga na fazenda liberou!")
        else:
            await interaction.response.send_message("A fila está vazia!", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.message.delete()
    view = PainelFilaView()
    await ctx.send(content="||@here||", embed=view.gerar_embed(), view=view)

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    print(f"✅ {bot.user.name} online!")

bot.run(os.environ['DISCORD_TOKEN'])
