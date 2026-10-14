import discord
import os
import json
import asyncio
import aiohttp
from discord.ext import commands, tasks
from dotenv import load_dotenv
import feedparser
from bs4 import BeautifulSoup
import quotes
import time
import re

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configurar intenções
intents = discord.Intents.default()
intents.members = True # Necessário para detectar novos membros
try:
    intents.message_content = True 
except AttributeError:
    print("Aviso: intent message_content não disponível nesta versão do discord.py")

# Inicializar o Bot
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'--- Deckard Cain chegou em Santuário ---')
    print(f'Logado como: {bot.user.name} ({bot.user.id})')
    print(f'Conectado a {len(bot.guilds)} servidores:')
    for guild in bot.guilds:
        print(f' - {guild.name} ({guild.id})')
    print(f'---------------------------------------------')
    
    # Registrar views persistentes
    bot.add_view(RoleView())
    bot.add_view(RulesView())
    bot.add_view(SupportView())
    bot.add_view(TicketControlView())
    bot.add_view(GroupAnnouncementView())
    bot.add_view(ClassRoleView())

    # Iniciar tarefas de segundo plano
    if not monitor_builds.is_running():
        monitor_builds.start()
    
    if not monitor_news.is_running():
        monitor_news.start()

    if not monitor_events.is_running():
        monitor_events.start()
    
    await bot.change_presence(activity=discord.Game(name="Diablo IV: Vessel of Hatred"))

@bot.event
async def on_guild_join(guild):
    print(f'!!! Entrou em um novo servidor: {guild.name} ({guild.id})')
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Fique um pouco e ouça! Eu sou Deckard Cain, e cheguei para auxiliar em sua jornada por Santuário.")
            break

# --- Monitor de Builds Novas ---

CACHE_FILE = "builds_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

