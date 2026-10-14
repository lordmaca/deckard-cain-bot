# 📜 Deckard Cain — The Last Horadrim Discord Bot
> *"Stay a while and listen... before the server host reboots!"*

[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com)
[![Diablo IV](https://img.shields.io/badge/Diablo_IV-Vessel_of_Hatred-8B0000?style=for-the-badge)](https://diablo4.blizzard.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

---

## 📖 The Legend: Why is an 80-year-old scholar running a Discord bot?

Long ago in Tristram, Deckard Cain spent his days trapped in a hanging cage, identifying rare rings that turned out to have `+2 to Light Radius`. 

After escaping the Prime Evils, surviving Maghda’s butterfly swarm, and dodging several cloud server shutdowns without a Git commit, Deckard has ascended to the digital realm. He is now the supreme guardian, meta-analyzer, and community manager for the **Ascended Nephalem** Diablo IV community.

---

## ⚡ Legendary Aspects & Features

### 🔍 1. The All-Seeing Eye of the Meta (Automated Build Scraper)
* **What it does:** Continuously scours **D4Builds.gg**, **Maxroll**, **Mobalytics**, and **Icy-Veins** so you don't have to refresh patch notes at 3 AM.
* **Smart Mentions:** When a build drops for Barbarian, Sorcerer, Druid, Rogue, Necromancer, or the busted **Spiritborn (Natispírito)** doing 47 quadrillion damage, it automatically tags the corresponding role in `#builds-novas`.
* **Zero Duplicate Spam:** Built-in JSON cache keeps track of known builds so your server doesn't get flooded like the Swamps of Hawezar.

### 🥩 2. The Butcher's Dynamic Voice Sanctuary
* **Instant Summoning:** Hop into the `[ 👆 ] Crie Seu Grupo` channel, and Deckard instantly conjures a private voice dungeon for you with Diablo-themed names (like `🥩 Açougue do Butcher` or `🔥 Fogueira de Tristram`).
* **Party Leadership:** The creator gets channel management permissions to kick AFK goblins.
* **Auto-Purge:** The second everyone leaves, the room vanishes into the void. No clutter, no ghosts.

### 🎲 3. Kadala's Disappointment Simulator (`!gamble`)
* Think you're getting a Tyrael's Might? Think again.
* Bet your hard-earned pride to roll for Sacred, Ancestral, or Mythic Uniques. Most of the time, Kadala just laughs and hands you a cracked leather cap.

### 📜 4. Horadric Lore, Recipes & Item Identification
* `!listen` / `!lore` / `!identify`: Cain shares deep Sanctuary lore and identifies your journey.
* `!recipe [item]`: Can't remember what goes into the Horadric Cube? Deckard knows.
* `!runeword [nome]`: Look up classic and modern runic combinations.
* `!item [nome]`: Quick item codex lookups.
* **Easter Egg:** Just whisper *"Fique um pouco e ouça"* in any chat channel and watch him wake up.

### 🎫 5. Town Hall Tickets (Support & Complaints)
* Did the World Boss not drop a single spark? Did someone steal your Living Steel?
* Creates isolated, private channels between the player and the guild officers for reports, suggestions, and grievances.

### 🛡️ 6. The Gates of Caldeum (Rules & Role Verification)
* Interactive UI buttons for new wanderers to accept server rules and earn their `Membro` role.
* Self-service role pickers for classes, World Boss pings, Helltide farming, and PvP bloodbaths.

---

## 📜 Grimoire of Commands

### ⚔️ Public Commands (For Every Wanderer)
| Command | Aliases | Description |
| :--- | :--- | :--- |
| `!help` | `!ajuda` | Summons the scroll of commands |
| `!listen` | `!lore`, `!identify` | Receive ancient Horadric wisdom |
| `!item <nome>` | — | Search Sanctuary item archives |
| `!runeword <nome>` | — | Consult Horadric Runewords |
| `!recipe <nome>` | — | Search Horadric Cube recipes |
| `!gamble` | — | Gamble for glory (or blue trash items) |
| *"Fique um pouco e ouça"* | — | Secret conversational trigger |

### 👑 High Council Commands (Admins & Officers)
| Command | Aliases | Description |
| :--- | :--- | :--- |
| `!setup_classes` | — | Spawns the interactive class selection panel (including Spiritborn) |
| `!setup_cargos` | — | Spawns activity roles (Helltide, World Boss, Pit, Nightmare Dungeons) |
| `!setup_regras` | — | Deploys the gatekeeper rules verification panel |
| `!setup_suporte` | — | Sets up the private ticket support totem |
| `!setup_divulgar` | — | Creates the group finder announcement panel |
| `!limpar <n>` | `!clear`, `!purge` | Casts Cataclysm to incinerate the last `n` messages |
| `!fix_roles` | — | Auto-generates any missing server roles |

---

## 🛠️ Summoning Deckard into Your Machine

### 1. Requirements
* **Python 3.10+** (Tested on Python 3.12)
* Discord Bot Token with the following **Privileged Gateway Intents**:
  * ✅ `Server Members Intent`
  * ✅ `Message Content Intent`
  * ✅ `Voice States Intent`

### 2. Quick Setup

```bash
# 1. Clone this ancient repository
git clone https://github.com/lordmaca/deckard-cain-bot.git
cd deckard-cain-bot

# 2. Forge your secret amulet (.env)
cp .env.example .env
# Edit .env and paste your DISCORD_TOKEN

# 3. Create a sacred environment & install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 4. Awaken Deckard Cain
python3 bot.py
```

---

## 🐧 Running as a Linux Daemon (`systemd`)

Keep Deckard alive forever, even when the server restarts:

```bash
# Copy the included unit file
sudo cp deckard-bot.service /etc/systemd/system/

# Reload systemd and unleash the Horadrim
sudo systemctl daemon-reload
sudo systemctl enable deckard-bot
sudo systemctl start deckard-bot

# Check if he's meditating peacefully
sudo systemctl status deckard-bot
```

---

## ⚠️ Sacred Decrees

> [!IMPORTANT]
> **Role Hierarchy Matters:** The `Deckard Cain` bot role in your Discord server settings **MUST be higher** than the roles it assigns (Barbarian, Member, Helltide, etc.). If you place him below mortals, Discord’s permissions will prevent him from bestowing blessings.

> [!CAUTION]
> **Never commit your `.env`:** The Prime Evils (and bots scanning GitHub) will steal your Discord token in 3 seconds flat. Keep `.env` safely in `.gitignore`.

---

<p align="center">
  <i>"I see you have brought another pull request... Let me identify it for you."</i>
  <br>
  <b>Ascended Nephalem © 2026</b>
</p>
