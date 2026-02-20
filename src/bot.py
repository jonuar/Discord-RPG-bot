import os
import discord
from discord.ext import commands
from db import get_database
from config import Config
import random


'''
TODO
-Si el personaje llega 0 monedas muere y debe crear su personaje de nuevo

-Duelo entre personajes tiran un dado y el valor random indicará si viven o mueren,
el que es derrota pierde 100 monedas

-Si la persona con la que se le hace duelo no ha credo su personaje, es mencionado
para que lo haga con instrucciones

-Cambiar diálogos a más fantasía con tintes de humor negro

- Hacer tests

-Desplegar bot en render o AWS

-Implementar compras de inventario.

'''



DISCORD_TOKEN = Config.DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Listas de razas y clases
RACES = [
    "Humano", "Elfo", "Orco", "Enano", "Gnomo", "Goblin", "Trol", "Dracónido", "Tiefling", "Mediano"
]
CLASSES = [
    "Guerrero", "Mago", "Druida", "Ladrón", "Paladín", "Bárbaro", "Clérigo", "Hechicero", "Monje", "Explorador"
]

# Conexión a db
database = get_database()

@bot.command(name="info")
async def mostrar_ayuda(ctx):
    help_text = (
        "**Comandos disponibles:**\n"
        "`!razas` - Muestra la lista de razas disponibles.\n"
        "`!clases` - Muestra la lista de clases disponibles.\n"
        "`!elegir <número><letra>` - Elige raza y clase. Ejemplo: `!elegir 1A`\n"
        "`!perfil` - Muestra tu perfil actual.\n"
        "`!cambiar_raza <raza>` - Cambia tu raza después de crear tu perfil. Cuesta 200 monedas.\n"
        "`!cambiar_clase <clase>` - Cambia tu clase después de crear tu perfil. Cuesta 200 monedas.\n"
        "`!info` - Muestra este mensaje de ayuda."
    )
    await ctx.send(help_text)

@bot.command(name="razas")
async def listar_razas(ctx):
    razas_text = "\n".join([f"{i+1}. {raza}" for i, raza in enumerate(RACES)])
    await ctx.send(f"Razas disponibles:\n{razas_text}")

@bot.command(name="clases")
async def listar_clases(ctx):
    letras = "ABCDEFGHIJ"
    clases_text = "\n".join([f"{letras[i]}. {clase}" for i, clase in enumerate(CLASSES)])
    await ctx.send(f"Clases disponibles:\n{clases_text}")

@bot.command(name="elegir")
async def elegir(ctx, opcion: str):
    if len(opcion) < 2:
        await ctx.send("Formato inválido. Ejemplo: `1C` para Humano y Druida.")
        return

    raza_idx = opcion[0]
    clase_letra = opcion[1].upper()

    try:
        raza_idx = int(raza_idx) - 1
        if raza_idx < 0 or raza_idx >= len(RACES):
            raise ValueError
    except ValueError:
        await ctx.send("Número de raza inválido. Usa `!razas` para ver las opciones.")
        return

    letras = "ABCDEFGHIJ"
    if clase_letra not in letras:
        await ctx.send("Letra de clase inválida. Usa `!clases` para ver las opciones.")
        return
    clase_idx = letras.index(clase_letra)
    clase = CLASSES[clase_idx]
    raza = RACES[raza_idx]

    user = await database.read_user(ctx.author.id)
    username = ctx.author.name
    if not user:
        await database.create_user(ctx.author.id, username=username, race=raza, user_class=clase)
    else:
        await database.update_user(ctx.author.id, {"race": raza, "class": clase})
    await ctx.send(f"{ctx.author.mention}, has elegido:\nRaza: **{raza}**\nClase: **{clase}**.")

@bot.command(name="cambiar_raza")
async def cambiar_raza(ctx, *, raza):
    raza = raza.capitalize()
    if raza not in RACES:
        await ctx.send("Raza no válida. Usa `!razas` para ver las opciones.")
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes elegir tu raza y clase con `!elegir`.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("No tienes suficientes monedas para cambiar de raza (200 requeridas).")
        return
    await database.update_user(ctx.author.id, {"race": raza, "coins": coins - 200})
    await ctx.send(f"{ctx.author.mention}, has cambiado tu raza a **{raza}**. Te quedan **§{coins - 200}** monedas.")

@bot.command(name="cambiar_clase")
async def cambiar_clase(ctx, *, clase):
    clase = clase.capitalize()
    if clase not in CLASSES:
        await ctx.send("Clase no válida. Usa `!clases` para ver las opciones.")
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes elegir tu raza y clase con `!elegir`.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("No tienes suficientes monedas para cambiar de clase (200 requeridas).")
        return
    await database.update_user(ctx.author.id, {"class": clase, "coins": coins - 200})
    await ctx.send(f"{ctx.author.mention}, has cambiado tu clase a **{clase}**. Te quedan **§{coins - 200}** monedas.")

@bot.command(name="perfil")
async def mostrar_perfil(ctx):
    user = await database.read_user(ctx.author.id)
    if not user:
        await ctx.send("No tienes perfil aún. Usa `!elegir_raza` y `!elegir_clase` para crear uno.")
        return
    raza = user.get("race", "No elegida")
    clase = user.get("class", "No elegida")
    coins = user.get("coins", 0)
    # inventory = user.get("inventory", [])
    await ctx.send(
        f"Perfil de {ctx.author.mention}:\n"
        f"Raza: **{raza}**\n"
        f"Clase: **{clase}**\n"
        f"Monedas: **§{coins}**\n"
        f"Inventario: {', '.join(inventory) if inventory else 'Vacío'}"
    )

@bot.command(name="duelo")
async def duelo(ctx, oponente: discord.Member):
    if oponente.id == ctx.author.id:
        await ctx.send("No puedes retarte a ti mismo.")
        return

    jugador = await database.read_user(ctx.author.id)
    rival = await database.read_user(oponente.id)

    if not jugador or not rival:
        await ctx.send("Ambos jugadores deben tener perfil creado con `!elegir`.")
        return

    if jugador.get("coins", 0) < 100 or rival.get("coins", 0) < 100:
        await ctx.send("Ambos jugadores deben tener al menos 100 monedas para participar en un duelo.")
        return

    dado_jugador = random.randint(1, 20)
    dado_rival = random.randint(1, 20)

    resultado = (
        f"{ctx.author.mention} tira el dado y saca **{dado_jugador}**.\n"
        f"{oponente.mention} tira el dado y saca **{dado_rival}**.\n"
    )

    if dado_jugador > dado_rival:
        await database.update_user(ctx.author.id, {"coins": jugador["coins"] + 100})
        await database.update_user(oponente.id, {"coins": rival["coins"] - 100})
        resultado += f"¡{ctx.author.mention} gana el duelo y recibe 100 monedas!"
    elif dado_rival > dado_jugador:
        await database.update_user(ctx.author.id, {"coins": jugador["coins"] - 100})
        await database.update_user(oponente.id, {"coins": rival["coins"] + 100})
        resultado += f"¡{oponente.mention} gana el duelo y recibe 100 monedas!"
    else:
        resultado += "¡Empate! Nadie gana ni pierde monedas."

    await ctx.send(resultado)

bot.run(DISCORD_TOKEN)