@tasks.loop(minutes=30)
async def monitor_builds():
    await bot.wait_until_ready()
    print("--- Iniciando monitoramento de builds (S13 / Lord of Hatred) ---")
    
    guild = discord.utils.get(bot.guilds, id=1086783767278014495)
    if not guild:
        return
        
    target_channel = discord.utils.get(guild.text_channels, name="builds-novas")
    if not target_channel:
        target_channel = next((c for c in guild.text_channels if "builds" in c.name.lower()), None)
    
    if not target_channel:
        print("Erro: Canal #builds-novas não encontrado.")
        return

    cache = load_cache()
    new_builds_found = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. D4Builds.gg
        try:
            print("Scrape: D4Builds.gg (JSON Extraction)...")
            async with session.get("https://d4builds.gg/builds/", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        data = json.loads(script.string)
                        # O caminho exato pode variar, mas geralmente está em pageProps
                        page_props = data.get("props", {}).get("pageProps", {})
                        builds = page_props.get("builds", []) or page_props.get("initialBuilds", [])
                        
                        for b in builds:
                            slug = b.get("slug")
                            if not slug: continue
                            full_url = f"https://d4builds.gg/builds/{slug}/"
                            if full_url in cache: continue

                            build_name = b.get("title", "Nova Build")
                            # Filtro S13
                            season = str(b.get("season", ""))
                            is_s13 = "13" in season or any(x in build_name.upper() for x in ["S13", "RECKONING", "HATRED"])
                            
                            if is_s13:
                                detected_class = detect_class(build_name, full_url)
                                await send_build_notification(target_channel, build_name, full_url, "D4Builds.gg", detected_class, guild)
                                cache.append(full_url)
                                new_builds_found += 1
                                if new_builds_found >= 15: break
        except Exception as e:
            print(f"Erro D4Builds (JSON): {e}")

        # 2. Maxroll.gg
        try:
            print("Scrape: Maxroll.gg (JSON Extraction)...")
            async with session.get("https://maxroll.gg/d4/build-guides", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    script = soup.find("script", id="__NEXT_DATA__")
                    if script:
                        data = json.loads(script.string)
                        page_props = data.get("props", {}).get("pageProps", {})
                        guides = page_props.get("guides", []) or page_props.get("allGuides", [])
                        
                        for g in guides:
                            slug = g.get("slug")
                            if not slug: continue
                            full_url = f"https://maxroll.gg/d4/build-guides/{slug}"
                            if full_url in cache: continue

                            build_name = g.get("title", "Nova Build")
                            
                            if any(x in build_name.upper() for x in ["S13", "SEASON 13", "RECKONING", "HATRED", "WARLOCK", "BRUXO"]):
                                detected_class = detect_class(build_name, full_url)
                                await send_build_notification(target_channel, build_name, full_url, "Maxroll.gg", detected_class, guild)
                                cache.append(full_url)
                                new_builds_found += 1
                                if new_builds_found >= 15: break
        except Exception as e:
            print(f"Erro Maxroll (JSON): {e}")

        # 3. Icy-Veins.com (HTML Extraction - Still reliable here)
        try:
            print("Scrape: Icy-Veins.com...")
            async with session.get("https://www.icy-veins.com/d4/guides/class-builds/", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    for card in soup.select('a[class*="guideCard"]'):
                        full_url = card.get("href")
                        if not full_url: continue
                        if not full_url.startswith("http"): full_url = f"https://www.icy-veins.com{full_url}"
                        if full_url in cache: continue
                        
                        build_name = card.get_text(strip=True)
                        
                        if any(x in build_name.upper() for x in ["SEASON 13", "S13", "HATRED", "RECKONING", "WARLOCK", "BRUXO"]):
                            detected_class = detect_class(build_name, full_url)
                            await send_build_notification(target_channel, build_name, full_url, "Icy Veins", detected_class, guild)
                            cache.append(full_url)
                            new_builds_found += 1
                            if new_builds_found >= 10: break
        except Exception as e:
            print(f"Erro Icy Veins: {e}")

        # 4. Mobalytics.gg
        try:
            print("Scrape: Mobalytics.gg...")
            async with session.get("https://mobalytics.gg/diablo-4/builds", timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    links = set()
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('/diablo-4/builds/') and href != '/diablo-4/builds/':
                            links.add(href)
                            
                    for href in list(links):
                        slug = href.split('/')[-1]
                        build_name = " ".join(word.capitalize() for word in slug.split("-"))
                        full_url = f"https://mobalytics.gg{href}"
                        if full_url in cache: continue
                        
                        if any(x in build_name.upper() for x in ["SEASON 13", "S13", "HATRED", "RECKONING", "WARLOCK", "BRUXO"]):
                            detected_class = detect_class(build_name, full_url)
                            await send_build_notification(target_channel, build_name, full_url, "Mobalytics", detected_class, guild)
                            cache.append(full_url)
                            new_builds_found += 1
                            if new_builds_found >= 10: break
        except Exception as e:
            print(f"Erro Mobalytics: {e}")

    if new_builds_found > 0:
        save_cache(cache[-500:])
    print(f"Monitoramento concluído. {new_builds_found} novas builds postadas.")

async def send_build_notification(channel, name, url, source, d_class, guild):
    mention = ""
    color = discord.Color.green()
    
    if d_class:
        role = discord.utils.get(guild.roles, name=d_class)
        if role:
            mention = role.mention
        
        if d_class == "Bruxo":
            color = discord.Color.from_rgb(148, 0, 211) # Dark Violet

    embed = discord.Embed(
        title=f"🔥 Nova Build: {name}",
        description=f"Uma nova build foi catalogada no portal **{source}**!",
        url=url,
        color=color
    )
    
    if d_class:
        embed.add_field(name="🛡️ Classe", value=d_class, inline=True)
    
    embed.add_field(name="🔗 Fonte", value=source, inline=True)
    embed.add_field(name="📖 Link", value=f"[Ver Build no {source}]({url})", inline=False)
    
    if any(x in name.upper() for x in ["HATRED", "S13", "RECKONING"]):
        embed.set_footer(text="Temporada 13 - Lord of Hatred")
    else:
        embed.set_footer(text="Deckard Cain Build Watcher")

    await channel.send(content=mention, embed=embed)
    await asyncio.sleep(2)

# --- Monitor de Notícias ---

NEWS_CACHE_FILE = "news_cache.json"

def load_news_cache():
    if os.path.exists(NEWS_CACHE_FILE):
        with open(NEWS_CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def save_news_cache(cache):
    with open(NEWS_CACHE_FILE, "w") as f:
        json.dump(cache, f)

@tasks.loop(minutes=30)
async def monitor_news():
    await bot.wait_until_ready()
    print("--- Iniciando monitoramento de notícias ---")
    
    guild = discord.utils.get(bot.guilds, id=1086783767278014495)
    if not guild: return
    
    target_channel = discord.utils.get(guild.text_channels, name="noticias")
    if not target_channel:
        target_channel = next((c for c in guild.text_channels if "noticia" in c.name.lower()), None)
    
    if not target_channel:
        print("Erro: Canal #noticias não encontrado.")
        return

    cache = load_news_cache()
    new_news_found = 0

    feeds = [
        ("Blizzard (Oficial)", "https://news.blizzard.com/pt-br/feed/diablo-4"),
        ("Wowhead", "https://www.wowhead.com/news/rss/diablo-4")
    ]

    async with aiohttp.ClientSession() as session:
        for source_name, url in feeds:
            try:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries[:5]: # Verificar as 5 mais recentes
                            link = entry.link
                            if link not in cache:
                                title = entry.title
                                summary = getattr(entry, "summary", "Clique no link para ler mais.")
                                # Limpar HTML do resumo se necessário
                                soup = BeautifulSoup(summary, "lxml")
                                clean_summary = soup.get_text()[:250] + "..."
                                
                                embed = discord.Embed(
                                    title=f"🗞️ {title}",
                                    description=clean_summary,
                                    url=link,
                                    color=discord.Color.blue()
                                )
                                embed.set_author(name=source_name)
                                embed.add_field(name="🔗 Link", value=f"[Ler notícia completa]({link})")
                                if hasattr(entry, "published"):
                                    embed.set_footer(text=f"Publicado em: {entry.published}")
                                
                                await target_channel.send(embed=embed)
                                cache.append(link)
                                new_news_found += 1
                                await asyncio.sleep(1) # Evitar spam
            except Exception as e:
                print(f"Erro ao monitorar feed {source_name}: {e}")

    if new_news_found > 0:
        # Manter apenas as últimas 100 no cache para não crescer infinitamente
        save_news_cache(cache[-100:])
    print(f"Monitoramento de notícias concluído. {new_news_found} novas postadas.")

# --- Monitor de Eventos (World Boss) ---

EVENT_CACHE_FILE = "event_cache.json"

def load_event_cache():
    if os.path.exists(EVENT_CACHE_FILE):
        with open(EVENT_CACHE_FILE, "r") as f:
            return json.load(f)
    return []

def save_event_cache(cache):
    with open(EVENT_CACHE_FILE, "w") as f:
        json.dump(cache, f)

@tasks.loop(minutes=5)
async def monitor_events():
    await bot.wait_until_ready()
    print("--- Iniciando monitoramento de eventos ---")
    
    guild = discord.utils.get(bot.guilds, id=1086783767278014495)
    if not guild: return
    
    target_channel = discord.utils.get(guild.text_channels, name="eventos")
    if not target_channel:
        target_channel = next((c for c in guild.text_channels if "evento" in c.name.lower()), None)
    
    if not target_channel:
        print("Erro: Canal #eventos não encontrado.")
        return

    cache = load_event_cache()
    new_event_found = False

    url = "https://helltides.com/api/schedule"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 1. World Boss
                    if "world_boss" in data and len(data["world_boss"]) > 0:
                        next_boss = data["world_boss"][0]
                        boss_id = str(next_boss["id"])
                        
                        if boss_id not in cache:
                            boss_timestamp = next_boss["timestamp"]
                            current_timestamp = asyncio.get_event_loop().time() # No, use time.time()
                            import time
                            now = time.time()
                            
                            diff_minutes = (boss_timestamp - now) / 60
                            
                            # Notificar quando faltar entre 25 e 35 minutos
                            if 25 <= diff_minutes <= 35:
                                boss_name = next_boss.get("boss", "World Boss")
                                zone_name = next_boss["zone"][0]["name"] if next_boss.get("zone") else "Santuário"
                                
                                role = discord.utils.get(guild.roles, name="World Boss")
                                mention = role.mention if role else "@World Boss"
                                
                                embed = discord.Embed(
                                    title=f"⚔️ O DESPERTAR DO MAL: {boss_name}",
                                    description=f"Um World Boss está prestes a surgir em **{zone_name}**!",
                                    color=discord.Color.red()
                                )
                                embed.add_field(name="🕒 Horário", value=f"Daqui a aproximadamente **30 minutos**", inline=True)
                                embed.add_field(name="📍 Local", value=zone_name, inline=True)
                                embed.set_footer(text="Deckard Cain - Alerta de Combate")
                                
                                await target_channel.send(content=f"{mention} preparem-se!", embed=embed)
                                cache.append(boss_id)
                                new_event_found = True

                    # 2. Legion Events
                    if "legion" in data and len(data["legion"]) > 0:
                        next_legion = data["legion"][0]
                        legion_id = f"legion_{next_legion['id']}"
                        
                        if legion_id not in cache:
                            import time
                            now = time.time()
                            legion_timestamp = next_legion["timestamp"]
                            diff_minutes = (legion_timestamp - now) / 60
                            
                            # Notificar quando faltar entre 8 e 12 minutos
                            if 8 <= diff_minutes <= 12:
                                zone_name = next_legion["zone"][0]["name"] if next_legion.get("zone") else "Santuário"
                                
                                role = discord.utils.get(guild.roles, name="Legion")
                                mention = role.mention if role else "@Legion"
                                
                                embed = discord.Embed(
                                    title=f"⚔️ EVENTO DE LEGIÃO",
                                    description=f"Uma Legião está se reunindo em **{zone_name}**!",
                                    color=discord.Color.orange()
                                )
                                embed.add_field(name="🕒 Horário", value=f"Daqui a aproximadamente **10 minutos**", inline=True)
                                embed.add_field(name="📍 Local", value=zone_name, inline=True)
                                embed.set_footer(text="Deckard Cain - Alerta de Combate")
                                
                                await target_channel.send(content=f"{mention} preparem-se!", embed=embed)
                                cache.append(legion_id)
                                new_event_found = True
    except Exception as e:
        print(f"Erro ao monitorar eventos: {e}")

    if new_event_found:
        save_event_cache(cache[-50:])
    print("Monitoramento de eventos concluído.")

def detect_class(title, url=""):
    combined = (title + " " + url).lower()
    if any(x in combined for x in ["barbarian", "bárbaro", "barbaro", "barb"]):
        return "Bárbaro"
    if any(x in combined for x in ["druid", "druida"]):
        return "Druida"
    if any(x in combined for x in ["necromancer", "necromante", "necro"]):
        return "Necromante"
    if any(x in combined for x in ["rogue", "renegado"]):
        return "Renegado"
    if any(x in combined for x in ["sorcerer", "sorc", "mago"]):
        return "Mago"
    if any(x in combined for x in ["spiritborn", "natispírito", "natispirito", "spirit"]):
        return "Natispírito"
    if any(x in combined for x in ["warlock", "witch doctor", "bruxo", "dread claws", "hell fracture"]):
        return "Bruxo"
    if any(x in combined for x in ["paladin", "crusader", "paladino"]):
        return "Paladino"
    return None

@bot.event
async def on_member_join(member):
    print(f'!!! Novo Nephalem chegou: {member.name} ({member.id})')
    # Auto-role desativado conforme solicitado. Agora os membros devem aceitar as regras.

# --- Canais de Voz Dinâmicos ---

FUNNY_VOICE_NAMES = [
    "🥩 Açougue do Butcher",
    "🏺 Tumba de Tal Rasha",
    "🏰 Catedral de Tristram",
    "💀 Necrotério do Cain",
    "🔥 Fortaleza do Pandemônio",
    "🐲 Pico Arreat",
    "🌵 Esgotos de Lut Gholein",
    "🌳 Selva de Kurast",
    "🏯 Câmara de Baal",
    "🧙‍♂️ Biblioteca de Zoltun Kulle",
    "🍺 Taberna do Ganso Gordo",
    "🏔️ Monastério das Cegas"
]

@bot.event
async def on_voice_state_update(member, before, after):
    # Trigger: Entrou no canal "Crie Seu Grupo"
    # O nome pode conter o emoji [ 👆 ] conforme a print
    trigger_name = "Crie Seu Grupo"
    
    # 1. Lógica de Criação
    if after.channel and trigger_name in after.channel.name:
        import random
        guild = member.guild
        category = after.channel.category
        channel_name = random.choice(FUNNY_VOICE_NAMES)
        
        # Configurar permissões: Usuário que criou pode gerenciar
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, speak=True, view_channel=True),
            member: discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, connect=True, speak=True),
            guild.me: discord.PermissionOverwrite(manage_channels=True, move_members=True, connect=True, view_channel=True)
        }
        
        try:
            # Criar o canal de voz
            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Canal dinâmico criado por {member.name}"
            )
            
            # Mover o usuário para o novo canal
            await member.move_to(new_channel)
            print(f"Canal dinâmico '{channel_name}' criado para {member.name}")
            
        except discord.Forbidden as e:
            print(f"ERRO DE PERMISSÃO no sistema de voz: {e}")
        except Exception as e:
            print(f"Erro inesperado no sistema de voz: {e}")

    # 2. Lógica de Limpeza
    if before.channel:
        # Verificar se o canal que o usuário deixou é um canal temporário e está vazio
        # Canais temporários estão na lista FUNNY_VOICE_NAMES
        if before.channel.name in FUNNY_VOICE_NAMES and len(before.channel.members) == 0:
            try:
                await before.channel.delete(reason="Canal temporário vazio.")
                print(f"Canal dinâmico '{before.channel.name}' removido (vazio).")
            except discord.Forbidden:
                print(f"Erro: Sem permissão para remover canal {before.channel.name}")
            except discord.NotFound:
                pass # Já foi deletado
            except Exception as e:
                print(f"Erro ao deletar canal vazio: {e}")

# --- Sistema de Regras ---

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Li e concordo com as regras", style=discord.ButtonStyle.success, custom_id="rules:accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_name = "Membro"
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        
        if role is None:
            try:
                role = await interaction.guild.create_role(name=role_name, reason="Sistema de Regras")
            except discord.Forbidden:
                await interaction.response.send_message("Não tenho permissão para criar o cargo 'Membro'.", ephemeral=True)
                return

        if role in interaction.user.roles:
            await interaction.response.send_message("Você já é um membro aceito!", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("Bem-vindo! Você agora tem acesso total ao servidor.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("Não tenho permissão para lhe atribuir o cargo. Verifique minha posição na lista de cargos.", ephemeral=True)

    @discord.ui.button(label="Não concordo com as regras", style=discord.ButtonStyle.danger, custom_id="rules:decline")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Você precisa concordar com as regras para se tornar um membro e acessar o restante do servidor.", ephemeral=True)

@bot.command(name='setup_regras')
@commands.has_permissions(administrator=True)
async def setup_regras(ctx):
    """Configura a mensagem de regras com botões de aceitação."""
    embed = discord.Embed(
        title="Regras do Servidor",
        color=discord.Color.red()
    )
    
    rules_text = (
        "1. **Seja gentil.**\n"
        "Você deve respeitar todos os usuários, independentemente do seu gosto por eles. Trate os outros da maneira que você gostaria de ser tratado.\n\n"
        "2. **Sem linguagem imprópria.**\n"
        "O uso de palavrões deve ser mínimo. No entanto, qualquer linguagem depreciativa para qualquer usuário é proibida.\n\n"
        "3. **Sem spam.**\n"
        "Não envie muitas mensagens pequenas uma após a outra. Não interrompa o bate-papo enviando spam.\n\n"
        "4. **Nenhum material pornográfico.**\n"
        "Este é um servidor da comunidade e não se destina a compartilhar esse tipo de material.\n\n"
        "5. **Sem nomes ofensivos e fotos de perfil.**\n"
        "Você será solicitado a alterar seu nome ou foto se a equipe os considerar inapropriados.\n\n"
        "6. **Sem ameaças diretas e indiretas.**\n"
        "Ameaças a outros usuários de DDoS, morte, DoX, abuso e outras ameaças maliciosas são absolutamente proibidas.\n\n"
        "7. **Discord obrigatório.**\n"
        "Se um membro estiver no jogo e não no Discord sem motivos claros para tal, o mesmo será removido do Clã.\n\n"
        "8. **Sem debates acalorados sobre política e religião.**\n"
        "Nossa intenção é ficarmos unidos, independente de qual ideologia seguimos; sendo assim é melhor evitarmos tais tópicos pela saúde do ambiente.\n\n"
        "9. **Ações que quebram o ToS do Diablo 4.**\n"
        "Fazer ou anunciar que irá fazer algo que quebra os termos de serviço do Diablo 4 é algo punível com banimento da guilda."
    )
    
    embed.description = rules_text
    view = RulesView()
    try:
        await ctx.send(embed=embed, view=view)
    except discord.Forbidden:
        try:
            await ctx.author.send("Eu não tenho permissão para enviar mensagens ou embeds no canal #regras! Por favor, verifique se tenho as permissões: 'Enviar Mensagens' e 'Inserir Links'.")
        except:
            pass
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass # Ignora se não puder deletar a mensagem original

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()
    # Gatilho em português
    if "fique um pouco e ouça" in content or "stay awhile and listen" in content:
        await message.channel.send(f"*{quotes.get_random_quote()}*")

    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Testa o pulso do bot."""
    await ctx.send(f"Ainda estou aqui, amigo. Latência: {round(bot.latency * 1000)}ms")

@bot.command(name='listen', aliases=['ouvir'])
async def listen(ctx):
    """Ouve uma frase aleatória do Cain."""
    await ctx.send(quotes.get_random_quote())

@bot.command(name='identify', aliases=['identificar'])
async def identify(ctx):
    """Identifica sua situação atual ou um item aleatório."""
    await ctx.send(quotes.get_identify_message())

@bot.command(name='lore')
async def lore(ctx):
    """Aprenda sobre a história de Santuário."""
    await ctx.send(f"**Arquivo de Conhecimento:** {quotes.get_random_lore()}")

@bot.command(name='item')
async def item(ctx, *, item_name: str = None):
    """Procura por um item clássico. Uso: !item shako"""
    if not item_name:
        await ctx.send("Qual item você deseja que eu examine? (Tente: !item shako, soj, enigma)")
        return
    
    result = quotes.lookup_item(item_name)
    await ctx.send(result)

@bot.command(name='runeword', aliases=['palavra'])
async def runeword(ctx, *, name: str = None):
    """Procura requisitos de palavras rúnicas. Uso: !runeword enigma"""
    if not name:
        await ctx.send("Qual palavra rúnica você procura? (Tente: !runeword spirit, enigma, grief)")
        return
    await ctx.send(f"**{name.title()}:** {quotes.lookup_runeword(name)}")

@bot.command(name='recipe', aliases=['receita'])
async def recipe(ctx, *, name: str = None):
    """Procura receitas do Cubo Horádrico. Uso: !recipe socket_weapon"""
    if not name:
        await ctx.send("De qual receita você precisa? (Tente: !recipe socket_weapon, up_unique_armor)")
        return
    await ctx.send(f"**Receita:** {quotes.lookup_recipe(name)}")

@bot.command(name='gamble', aliases=['apostar'])
async def gamble(ctx):
    """Tente sua sorte com Gheed... ou Cain."""
    await ctx.send(f"*{ctx.author.name} joga um pouco de ouro...* \n{quotes.gamble()}")

# --- Sistema de Cargos por Botões ---

class RoleButton(discord.ui.Button):
    def __init__(self, role_name, emoji, style=discord.ButtonStyle.secondary):
        # O custom_id é necessário para que os botões funcionem após o bot reiniciar
        custom_id = f"role_button:{role_name}"
        super().__init__(label=role_name, emoji=emoji, style=style, custom_id=custom_id)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        # Usar defer para evitar "Interaction failed" se demorar
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            role = discord.utils.get(guild.roles, name=self.role_name)

            if role is None:
                # Tentar criar o cargo se não existir
                try:
                    role = await guild.create_role(name=self.role_name, reason="Sistema de Cargos Deckard Cain")
                except discord.Forbidden:
                    await interaction.followup.send(f"Eu não tenho permissão para criar o cargo **{self.role_name}**.", ephemeral=True)
                    return

            if role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(role)
                    await interaction.followup.send(f"O cargo **{self.role_name}** foi removido!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send(f"Eu não tenho permissão para remover o cargo **{self.role_name}**. Verifique minha posição na lista de cargos!", ephemeral=True)
            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.followup.send(f"O cargo **{self.role_name}** foi adicionado!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send(f"Eu não tenho permissão para adicionar o cargo **{self.role_name}**. Verifique minha posição na lista de cargos!", ephemeral=True)
        
        except Exception as e:
            print(f"Erro crítico no callback de cargo: {e}")
            await interaction.followup.send(f"Ocorreu um erro interno ao processar seu cargo.", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout=None para os botões serem persistentes
        
        # Adicionando os botões conforme a imagem
        self.add_item(RoleButton("Leveling", "🧪"))
        self.add_item(RoleButton("PvP", "⚔️"))
        self.add_item(RoleButton("Helltide", "🏰"))
        self.add_item(RoleButton("Hardcore", "🔥"))
        self.add_item(RoleButton("Dungeon", "🏯"))
        self.add_item(RoleButton("Nightmare Dungeon", "🏯"))
        self.add_item(RoleButton("World Boss", "🐲"))
        # Novos Cargos Vessel of Hatred
        self.add_item(RoleButton("The Pit", "🏺"))
        self.add_item(RoleButton("Infernal Hordes", "🔥"))
        self.add_item(RoleButton("Fishing", "🎣"))
        self.add_item(RoleButton("Kurast Undercity", "🏛️"))
        self.add_item(RoleButton("Dark Citadel", "🏰"))
        self.add_item(RoleButton("War Plans", "📜"))
        self.add_item(RoleButton("Echoing Hatred", "🗣️"))
        self.add_item(RoleButton("Legion", "🛡️"))

# --- Sistema de Cargos de Classe ---

class ClassRoleButton(discord.ui.Button):
    def __init__(self, role_name, emoji):
        custom_id = f"class_role:{role_name}"
        super().__init__(label=role_name, emoji=emoji, style=discord.ButtonStyle.success, custom_id=custom_id)
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.role_name)

        if role is None:
            try:
                role = await guild.create_role(name=self.role_name, reason="Cargos de Classe Deckard Cain")
            except discord.Forbidden:
                await interaction.followup.send(f"Sem permissão para criar o cargo **{self.role_name}**.", ephemeral=True)
                return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.followup.send(f"Você não é mais um **{self.role_name}**!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send(f"Agora você é um **{self.role_name}**! Que os deuses te guiem.", ephemeral=True)

class ClassRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ClassRoleButton("Bárbaro", "🪓"))
        self.add_item(ClassRoleButton("Druida", "🐾"))
        self.add_item(ClassRoleButton("Necromante", "💀"))
        self.add_item(ClassRoleButton("Renegado", "🏹"))
        self.add_item(ClassRoleButton("Mago", "✨"))
        self.add_item(ClassRoleButton("Natispírito", "🦅"))
        self.add_item(ClassRoleButton("Bruxo", "🔮"))
        self.add_item(ClassRoleButton("Paladino", "🛡️"))

@bot.command(name='setup_classes')
@commands.has_permissions(administrator=True)
async def setup_classes(ctx):
    """Configura o painel de seleção de classes."""
    embed = discord.Embed(
        title="Escolha sua Classe",
        description="Selecione abaixo a classe que você está jogando para receber notificações de builds e ser identificado no clã.",
        color=discord.Color.dark_green()
    )
    view = ClassRoleView()
    await ctx.send(embed=embed, view=view)
    try: await ctx.message.delete()
    except: pass

# --- Sistema de Divulgação de Grupos ---

class GroupAnnouncementModal(discord.ui.Modal):
    complemento = discord.ui.TextInput(
        label="Mensagem Complementar",
        style=discord.TextStyle.paragraph,
        placeholder="Ex: Faltam 2 slots! Vamos fazer The Pit tier 100.",
        required=False,
        max_length=300
    )

    def __init__(self, role_name, voice_channel, quote):
        super().__init__(title="Divulgação de Grupo")
        self.role_name = role_name
        self.voice_channel = voice_channel
        self.quote = quote

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        target_channel = discord.utils.get(guild.text_channels, name="grupos")
        if not target_channel:
            target_channel = next((c for c in guild.text_channels if "grupos" in c.name.lower()), None)

        if not target_channel:
            await interaction.response.send_message("Não consegui encontrar o canal de grupos!", ephemeral=True)
            return

        try:
            invite = await self.voice_channel.create_invite(max_age=3600, reason="Divulgação de Grupo")
            
            embed = discord.Embed(
                title="📢 Novo Grupo Formado!",
                description=f"*{self.quote}*",
                color=discord.Color.gold()
            )
            embed.add_field(name="👤 Líder", value=interaction.user.mention, inline=True)
            embed.add_field(name="⚔️ Atividade", value=self.role_name, inline=True)
            
            if self.complemento.value:
                embed.add_field(name="📜 Nota do Líder", value=self.complemento.value, inline=False)
                
            embed.add_field(name="🔊 Canal de Voz", value=f"[{self.voice_channel.name}]({invite.url})", inline=False)
            embed.set_footer(text="Clique no nome do canal acima para se juntar à caçada!")
            
            role = discord.utils.get(guild.roles, name=self.role_name)
            mention = role.mention if role else f"@{self.role_name}"
            
            await target_channel.send(content=mention, embed=embed)
            await interaction.response.send_message(f"Seu grupo foi divulgado em {target_channel.mention}!", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"Erro ao compartilhar: {e}", ephemeral=True)

class GroupSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Leveling", emoji="🧪"),
            discord.SelectOption(label="PvP", emoji="⚔️"),
            discord.SelectOption(label="Helltide", emoji="🏰"),
            discord.SelectOption(label="Hardcore", emoji="🔥"),
            discord.SelectOption(label="Dungeon", emoji="🏯"),
            discord.SelectOption(label="Nightmare Dungeon", emoji="🏯"),
            discord.SelectOption(label="World Boss", emoji="🐲"),
            discord.SelectOption(label="The Pit", emoji="🏺"),
            discord.SelectOption(label="Infernal Hordes", emoji="🔥"),
            discord.SelectOption(label="Fishing", emoji="🎣"),
            discord.SelectOption(label="Kurast Undercity", emoji="🏛️"),
            discord.SelectOption(label="Dark Citadel", emoji="🏰"),
            discord.SelectOption(label="War Plans", emoji="📜"),
            discord.SelectOption(label="Echoing Hatred", emoji="🗣️")
        ]
        super().__init__(placeholder="Selecione o cargo que você quer notificar", min_values=1, max_values=1, options=options, custom_id="group:select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

class GroupAnnouncementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GroupSelect())

    @discord.ui.button(label="Compartilhar", style=discord.ButtonStyle.primary, emoji="🚀", custom_id="group:share")
    async def share(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Verificar conexão de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("Você precisa estar conectado em um canal de voz para compartilhar seu grupo!", ephemeral=True)
            return

        # 2. Obter o cargo selecionado
        select = [item for item in self.children if isinstance(item, GroupSelect)][0]
        if not select.values:
            await interaction.response.send_message("Por favor, selecione um cargo antes de compartilhar!", ephemeral=True)
            return
        
        role_name = select.values[0]
        voice_channel = interaction.user.voice.channel
        
        # 3. Mensagens engraçadas por atividade
        ACTIVITY_QUOTES = {
            "Leveling": "A pressa é a inimiga da perfeição, mas a amiga do XP fácil!",
            "PvP": "Alguém disse orelhas grátis? Vamos colher algumas!",
            "Helltide": "O tempo está ótimo para um passeio no Inferno, não acham?",
            "The Pit": "Vamos descer até onde a luz não alcança... e o loot brilha!",
            "Infernal Hordes": "Mais carne para o moedor! Quem traz o tempero de enxofre?",
            "Fishing": "Espero que pesquemos algo melhor que a perna de pau do Wirt.",
            "Kurast Undercity": "Explorar esgotos... que romântico. Tragam seus perfumes!",
            "Dark Citadel": "Um castelo escuro e cheio de demônios. Meu tipo favorito de férias.",
            "War Plans": "Eu tenho um plano: nós batemos, eles morrem. Gostaram?",
            "Echoing Hatred": "O ódio está no ar! Vamos dar um motivo para eles gritarem.",
            "World Boss": "Ele é grande, feio e tem tesouros. Vamos resolver os dois primeiros problemas!",
            "Hardcore": "Lembrem-se: se morrerem, eu não conheço vocês.",
            "Dungeon": "Mais um corredor escuro? O último a sair apaga a tocha!",
            "Nightmare Dungeon": "Como uma Masmorra comum, mas com mais pesadelos e menos sono."
        }
        
        quote = ACTIVITY_QUOTES.get(role_name, "Venham lutar conosco Nephalem!")

        # 4. Abrir Modal para mensagem complementar
        modal = GroupAnnouncementModal(role_name, voice_channel, quote)
        await interaction.response.send_modal(modal)

@bot.command(name='setup_divulgar')
@commands.has_permissions(administrator=True)
async def setup_divulgar(ctx):
    """Configura o painel de divulgação de grupos."""
    embed = discord.Embed(
        title="Compartilhe seu grupo aqui!",
        description="Após criar seu grupo, selecione uma opção para convidar outros membros da guild para jogar com você.",
        color=discord.Color.red()
    )
    
    view = GroupAnnouncementView()
    try:
        await ctx.send(embed=embed, view=view)
    except discord.Forbidden:
        await ctx.author.send("Não tenho permissão para enviar o painel no canal!")
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

@bot.command(name='setup_cargos')
@commands.has_permissions(administrator=True)
async def setup_cargos(ctx):
    """Configura a mensagem de seleção de cargos com botões."""
    embed = discord.Embed(
        title="Cargos para Notificação",
        description="Clique nos botões abaixo para ativar ou desativar as notificações de um cargo específico.",
        color=discord.Color.red()
    )
    
    view = RoleView()
    try:
        await ctx.send(embed=embed, view=view)
    except discord.Forbidden:
        await ctx.author.send("Eu não tenho permissão para enviar mensagens neste canal!")
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

# --- Sistema de Tickets de Suporte ---

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Apenas a Staff pode fechar este ticket.", ephemeral=True)
            return
        
        await interaction.response.send_message("Este ticket será fechado em 5 segundos...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete(reason="Ticket fechado pela Staff.")

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, emoji: str):
        guild = interaction.guild
        user = interaction.user
        
        category = discord.utils.get(guild.categories, name="TICKETS")
        if category is None:
            try:
                category = await guild.create_category("TICKETS")
            except discord.Forbidden:
                await interaction.response.send_message("Não tenho permissão para criar categorias!", ephemeral=True)
                return

        channel_name = f"{emoji}-{ticket_type}-{user.name}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        
        staff_role = discord.utils.get(guild.roles, name="Oficial") or discord.utils.get(guild.roles, name="Staff")
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        try:
            channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
            await interaction.response.send_message(f"Seu ticket foi criado: {channel.mention}", ephemeral=True)
            
            embed = discord.Embed(
                title=f"Ticket de {ticket_type.capitalize()}",
                description=f"Olá {user.mention}, explique os detalhes da sua {ticket_type} abaixo. A coordenação será notificada.",
                color=discord.Color.gold()
            )
            embed.set_footer(text="Deckard Cain Support System")
            
            await channel.send(embed=embed, view=TicketControlView())
            if staff_role:
                await channel.send(f"{staff_role.mention}, um novo ticket de {ticket_type} foi aberto por {user.mention}.")
                
        except discord.Forbidden:
            await interaction.response.send_message("Erro: Não tenho permissão para criar canais de texto!", ephemeral=True)

    @discord.ui.button(label="Sugestão", style=discord.ButtonStyle.secondary, emoji="💡", custom_id="support:sugestao")
    async def sugestao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "sugestão", "💡")

    @discord.ui.button(label="Denúncia", style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="support:denuncia")
    async def denuncia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "denúncia", "🚫")

@bot.command(name='setup_noticias')
@commands.has_permissions(administrator=True)
async def setup_noticias(ctx):
    """Configura o canal de notícias."""
    embed = discord.Embed(
        title="📰 Central de Notícias Deckard Cain",
        description="Este canal agora está sob a vigília do Cain. Notícias oficiais da Blizzard e novidades do Wowhead serão postadas aqui automaticamente.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    try: await ctx.message.delete()
    except: pass

@bot.command(name='migrate_visitantes')
@commands.has_permissions(administrator=True)
async def migrate_visitantes(ctx):
    """Move todos os membros com cargo 'Visitante' para 'Membro'."""
    role_visitante = discord.utils.get(ctx.guild.roles, name="Visitante")
    role_membro = discord.utils.get(ctx.guild.roles, name="Membro")

    if not role_visitante or not role_membro:
        await ctx.send("❌ Erro: Certifique-se que os cargos 'Visitante' e 'Membro' existam.")
        return

    msg = await ctx.send(f"⏳ Iniciando migração de **{role_visitante.name}** para **{role_membro.name}**...")
    
    count = 0
    errors = 0
    
    # Garantir que temos a lista completa
    async for member in ctx.guild.fetch_members(limit=None):
        if role_visitante in member.roles:
            try:
                # Adiciona o novo cargo primeiro
                await member.add_roles(role_membro, reason="Migração por Deckard Cain")
                # Remove o antigo se a adição funcionou
                await member.remove_roles(role_visitante, reason="Migração por Deckard Cain")
                
                count += 1
                if count % 5 == 0:
                    await msg.edit(content=f"⏳ Migrando... {count} membros processados.")
                    print(f"Migração: {count} membros processados...")
                
                # Pequeno delay para evitar rate limit agressivo
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                print(f"ERRO DE PERMISSÃO: Não consegui alterar o cargo de {member.name}")
                errors += 1
            except Exception as e:
                print(f"Erro ao migrar {member.name}: {e}")
                errors += 1

    final_msg = f"✅ Migração concluída!\n👤 **{count}** membros atualizados.\n⚠️ **{errors}** falhas (verifique se o cargo do bot está acima dos outros)."
    await ctx.send(final_msg)

@bot.command(name='check_builds')
@commands.has_permissions(administrator=True)
async def check_builds(ctx):
    """Força uma verificação manual de novas builds."""
    await ctx.send("🔍 Iniciando verificação manual de builds em Santuário...", delete_after=5)
    await monitor_builds()
    await ctx.send("✅ Verificação concluída. Verifique os logs e o canal #builds-novas.", delete_after=5)

@bot.command(name='fix_roles')
@commands.has_permissions(administrator=True)
async def fix_roles(ctx):
    """Cria todos os cargos necessários se eles não existirem."""
    roles_to_create = [
        "Membro", "Leveling", "PvP", "Helltide", "Hardcore", "Dungeon", 
        "Nightmare Dungeon", "World Boss", "The Pit", "Infernal Hordes", 
        "Fishing", "Kurast Undercity", "Dark Citadel", "War Plans", "Echoing Hatred", "Legion",
        "Bárbaro", "Druida", "Necromante", "Renegado", "Mago", "Natispírito", "Bruxo", "Paladino"
    ]
    
    created = []
    existed = []
    failed = []
    
    for r_name in roles_to_create:
        role = discord.utils.get(ctx.guild.roles, name=r_name)
        if role:
            existed.append(r_name)
        else:
            try:
                await ctx.guild.create_role(name=r_name, reason="Fix Roles command")
                created.append(r_name)
            except discord.Forbidden:
                failed.append(r_name)
    
    msg = "**Relatório de Cargos:**\n"
    if created: msg += f"✅ Criados: {', '.join(created)}\n"
    if existed: msg += f"ℹ️ Já existiam: {', '.join(existed)}\n"
    if failed: msg += f"❌ Falha (falta permissão): {', '.join(failed)}\n"
    
    await ctx.send(msg)

@bot.command(name='setup_suporte')
@commands.has_permissions(administrator=True)
async def setup_suporte(ctx):
    """Configura a mensagem de suporte para tickets."""
    embed = discord.Embed(
        title="Suporte",
        description="Clique no botão abaixo para entrar em contato com a coordenação da Ascended Nephalem a respeito de uma sugestão ou denúncia",
        color=discord.Color.red()
    )
    
    view = SupportView()
    try:
        await ctx.send(embed=embed, view=view)
    except discord.Forbidden:
        await ctx.author.send("Não tenho permissão para enviar o painel de suporte no canal!")
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

@bot.command(name='limpar', aliases=['clear', 'purge'])
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, quantidade: int = 100):
    """Limpa mensagens do canal. Uso: !limpar 50"""
    if quantidade <= 0:
        await ctx.send("Por favor, informe uma quantidade maior que zero.", delete_after=5)
        return
    
    # Limitar a 100 por vez para segurança
    quantidade = min(quantidade, 100)
    
    print(f"Tentando limpar {quantidade} mensagens no canal {ctx.channel.name}...")
    
    try:
        deleted = await ctx.channel.purge(limit=quantidade + 1)
        await ctx.send(f"🧹 Santuário foi limpo! **{len(deleted)-1}** mensagens foram removidas.", delete_after=5)
        print(f"Limpeza concluída: {len(deleted)-1} mensagens removidas.")
    except discord.Forbidden:
        await ctx.send("Eu não tenho permissão para gerenciar mensagens (Manage Messages) neste canal.", delete_after=10)
        print(f"ERRO: Permissão negada no canal {ctx.channel.name}")
    except discord.HTTPException as e:
        await ctx.send(f"Erro de conexão com o Discord (Rate Limit?): {e}", delete_after=10)
        print(f"ERRO HTTP: {e}")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro inesperado: {e}", delete_after=10)
        print(f"ERRO INESPERADO: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"Desculpe, amigo {ctx.author.mention}, mas você não tem as permissões necessárias para usar este comando.", delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Faltou algum argumento necessário para o comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Por favor, forneça um número válido.", delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Erro no comando: {error}")
        try:
            await ctx.send(f"Ocorreu um erro ao processar o comando.")
        except:
            pass

@bot.command(name='help', aliases=['ajuda'])
async def help_command(ctx):
    """Mostra os comandos disponíveis."""
    embed = discord.Embed(
        title="Sabedoria de Deckard Cain",
        description="Eu retornei para auxiliar os Nephalem Ascendidos!",
        color=discord.Color.gold()
    )
    embed.add_field(name="📜 História", value="`!listen`, `!lore`, `!identify`", inline=True)
    embed.add_field(name="⚔️ Banco de Dados", value="`!item [nome]`, `!runeword [nome]`, `!recipe [nome]`", inline=True)
    embed.add_field(name="💰 Diversão", value="`!gamble`", inline=True)
    embed.add_field(name="⚙️ Admin", value="`!setup_cargos`, `!setup_regras`, `!limpar [num]`", inline=True)
    embed.add_field(name="✨ Gatilho", value="Digite 'Fique um pouco e ouça' em qualquer lugar.", inline=False)
    
    embed.set_footer(text="Que seus drops sejam lendários.")
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("Erro: DISCORD_TOKEN não encontrado no arquivo .env.")
    else:
        try:
            bot.run(TOKEN)
        except discord.errors.PrivilegedIntentsRequired:
            print("\n!!! ERRO: Intenções Privilegiadas Necessárias !!!")
            print("Por favor, ative 'Message Content Intent' E 'Server Members Intent' no Portal do Desenvolvedor.")
            print("Reiniciando em Modo Limitado...")
            
            intents.message_content = False
            intents.members = False
            bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
            
            @bot.event
            async def on_ready():
                print(f'--- Deckard Cain chegou (Modo Limitado) ---')
                print(f'Logado como: {bot.user.name} ({bot.user.id})')
            
            bot.run(TOKEN)
