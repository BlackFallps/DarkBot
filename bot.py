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

fila_fazenda = []

# --- Interface do Painel ---
class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def gerar_embed(self):
        embed = discord.Embed(
            title="🚜 FILA DA FAZENDA GOMES GIRARDI 🌾",
            description="Clique nos botões abaixo para gerenciar sua vaga!",
            color=discord.Color.brand_green()
        )
        embed.set_thumbnail(url="https://r2.fivemanage.com/W9vFnvRHli5f57dMM8AKy/FazendaGomes.png")

        if fila_fazenda:
            lista_nomes = "\n".join([f"🥇 **{m}** *(Próximo!)*" if i == 0 else f"{i+1}. {m}" for i, m in enumerate(fila_fazenda)])
            embed.add_field(name="Jogadores na Fila", value=lista_nomes, inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila.*", inline=False)
        embed.set_footer(text=f"Total: {len(fila_fazenda)}")
        return embed

    async def atualizar(self, interaction):
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.mention not in fila_fazenda:
            fila_fazenda.append(interaction.user.mention)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        if interaction.user.mention in fila_fazenda:
            fila_fazenda.remove(interaction.user.mention)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Você não está na fila!", ephemeral=True)

    @discord.ui.button(label="Liberar Vaga", style=discord.ButtonStyle.blurple, custom_id="liberar_vaga")
    async def liberar(self, interaction: discord.Interaction, button: Button):
        if not fila_fazenda: return await interaction.response.send_message("A fila está vazia!", ephemeral=True)
        removido = fila_fazenda.pop(0)
        await self.atualizar(interaction)
        await interaction.followup.send(f"✅ Vaga liberada para {removido}!", ephemeral=True)

# --- Botão dos Tickets ---
class TicketBotaoView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Garantir minha vaga", style=discord.ButtonStyle.green, custom_id="ticket_entrar")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.mention not in fila_fazenda:
            fila_fazenda.append(interaction.user.mention)
            await interaction.response.send_message("✅ Adicionado à fila!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

@bot.event
async def on_guild_channel_create(channel):
    if "ticket-" in channel.name.lower():
        await asyncio.sleep(2)
        await channel.send("**Bem-vindo à Fazenda!**", view=TicketBotaoView())

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.message.delete()
    view = PainelFilaView()
    await ctx.send(embed=view.gerar_embed(), view=view)

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    bot.add_view(TicketBotaoView())
    print(f"✅ {bot.user.name} online!")

bot.run(os.environ['DISCORD_TOKEN'])
