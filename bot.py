import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Online 24/7!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Listas globais
fila_fazenda = []
fila_ids = []

# --- Função Auxiliar para atualizar ONDE quer que o painel esteja ---
async def atualizar_painel_global():
    # Procura em todos os canais por uma mensagem que tenha o título do painel
    for guild in bot.guilds:
        for channel in guild.text_channels:
            async for message in channel.history(limit=100):
                if message.author == bot.user and "🚜 FILA DA FAZENDA" in str(message.embeds):
                    await message.edit(embed=PainelFilaView().gerar_embed(), view=PainelFilaView())

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
            await interaction.response.send_message("✅ Você entrou na fila!", ephemeral=True)
            try: await interaction.message.delete()
            except: pass
            # Atualiza o painel principal em qualquer lugar que ele esteja
            await atualizar_painel_global()
        else:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)

class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def gerar_embed(self):
        embed = discord.Embed(
            title="🚜 FILA DA FAZENDA GOMES GIRARDI 🌾",
            description="Clique nos botões abaixo para gerenciar sua vaga na fila!",
            color=discord.Color.brand_green()
        )
        if fila_fazenda:
            lista = "\n".join([f"🥇 **{nome}**" if i == 0 else f"{i+1}. {nome}" for i, nome in enumerate(fila_fazenda)])
            embed.add_field(name="Jogadores na Fila", value=lista, inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila.*", inline=False)
        embed.set_footer(text=f"Total: {len(fila_fazenda)}")
        return embed

    async def atualizar(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id not in fila_ids:
            fila_fazenda.append(interaction.user.display_name)
            fila_ids.append(interaction.user.id)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Já está na fila!", ephemeral=True)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in fila_ids:
            idx = fila_ids.index(interaction.user.id)
            fila_fazenda.pop(idx); fila_ids.pop(idx)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Não está na fila!", ephemeral=True)

    @discord.ui.button(label="Liberar Vaga", style=discord.ButtonStyle.blurple, custom_id="liberar_vaga")
    async def avancar(self, interaction: discord.Interaction, button: Button):
        if not fila_fazenda: return await interaction.response.send_message("Vazia!", ephemeral=True)
        removido_nome = fila_fazenda.pop(0); fila_ids.pop(0)
        await self.atualizar(interaction)
        member = interaction.guild.get_member(fila_ids[0] if fila_ids else 0) # Simplificado
        # ... (restante da lógica de busca do canal mantida)
        await interaction.response.send_message(f"✅ Vaga de {removido_nome} liberada!", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(PainelFilaView())
    bot.add_view(LembreteFilaView(None))
    print(f"✅ {bot.user.name} online!")

@bot.event
async def on_guild_channel_create(channel):
    if "ticket-" in channel.name.lower():
        await asyncio.sleep(3)
        embed = discord.Embed(title="🚜 Fila da Fazenda", description="Entre na fila clicando no botão abaixo!", color=discord.Color.green())
        await channel.send(embed=embed, view=LembreteFilaView(channel))

@bot.command()
@commands.has_permissions(administrator=True)
async def fixarpainel(ctx):
    await ctx.send(embed=PainelFilaView().gerar_embed(), view=PainelFilaView())

bot.run(os.environ['DISCORD_TOKEN'])
