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
CARGOS_PERMITIDOS = [1465117225672249487, 1509877190995476610, 1281476884131090467]

fila_jogadores = []

# --- View com o botão de LINK ---
class BotaoLinkView(View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Ir para o Painel", style=discord.ButtonStyle.link, url=url))

# --- Classe do Painel ---
class PainelFilaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def gerar_embed(self):
        embed = discord.Embed(
            title="🌾 FILA DA FAZENDA GOMES GIRARDI 🌾",
            description="Clique nos botões abaixo para gerenciar sua vaga na fila!",
            color=discord.Color.brand_green()
        )
        embed.set_thumbnail(url="https://r2.fivemanage.com/W9vFnvRHli5f57dMM8AKy/FazendaGomes.png")
        
        if fila_jogadores:
            lista_formatada = []
            for i, jogador in enumerate(fila_jogadores):
                mention = f"<@{jogador['id']}>"
                if i == 0:
                    lista_formatada.append(f"🥇 **{mention}** *(Próximo a Ser Contratado)*")
                else:
                    lista_formatada.append(f"{i+1}. {mention}")
            embed.add_field(name="Jogadores na Fila", value="\n".join(lista_formatada), inline=False)
        else:
            embed.add_field(name="Jogadores na Fila", value="*Ninguém na fila por enquanto.*", inline=False)
        embed.set_footer(text=f"Total: {len(fila_jogadores)}")
        return embed

    async def atualizar(self, interaction):
        # Editamos a mensagem do painel e limpamos os pings desnecessários
        await interaction.response.edit_message(content="||@here||", embed=self.gerar_embed(), view=self)

    # --- BOTÃO: ENTRAR NA FILA ---
    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green, custom_id="entrar_fila")
    async def entrar(self, interaction: discord.Interaction, button: Button):
        if not any(j['id'] == interaction.user.id for j in fila_jogadores):
            fila_jogadores.append({'id': interaction.user.id})
            await interaction.response.send_message("✅ Você entrou na fila!", ephemeral=True)
            await self.atualizar(interaction)
        else:
            await interaction.response.send_message("⚠️ Você já está na fila!", ephemeral=True)
            
    # --- BOTÃO: SAIR DA FILA ---
    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red, custom_id="sair_fila")
    async def sair(self, interaction: discord.Interaction, button: Button):
        global fila_jogadores
        fila_jogadores = [j for j in fila_jogadores if j['id'] != interaction.user.id]
        await self.atualizar(interaction)
        await interaction.response.send_message("Você saiu da fila!", ephemeral=True)

    # --- BOTÃO: LIBERAR VAGA ---
    @discord.ui.button(label="Liberar Vaga 1° da Fila", style=discord.ButtonStyle.blurple, custom_id="liberar_vaga")
    async def avancar(self, interaction: discord.Interaction, button: Button):
        # Verifica se quem clicou tem cargo
        if not any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles):
            return await interaction.response.send_message("❌ Apenas Gerentes ou Donos podem liberar a vaga!", ephemeral=True)
        
        if not fila_jogadores:
            return await interaction.response.send_message("A fila está vazia!", ephemeral=True)
        
        # Remove jogador
        jogador = fila_jogadores.pop(0)
        await self.atualizar(interaction)
        
        # Resposta de sucesso para o gerente
        await interaction.response.send_message(f"✅ Vaga de <@{jogador['id']}> liberada!", ephemeral=True)
        
        # Tenta enviar DM para o jogador
        try:
            membro = interaction.guild.get_member(jogador['id'])
            if membro:
                await membro.send("✅ **Sua Vaga na Fazenda Gomes Girardi foi liberada!** Procure os Gerentes ou os Donos no Condado para ser contratado.")
        except:
            print("Não foi possível enviar DM para o jogador.")

# --- Eventos ---
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
