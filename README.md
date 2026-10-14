# 📜 Deckard Cain - Discord Bot (Ascended Nephalem)

O Deckard Cain é um bot multifuncional desenvolvido especificamente para a comunidade de Diablo 4 no servidor **Ascended Nephalem**. Ele combina sabedoria ancestral com ferramentas modernas de gerenciamento de servidor.

## 🚀 Principais Funcionalidades

### 🔍 Monitor de Builds Automático
*   **Vigilância Constante:** Monitora sites como D4Builds.gg em busca de novas builds de meta.
*   **Menções Inteligentes:** Detecta a classe da build e marca automaticamente o cargo correspondente (ex: @Bárbaro, @Druida) no canal `#builds-novas`.

### 🔊 Canais de Voz Dinâmicos
*   **Invocação de Salas:** Ao entrar no canal `[ 👆 ] Crie Seu Grupo`, o bot cria instantaneamente uma sala privada com nomes temáticos (ex: `🥩 Açougue do Butcher`).
*   **Autogestão:** O criador ganha permissão para gerenciar sua sala.
*   **Limpeza Automática:** Salas vazias são deletadas para manter o servidor organizado.

### 🎫 Sistema de Suporte (Tickets)
*   **Privacidade:** Cria canais privados para Sugestões e Denúncias.
*   **Gestão de Staff:** Apenas o autor e a equipe de coordenação têm acesso ao ticket.

### 🎭 Gerenciamento de Cargos e Classes
*   **Auto-atendimento:** Painéis com botões persistentes para escolha de atividades e classes.
*   **Expansão Pronta:** Já inclui suporte para a classe **Natispírito (Spiritborn)** e novos eventos de *Vessel of Hatred*.

### 📜 Sistema de Regras e Verificação
*   **Portão de Entrada:** Novos membros devem aceitar as regras através de um botão para ganhar o cargo de Membro.

---

## 🛠️ Comandos Disponíveis

### 👤 Comandos Públicos
*   `!help` / `!ajuda`: Mostra a lista de comandos.
*   `!listen` / `!lore` / `!identify`: Deckard Cain conta histórias e identifica sua jornada.
*   `!item [nome]`: Busca informações sobre itens.
*   `!runeword [nome]`: Busca palavras rúnicas.
*   `!recipe [nome]`: Busca receitas do Cubo Horádrico.
*   `!gamble`: Tente a sorte na aposta (Estilo Gheed/Kadala).
*   *Gatilho Especial:* Digite "Fique um pouco e ouça" no chat.

### 👑 Comandos de Administração
*   `!setup_cargos`: Envia o painel de seleção de atividades (Helltide, PvP, etc).
*   `!setup_classes`: Envia o painel de seleção de classes (Bárbaro, Mago, etc).
*   `!setup_regras`: Configura o sistema de aceitação de regras.
*   `!setup_suporte`: Configura o painel de tickets de atendimento.
*   `!setup_divulgar`: Configura o painel de convite para grupos.
*   `!limpar [quantidade]`: Remove mensagens do canal (Aliases: `!clear`, `!purge`).
*   `!fix_roles`: Cria/Corrige todos os cargos necessários no servidor.

---

## ⚙️ Configuração Técnica

### Requisitos
*   **Python 3.10+**
*   **discord.py 2.0+**
*   **Intents Necessárias:** `Message Content`, `Server Members`, `Voice States`.

### Instalação
1. Clone o repositório.
2. Crie um arquivo `.env` com seu `DISCORD_TOKEN`.
3. Instale as dependências: `pip install -r requirements.txt`.
4. Execute o bot: `python bot.py`.

### Hierarquia de Cargos
> [!IMPORTANT]
> O cargo do bot deve estar no **topo da lista de cargos** para que ele consiga gerenciar os cargos de classe e atividades dos outros membros.

---
*"Fique um pouco e ouça... e que seus drops sejam lendários!"*
