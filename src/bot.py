import os
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
# from dotenv import load_dotenv
from db import get_database
from config import Config

# load_dotenv()

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

# Conexión a MongoDB
mongo_client = AsyncIOMotorClient(Config.MONGO_URI)
db = mongo_client[Config.DB_NAME]
users_collection = db[Config.COLLECTION_NAME]
database = get_database()

@bot.command(name="info")
async def mostrar_ayuda(ctx):
    help_text = (
        "**Comandos disponibles:**\n"
        "`!razas` - Muestra la lista de razas disponibles.\n"
        "`!clases` - Muestra la lista de clases disponibles.\n"
        "`!elegir <número><letra>` - Elige raza y clase. Ejemplo: `!elegir 1A`\n"
        "`!perfil` - Muestra tu perfil actual.\n"
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
    if not user:
        await database.create_user(ctx.author.id, race=raza, user_class=clase)
    else:
        await database.update_user(ctx.author.id, {"race": raza, "class": clase})
    await ctx.send(f"Has elegido:\nRaza: **{raza}**\nClase: **{clase}**.")

@bot.command(name="elegir_raza")
async def elegir_raza(ctx, *, raza):
    raza = raza.capitalize()
    if raza not in RACES:
        await ctx.send("Raza no válida. Usa `!razas` para ver las opciones.")
        return
    user = await database.read_user(ctx.author.id)
    if not user:
        await database.create_user(ctx.author.id, race=raza)
    else:
        await database.update_user(ctx.author.id, {"race": raza})
    await ctx.send(f"Has elegido la raza: **{raza}**.")

@bot.command(name="elegir_clase")
async def elegir_clase(ctx, *, clase):
    clase = clase.capitalize()
    if clase not in CLASSES:
        await ctx.send("Clase no válida. Usa `!clases` para ver las opciones.")
        return
    user = await database.read_user(ctx.author.id)
    if not user:
        await database.create_user(ctx.author.id, user_class=clase)
    else:
        await database.update_user(ctx.author.id, {"class": clase})
    await ctx.send(f"Has elegido la clase: **{clase}**.")

@bot.command(name="perfil")
async def mostrar_perfil(ctx):
    user = await database.read_user(ctx.author.id)
    if not user:
        await ctx.send("No tienes perfil aún. Usa `!elegir_raza` y `!elegir_clase` para crear uno.")
        return
    raza = user.get("race", "No elegida")
    clase = user.get("class", "No elegida")
    coins = user.get("coins", 0)
    inventory = user.get("inventory", [])
    await ctx.send(
        f"Perfil de {ctx.author.mention}:\n"
        f"Raza: **{raza}**\n"
        f"Clase: **{clase}**\n"
        f"Monedas: **{coins}**\n"
        f"Inventario: {', '.join(inventory) if inventory else 'Vacío'}"
    )

bot.run(DISCORD_TOKEN)