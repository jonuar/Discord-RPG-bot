import os
import discord
from discord.ext import commands
from db import get_database
from config import Config
import random
from dialogs import obtener_dialogo


'''
TODO
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
        "\nElige sabiamente... o no, igual el destino te alcanzará."
    )

@bot.command(name="clases")
async def listar_clases(ctx):
    letras = "ABCDEFGHIJ"
    clases_text = "\n".join([f"{letras[i]}. {clase}" for i, clase in enumerate(CLASSES)])
    await ctx.send(
        f"Las sendas del infortunio te ofrecen estas clases:\n{clases_text}\n"
        "\nRecuerda: ningún mago ha muerto de viejo, y ningún bárbaro ha muerto de sabio."
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
async def cambiar_raza(ctx, numero: int):
    if numero < 1 or numero > len(RACES):
        await ctx.send(obtener_dialogo("error_razas"))
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes forjar tu destino con !elegir.")
        return
    raza = RACES[numero - 1]
    if user.get("race") == raza:
        await ctx.send("Ya eres esa raza. El destino no permite cambios redundantes.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("Tus bolsillos están tan vacíos como tu esperanza. Necesitas 200 monedas para cambiar de raza.")
        return
    new_coins = coins - 200
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(obtener_dialogo("cambiar_raza_muerte", user=ctx.author.mention))
    else:
        await database.update_user(ctx.author.id, {"race": raza, "coins": new_coins})
        await ctx.send(obtener_dialogo("cambiar_raza_exito", user=ctx.author.mention, raza=raza, coins=new_coins))

@bot.command(name="cambiar_clase")
async def cambiar_clase(ctx, letra: str):
    letras = "ABCDEFGHIJ"
    letra = letra.upper()
    if letra not in letras:
        await ctx.send(obtener_dialogo("error_clases"))
        return
    user = await database.read_user(ctx.author.id)
    if not user or not user.get("race") or not user.get("class"):
        await ctx.send("Primero debes elegir tu destino con !elegir.")
        return
    clase = CLASSES[letras.index(letra)]
    if user.get("class") == clase:
        await ctx.send("Ya tienes esa clase. El destino no permite cambios redundantes.")
        return
    coins = user.get("coins", 0)
    if coins < 200:
        await ctx.send("No tienes suficientes monedas. Quizás vender tu alma sea más rentable.")
        return
    new_coins = coins - 200
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(obtener_dialogo("cambiar_clase_muerte", user=ctx.author.mention))
    else:
        await database.update_user(ctx.author.id, {"class": clase, "coins": new_coins})
        await ctx.send(obtener_dialogo("cambiar_clase_exito", user=ctx.author.mention, clase=clase, coins=new_coins))

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