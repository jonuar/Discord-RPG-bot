import os
import discord
from discord.ext import commands
from db import get_database
from config import Config
import random


'''
TODO


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
        "`!elegir <número><letra>` - Elige tu raza y clase. Ejemplo: `!elegir 1A`\n"
        "`!perfil` - Muestra tu perfil actual.\n"
        "`!cambiar_raza <raza>` - Cambia tu raza después de crear tu perfil. Cuesta 200 monedas. Si llegas a 0 monedas, tu personaje muere y debes crear uno nuevo.\n"
        "`!cambiar_clase <clase>` - Cambia tu clase después de crear tu perfil. Cuesta 200 monedas. Si llegas a 0 monedas, tu personaje muere y debes crear uno nuevo.\n"
        "`!duelo @usuario` - Reta a otro jugador a un duelo de dados. Ambos deben tener perfil y al menos 100 monedas. El ganador recibe 100 monedas del perdedor. Si un jugador queda en 0 monedas, muere y debe crear un nuevo perfil.\n"
        "`!info` - Muestra este mensaje de ayuda.\n\n"
        "Reglas especiales:\n"
        "- Si tu personaje llega a 0 monedas, muere y debes crear uno nuevo con `!elegir`.\n"
        "- Si retas a duelo a alguien sin perfil, será mencionado y recibirá instrucciones para crearlo.\n"
    )
    await ctx.send(help_text)

@bot.command(name="razas")
async def listar_razas(ctx):
    razas_text = "\n".join([f"{i+1}. {raza}" for i, raza in enumerate(RACES)])
    await ctx.send(
        f"En el gran libro de los condenados, las razas disponibles son:\n{razas_text}\n"
        "Elige sabiamente... o no, igual el destino te alcanzará."
    )

@bot.command(name="clases")
async def listar_clases(ctx):
    letras = "ABCDEFGHIJ"
    clases_text = "\n".join([f"{letras[i]}. {clase}" for i, clase in enumerate(CLASSES)])
    await ctx.send(
        f"Las sendas del infortunio te ofrecen estas clases:\n{clases_text}\n"
        "Recuerda: ningún mago ha muerto de viejo, y ningún bárbaro ha muerto de sabio."
    )

@bot.command(name="elegir")
async def elegir(ctx, opcion: str):
    if len(opcion) < 2:
        await ctx.send("¿Intentas engañar al destino? Usa el formato correcto, mortal: `!elegir 1C`.")
        return

    raza_idx = opcion[0]
    clase_letra = opcion[1].upper()

    try:
        raza_idx = int(raza_idx) - 1
        if raza_idx < 0 or raza_idx >= len(RACES):
            raise ValueError
    except ValueError:
        await ctx.send("Tu elección de raza es tan válida como un dragón vegetariano. Usa `!razas` para ver las opciones.")
        return

    letras = "ABCDEFGHIJ"
    if clase_letra not in letras:
        await ctx.send("¿Clase secreta? No existe. Usa `!clases` para ver las opciones.")
        return
    clase_idx = letras.index(clase_letra)
    clase = CLASSES[clase_idx]
    raza = RACES[raza_idx]

    user = await database.read_user(ctx.author.id)
    username = ctx.author.name
    if not user:
        await database.create_user(ctx.author.id, username=username, race=raza, user_class=clase)
        await ctx.send(
            f"{ctx.author.mention}, los dioses se ríen mientras eliges:\n"
            f"Raza: **{raza}**\nClase: **{clase}**\n"
            "Tu destino está sellado... por ahora."
        )
    else:
        await database.update_user(ctx.author.id, {"race": raza, "class": clase})
        await ctx.send(
            f"{ctx.author.mention}, has cambiado tu senda a:\n"
            f"Raza: **{raza}**\nClase: **{clase}**\n"
            "¿Crees que así evitarás la tragedia? Ingenuo."
        )

@bot.command(name="cambiar_raza")
async def cambiar_raza(ctx, *, raza):
    raza = raza.capitalize()
    if raza not in RACES:
        await ctx.send("Esa raza solo existe en tus sueños febriles. Usa `!razas` para ver las opciones reales.")
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes forjar tu destino con `!elegir`. No puedes huir de lo que no eres.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("Tus bolsillos están tan vacíos como tu esperanza. Necesitas 200 monedas para cambiar de raza.")
        return
    new_coins = coins - 200
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, el ritual para cambiar de raza ha drenado tus últimas monedas y tu alma. "
            "Has muerto y tu existencia ha sido borrada de los anales del infortunio. Usa `!elegir` para renacer... si te atreves."
        )
    else:
        await database.update_user(ctx.author.id, {"race": raza, "coins": new_coins})
        await ctx.send(
            f"{ctx.author.mention}, tras un oscuro ritual, ahora eres **{raza}**. "
            f"Te quedan **§{new_coins}** monedas y una nueva identidad que pronto lamentarás."
        )

@bot.command(name="cambiar_clase")
async def cambiar_clase(ctx, *, clase):
    clase = clase.capitalize()
    if clase not in CLASSES:
        await ctx.send("Esa clase solo existe en las pesadillas de los bardos. Usa `!clases` para ver las opciones.")
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes elegir tu destino con `!elegir`. No puedes cambiar lo que nunca fuiste.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("No tienes suficientes monedas. Quizás vender tu alma sea más rentable.")
        return
    new_coins = coins - 200
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, tu intento de cambiar de clase ha vaciado tus arcas y tu existencia. "
            "Has muerto y deberás crear un nuevo perfil con `!elegir`. La próxima vez, elige con más sabiduría... o no."
        )
    else:
        await database.update_user(ctx.author.id, {"class": clase, "coins": new_coins})
        await ctx.send(
            f"{ctx.author.mention}, tras un entrenamiento mortal (literalmente), ahora eres **{clase}**. "
            f"Te quedan **§{new_coins}** monedas y una nueva profesión que probablemente te mate más rápido."
        )

@bot.command(name="perfil")
async def mostrar_perfil(ctx):
    user = await database.read_user(ctx.author.id)
    if not user:
        await ctx.send(
            "Tu existencia es tan vacía como tu perfil. Usa `!elegir` para comenzar tu trágica aventura."
        )
        return
    raza = user.get("race", "No elegida")
    clase = user.get("class", "No elegida")
    coins = user.get("coins", 0)
    inventory = user.get("inventory", [])
    await ctx.send(
        f"**Perfil de {ctx.author.mention}**\n"
        f"Raza: **{raza}**\n"
        f"Clase: **{clase}**\n"
        f"Monedas: **§{coins}**\n"
        f"Inventario: {', '.join(inventory) if inventory else 'Vacío, como tus sueños de grandeza.'}"
    )

@bot.command(name="duelo")
async def duelo(ctx, oponente: discord.Member):
    if oponente.id == ctx.author.id:
        await ctx.send("¿Te has mirado al espejo últimamente? No puedes batirte en duelo contigo mismo, aunque sería divertido verte perder.")
        return

    jugador = await database.read_user(ctx.author.id)
    rival = await database.read_user(oponente.id)

    if not jugador or not rival:
        await ctx.send(
            f"Ambos aventureros deben tener un destino escrito en el grimorio (`!elegir`). "
            f"{oponente.mention}, deja de esconderte y crea tu personaje antes de enfrentar tu inevitable derrota."
        )
        return

    if jugador.get("coins", 0) < 100 or rival.get("coins", 0) < 100:
        await ctx.send(
            "Ambos deben tener al menos 100 monedas para arriesgar en este duelo. "
            "Sin oro, solo les queda pelear por migajas... o por su dignidad."
        )
        return

    dado_jugador = random.randint(1, 20)
    dado_rival = random.randint(1, 20)

    resultado = (
        f"En la arena de la vergüenza, {ctx.author.mention} lanza su dado y obtiene **{dado_jugador}**.\n"
        f"{oponente.mention} responde con un giro dramático y saca **{dado_rival}**.\n"
    )

    if dado_jugador > dado_rival:
        await database.update_user(ctx.author.id, {"coins": jugador["coins"] + 100})
        await database.update_user(oponente.id, {"coins": rival["coins"] - 100})
        # Verifica si el oponente murió
        if rival["coins"] - 100 <= 0:
            await database.delete_user(oponente.id)
            resultado += (
                f"\n{oponente.mention} ha perdido todas sus monedas y su alma ha sido reclamada. "
                "Deberá forjar un nuevo destino con `!elegir`."
            )
        else:
            resultado += (
                f"¡{ctx.author.mention} aplasta a su rival y saquea 100 monedas de su bolsa! "
                f"{oponente.mention}, siempre puedes vender tu dignidad para recuperar el oro perdido."
            )
    elif dado_rival > dado_jugador:
        await database.update_user(ctx.author.id, {"coins": jugador["coins"] - 100})
        await database.update_user(oponente.id, {"coins": rival["coins"] + 100})
        # Verifica si el jugador murió
        if jugador["coins"] - 100 <= 0:
            await database.delete_user(ctx.author.id)
            resultado += (
                f"\n{ctx.author.mention} ha perdido todas sus monedas y ha sido borrado de la historia. "
                "Deberá crear un nuevo perfil con `!elegir`."
            )
        else:
            resultado += (
                f"¡{oponente.mention} se alza victorioso y roba 100 monedas! "
                f"{ctx.author.mention}, quizás la suerte te sonría en tu próxima vida... o no."
            )
    else:
        resultado += (
            "¡Empate! Los dioses del azar se burlan de ambos y nadie gana ni pierde monedas. "
            "Quizás deberían dedicarse a la poesía."
        )

    await ctx.send(resultado)

bot.run(DISCORD_TOKEN)