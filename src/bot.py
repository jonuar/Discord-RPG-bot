import os
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Listas de razas y clases
RACES = [
    "Humano", "Elfo", "Orco", "Enano", "Gnomo", "Goblin", "Trol", "Dracónido", "Tiefling", "Mediano"
]
CLASSES = [
    "Guerrero", "Mago", "Druida", "Ladrón", "Paladín", "Bárbaro", "Clérigo", "Hechicero", "Monje", "Explorador"
]

# Conexión a MongoDB
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client["rpgbot"]
users_collection = db["users"]

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

    # Parse raza (número) y clase (letra)
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

    await users_collection.update_one(
        {"user_id": ctx.author.id},
        {"$set": {"raza": raza, "clase": clase}},
        upsert=True
    )
    await ctx.send(f"Has elegido:\nRaza: **{raza}**\nClase: **{clase}**.")

@bot.command(name="elegir_raza")
async def elegir_raza(ctx, *, raza):
    raza = raza.capitalize()
    if raza not in RACES:
        await ctx.send("Raza no válida. Usa `!razas` para ver las opciones.")
        return
    await users_collection.update_one(
        {"user_id": ctx.author.id},
        {"$set": {"raza": raza}},
        upsert=True
    )
    await ctx.send(f"Has elegido la raza: **{raza}**.")

@bot.command(name="elegir_clase")
async def elegir_clase(ctx, *, clase):
    clase = clase.capitalize()
    if clase not in CLASSES:
        await ctx.send("Clase no válida. Usa `!clases` para ver las opciones.")
        return
    await users_collection.update_one(
        {"user_id": ctx.author.id},
        {"$set": {"clase": clase}},
        upsert=True
    )
    await ctx.send(f"Has elegido la clase: **{clase}**.")

@bot.command(name="perfil")
async def mostrar_perfil(ctx):
    user = await users_collection.find_one({"user_id": ctx.author.id})
    if not user:
        await ctx.send("No tienes perfil aún. Usa `!elegir_raza` y `!elegir_clase` para crear uno.")
        return
    raza = user.get("raza", "No elegida")
    clase = user.get("clase", "No elegida")
    await ctx.send(f"Perfil de {ctx.author.mention}:\nRaza: **{raza}**\nClase: **{clase}**")

bot.run(DISCORD_TOKEN)