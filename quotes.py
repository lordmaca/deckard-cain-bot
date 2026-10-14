import random

QUOTES = [
    "Fique um pouco e ouça!",
    "Saudações, amigo. Eu sou Deckard Cain, o último dos Horadrim.",
    "O Cubo Horádrico é um artefato verdadeiramente notável.",
    "Diz-se que os Três Males Supremos foram banidos para o nosso mundo há muito tempo.",
    "Você tem um belo tesouro aí nesse Cubo Horádrico.",
    "Eu irei identificar seus itens, por uma pequena taxa... oh espere, para você, amigo, é de graça.",
    "As Pedras das Almas foram criadas para conter as essências dos Males Supremos.",
    "Diablo, o Senhor do Medo, retornou a Santuário.",
    "Cuidado, o caminho à frente é repleto de perigos.",
    "Os arquivos dos Horadrim contêm muitos segredos.",
    "Tyrael, o Arcanjo da Justiça, nos guiou no passado.",
    "A Pedra do Mundo foi criada para esconder Santuário dos Altos Céus e dos Infernos Ardentes."
]

IDENTIFY_MESSAGES = [
    "Hmm, deixe-me ver... Ah! Este é um belo exemplar de artesanato Horádrico.",
    "Este item vibra com uma leve energia mágica. Está pronto para o uso.",
    "Eu vi muitas coisas em minha longa vida, mas isso... isso é verdadeiramente único.",
    "Um encantamento simples, mas eficaz. Use-o bem.",
    "Isso foi perdido há muito tempo nas profundezas da Catedral de Tristram.",
    "Está identificado! Que ele lhe sirva melhor do que ao seu antigo dono."
]

LORE = [
    "Os Horadrim eram uma antiga ordem de magos dedicados a caçar os Males Supremos.",
    "Tristram já foi uma cidade pacífica antes da Catedral ser corrompida pela presença de Diablo.",
    "A Guerra do Pecado foi um conflito secreto entre os Altos Céus e os Infernos Ardentes pelas almas da humanidade.",
    "Santuário foi criado pelo anjo renegado Inarius e pela demônia Lilith.",
    "Os Infernos Ardentes são governados pelos Três Males Supremos: Diablo, Baal e Mefisto.",
    "Os Altos Céus são governados pelo Conselho Angiris, liderado por Imperius e Tyrael."
]

ITEMS = {
    "shako": "Brasão da Harlequina (Harlequin Crest) - Um elmo lendário que concede +2 para todas as habilidades, vida, mana e redução de dano. Essencial para quase qualquer build.",
    "soj": "Pedra de Jordão (Stone of Jordan) - Um anel lendário que aumenta o poder mágico (+1 para todas as habilidades) e aumenta sua mana total em 25%.",
    "hoto": "Coração do Carvalho (Ko + Vex + Pul + Thul) - Uma poderosa runeword para cajados/maças, favorita de conjuradores pela alta taxa de conjuração e resistências.",
    "enigma": "Enigma (Jah + Ith + Ber) - Uma armadura de runas que concede a habilidade de teleporte, bônus massivo de força e chance de itens mágicos.",
    "griffon": "Olho de Grifo (Griffon's Eye) - Um diadema que aumenta o dano de raio e reduz a resistência do inimigo. Essencial para Amazonas de raio e Sorceress.",
    "botd": "Sopro dos Mortos (Breath of the Dying - Vex + Hel + El + Eld + Zod + Eth) - Uma arma de runas devastadora com dano massivo e roubo de vida.",
    "cta": "Chamado às Armas (Call to Arms - Amn + Ral + Mal + Ist + Ohm) - Concede habilidades de Bárbaro para qualquer classe. Obrigatório na troca de arma.",
    "infinity": "Infinito (Infinity - Ber + Mal + Ber + Ist) - Concede uma Aura de Convicção, removendo as resistências elementares dos inimigos.",
    "fortitude": "Fortitude (El + Sol + Dol + Lo) - A armadura suprema de dano físico para você ou seu mercenário."
}

RUNEWORDS = {
    "enigma": "Jah + Ith + Ber em uma Armadura de 3 engastes. Concede Teleporte e +2 em Todas as Habilidades.",
    "infinity": "Ber + Mal + Ber + Ist em uma Arma de Haste ou Lança de 4 engastes. Concede Aura de Convicção Nível 12.",
    "hoto": "Ko + Vex + Pul + Thul em um Mangual ou Cajado de 4 engastes. Concede +3 em Todas as Habilidades e 40% FCR.",
    "fortitude": "El + Sol + Dol + Lo em uma Armadura ou Arma de 4 engastes. Concede 300% de Dano Aumentado.",
    "spirit": "Tal + Thul + Ort + Amn em um Escudo ou Espada de 4 engastes. O melhor item de conjurador para o início do jogo.",
    "grief": "Eth + Tir + Lo + Mal + Ral em uma Espada ou Machado de 5 engastes. O rei do dano corpo a corpo.",
    "stealth": "Tal + Eth em uma Armadura de 2 engastes. Um ótimo item inicial para qualquer aventureiro."
}

RECIPES = {
    "socket_weapon": "Ral + Amn + Ametista Perfeita + Arma Normal -> Arma com Engastes (Quantidade aleatória)",
    "socket_armor": "Tal + Thul + Topázio Perfeito + Armadura Normal -> Armadura com Engastes (Quantidade aleatória)",
    "socket_helm": "Ral + Thul + Safira Perfeita + Elmo Normal -> Elmo com Engastes (Quantidade aleatória)",
    "socket_shield": "Tal + Amn + Rubi Perfeito + Escudo Normal -> Escudo com Engastes (Quantidade aleatória)",
    "up_unique_armor": "Ko + Lem + Diamante Perfeito + Armadura Única Excepcional -> Versão de Elite",
    "up_unique_weapon": "Lum + Pul + Esmeralda Perfeita + Arma Única Excepcional -> Versão de Elite",
    "reroll_charm": "3 Gemas Perfeitas + Amuleto Mágico -> Novo Amuleto Mágico do mesmo nível (usado para Skillers)"
}

GAMBLE_RESULTS = [
    "Você encontrou uma Faixa comum... mais sorte na próxima vez, aventureiro.",
    "Ah! Um Anel Raro com algumas resistências decentes. Nada mal!",
    "Um Amuleto mágico... ele brilha fracamente, mas é quase inútil.",
    "SEM SENTIDO! Você jogou seu ouro fora por um monte de metal enferrujado.",
    "MARAVILHOSO! Você encontrou um item Único! (Um homem pode sonhar, não pode?)",
    "Uma bela peça de Conjunto. Talvez você consiga encontrar o resto da coleção?"
]

def get_random_quote():
    return random.choice(QUOTES)

def get_random_lore():
    return random.choice(LORE)

def get_identify_message():
    return random.choice(IDENTIFY_MESSAGES)

def lookup_item(name):
    name = name.lower()
    return ITEMS.get(name, "Não estou familiarizado com este item específico, mas sinto que tem pouco valor...")

def lookup_runeword(name):
    name = name.lower()
    return RUNEWORDS.get(name, "Essa palavra rúnica não está em meus arquivos. Tem certeza de que as runas estão na ordem correta?")

def lookup_recipe(name):
    name = name.lower()
    return RECIPES.get(name, "O Cubo Horádrico não reconhece essa combinação.")

def gamble():
    return random.choice(GAMBLE_RESULTS)
