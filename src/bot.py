from utils.assets_utils import (
    combinar_tres_horizontal,
    obtener_imagen_raza,
    obtener_imagen_clase,
    combinar_imagenes_misma_altura,
    redimensionar_por_alto,
)
import discord
from discord.ext import commands
from discord.ext.commands import MemberNotFound
from config import Config
from db import get_database
import random
from dialogs import obtener_dialogo
import re
import logging
import traceback
from utils.llm_provider import get_llm
from datetime import datetime, UTC

'''
TO DO:
-Separate commands in files: apirouter
-Testing
'''

DISCORD_TOKEN = Config.DISCORD_TOKEN
scene_context = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

database = get_database()

RACES = [
    {"nombre": "Humano", "descripcion": "Maestro en sobrevivir a lunes y dragones."},
    {"nombre": "Elfo", "descripcion": "Orejas largas, paciencia corta."},
    {"nombre": "Orco", "descripcion": "Fuerza bruta, higiene opcional."},
    {"nombre": "Enano", "descripcion": "Barba épica, altura simple."},
    {"nombre": "Gnomo", "descripcion": "Pequeño en tamaño, grande en travesuras."},
    {"nombre": "Goblin", "descripcion": "Encorbado, verde y siempre tramando algo."},
    {"nombre": "Trol", "descripcion": "Grande, fuerte y no muy fan del jabón."},
    {"nombre": "Dracónido", "descripcion": "Escamas de dragón, aliento mortecino."},
    {"nombre": "Tiefling", "descripcion": "Cuernos grandes, secretos oscuros."},
    {"nombre": "Mediano", "descripcion": "Nunca rechaza una segunda cena."}
]

CLASSES = [
    {"letra": "A", "nombre": "Guerrero", "descripcion": "Resuelve todo a golpes, incluso los acertijos."},
    {"letra": "B", "nombre": "Mago", "descripcion": "Hace magia... y desaparecer su dinero."},
    {"letra": "C", "nombre": "Druida", "descripcion": "Habla con plantas. Las plantas no responden."},
    {"letra": "D", "nombre": "Ladrón", "descripcion": "Tu bolsa no está segura cerca de él."},
    {"letra": "E", "nombre": "Paladín", "descripcion": "Justicia en armadura... y a veces en exceso."},
    {"letra": "F", "nombre": "Bárbaro", "descripcion": "Grita primero, pregunta después."},
    {"letra": "G", "nombre": "Clérigo", "descripcion": "Reza por ti... y por su suerte en los dados."},
    {"letra": "H", "nombre": "Hechicero", "descripcion": "Poder innato, excusas infinitas."},
    {"letra": "I", "nombre": "Monje", "descripcion": "Golpea rápido, medita lento."},
    {"letra": "J", "nombre": "Explorador", "descripcion": "Siempre perdido, pero con estilo."}
]

OBJETOS_TIENDA = [
    {"nombre": "Elixir de la Bruma", "emoji": "🏺", "precio": 100, "descripcion": "Mejora tu suerte en el duelo: si pierdes, tu fortuna no disminuye."},
    {"nombre": "Hongo del Abismo", "emoji": "🍄", "precio": 100, "descripcion": "Afecta a tu enemigo: si eres derrotado, ambos pierden §100 monedas."},
    {"nombre": "Pizza con yogur", "emoji": "🍕", "precio": 200, "descripcion": "Multiplica tu bolsa: si ganas el duelo, tus monedas se multiplican por tres."},
    {"nombre": "Mano del Despojo", "emoji": "🫳🏻", "precio": 200, "descripcion": "Si ganas el duelo, roba un objeto aleatorio del inventario de tu oponente (que no sea otra Mano)."}
]
OBJETOS_ESPECIALES = [obj["nombre"] for obj in OBJETOS_TIENDA]
IMAGE_HEIGHT = 120
PRECIO_CAMBIO = 200


@bot.command(name="info")
async def info(ctx):
    mensaje = (
        "**Comandos principales:**\n"
        "`!razas` y `!clases` - Consulta las opciones disponibles.\n"
        "`!elegir <número de raza><letra de clase>` - Crea tu perfil eligiendo raza y clase.\n"
        "`!perfil` - Muestra tu perfil actual.\n"
        "`!duelo @usuario` - Reta a otro aventurero a un duelo.\n"
        f"`!cambiar_raza <número>` - Cambia tu raza por un precio.\n"
        f"`!cambiar_clase <letra>` - Cambia tu clase por un precio.\n"
        "`!tienda` - Muestra los objetos que puedes comprar al mercader.\n"
        "`!comprar <número>` - Compra un objeto de la tienda para tu inventario.\n"
        "`!top` - Muestra el top 5 de los jugadores con más monedas.\n"
        "`!narrar` - Escuchad al Dungeon Master, cuya palabra se hace realidad.\n"
        "\n"
        "**Reglas y mecánicas:**\n"
        f"- Cambiar de raza o clase cuesta {PRECIO_CAMBIO} monedas.\n"
        "- Los duelos se resuelven con dados. El ganador obtiene monedas del perdedor.\n"
        "- Si pierdes todas tus monedas, tu perfil será eliminado y deberás empezar de nuevo.\n"
        "- Los objetos de la tienda pueden alterar el resultado de los duelos.\n"
        "- Los objetos se usan automáticamente en los duelos si tienes alguno en tu inventario.\n"
        "- Si tienes más de un objeto especial en tu inventario, se usará uno de manera aleatoria en el duelo.\n"
        "- Solo puedes tener un ejemplar de cada objeto en tu inventario.**\n"
        "- Recuerda, NUNCA retar al bot.**\n"

    )
    await ctx.send(mensaje)

# Hacerlo IA agnostico, usar Langchain

@bot.command(name="narrar")
async def narrar(ctx, *, user_input: str = ""):
    try:
        channel_id = str(ctx.channel.id)
        player_name = ctx.author.display_name

        # Obtén la info del jugador desde la base de datos
        user_doc = await database.read_user(ctx.author.id)
        player_race = user_doc.get("race", {}).get("nombre", "aventurero") if user_doc else "aventurero"
        player_class = user_doc.get("class", {}).get("nombre", "explorador") if user_doc else "explorador"

        # Recupera el contexto anterior de la colección 'scene_context'
        scenes_collection = database.client[Config.DB_NAME]["scene_context"]
        cursor = scenes_collection.find({"channel_id": channel_id}).sort("timestamp", -1).limit(2)
        last_scenes = await cursor.to_list(length=1)
        context = ""
        for scene in reversed(last_scenes):  # Orden cronológico
            context += f"{scene['player_name']}: {scene['user_input']}\nDM: {scene['narration']}\n"

        prompt = (
            f"Eres un Dungeon Master con humor oscuro. "
            f"Estás narrando una partida de rol para {player_name}, su raza y clase son: {player_race} - {player_class}. "
            f"El contexto de las últimas escenas es:\n{context}\n\n"
            f"Usa este contexto para continuar la historia, mencionando a los personajes involucrados y sus acciones recientes. "
            f"No repitas el contexto, sino que avanza la narración, introduce nuevas situaciones, peligros, oportunidades o giros inesperados. "
            f"Puedes iniciar una nueva escena o proponer un punto de giro si la historia lo permite. "
            f"Responde con una narración breve (máximo 3 frases) y siempre involucra activamente al jugador.\n\n"
            f"{player_name}: {user_input}\nDM:"
        )

        # Llama al LLM agnóstico
        try:
            llm = get_llm()
            narration = llm.invoke(prompt)
            if hasattr(narration, "content"):
                narration = narration.content
            narration = str(narration)
            logger.info(f"LLM response for {player_name}: {narration}")
        except Exception as llm_error:
            logger.error(f"Error al invocar el LLM: {llm_error}\n{traceback.format_exc()}")
            narration = "El Dungeon Master está en silencio... (Error al contactar al oráculo)."

        # Construye un diccionario de nombres a menciones
        name_to_mention = {player_name: ctx.author.mention}
        for scene in last_scenes:
            name = scene.get("player_name")
            if name and name not in name_to_mention:
                member = discord.utils.get(ctx.guild.members, display_name=name)
                if member:
                    name_to_mention[name] = member.mention

        # Reemplaza nombres por menciones en la narración
        for name, mention in name_to_mention.items():
            narration = narration.replace(name, mention)

        await scenes_collection.insert_one({
            "channel_id": channel_id,
            "player_name": player_name,
            "player_race": player_race,
            "player_class": player_class,
            "user_input": user_input,
            "narration": narration,
            "timestamp": datetime.now(UTC)
        })

        await ctx.send(narration)
    except Exception as e:
        logger.error(f"Error inesperado en !narrar: {e}\n{traceback.format_exc()}")
        await ctx.send("Ocurrió un error inesperado al narrar la escena. Consulta al desarrollador.")

@bot.command(name="razas")
async def listar_razas(ctx):

    mensaje = "**Las razas disponibles son:**\n\n"
    for i, raza in enumerate(RACES, 1):
        mensaje += f"{i}. **{raza['nombre']}** — {raza['descripcion']}\n"
    await ctx.send(mensaje)

@bot.command(name="clases")
async def listar_clases(ctx):

    mensaje = "**Las sendas del infortunio te ofrecen estas clases:**\n\n"
    for clase in CLASSES:
        mensaje += f"{clase['letra']}. **{clase['nombre']}** — {clase['descripcion']}\n"
    await ctx.send(mensaje)

@bot.command(name="elegir")
async def elegir(ctx, opcion: str):
    # Verifica si el usuario ya tiene un perfil creado
    user = await database.read_user(ctx.author.id)
    if user:
        await ctx.send("Ya tienes un perfil. Si quieres cambiar de raza o clase, usa `!cambiar_raza` o `!cambiar_clase`.")
        return

    # Usa regex para separar el número de raza (uno o más dígitos) y la letra de clase
    match = re.match(r"^(\d+)([A-Za-z])$", opcion)
    if not match:
        # Si el formato es incorrecto, muestra un mensaje de ayuda
        await ctx.send(
            "Formato incorrecto. Usa `!elegir <número de raza><letra de clase>`, por ejemplo: `!elegir 10H`.\n"
            "Consulta las razas con `!razas` y las clases con `!clases`."
        )
        return

    # Extrae el número de raza y la letra de clase del input del usuario
    raza_num = int(match.group(1))      # Número de raza (puede ser de más de un dígito)
    clase_letra = match.group(2).upper()  # Letra de clase, convertida a mayúscula


    try:
        raza_idx = raza_num - 1
        if raza_idx < 0 or raza_idx >= len(RACES):
            raise ValueError
    except ValueError:
        await ctx.send("Tu elección de raza es tan absurda como un dragón vegetariano. Usa `!razas` para ver las opciones.")
        return
    letras = "ABCDEFGHIJ"
    if clase_letra not in letras:
        await ctx.send("¿Clase secreta? No existe. Usa `!clases` para ver las opciones.")
        return
    clase_idx = letras.index(clase_letra)
    clase = CLASSES[clase_idx]
    raza = RACES[raza_idx]

    img_raza = redimensionar_por_alto(obtener_imagen_raza(raza["nombre"]), alto=IMAGE_HEIGHT)
    img_clase = redimensionar_por_alto(obtener_imagen_clase(clase["nombre"]), alto=IMAGE_HEIGHT)
    img_combinada = combinar_imagenes_misma_altura(img_raza, img_clase, alto=IMAGE_HEIGHT)
    await ctx.send(file=discord.File(img_combinada))

    username = ctx.author.name
    await database.create_user(ctx.author.id, username=username, race=raza, user_class=clase)
    await ctx.send(
        f"{ctx.author.mention}, los dioses te vigilan mientras eliges:\n"
        f"Raza: **{raza['nombre']}**\nClase: **{clase['nombre']}**\n"
        f"Se te ha otorgado un tributo celestial por **§1000** monedas\n"
        "Tu destino está sellado... por ahora."
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
        await ctx.send(obtener_dialogo("cambiar_raza_misma", user=ctx.author.mention))
        return
    coins = user.get("coins", 0)
    if coins < PRECIO_CAMBIO:
        await ctx.send(f"Tus bolsillos están tan vacíos como tu esperanza. Necesitas {PRECIO_CAMBIO} monedas para cambiar de raza.")
        return
    new_coins = coins - PRECIO_CAMBIO
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(obtener_dialogo("cambiar_raza_muerte", user=ctx.author.mention))
    else:
        await database.update_user(ctx.author.id, {"race": raza, "coins": new_coins})
        await ctx.send(obtener_dialogo("cambiar_raza_exito", user=ctx.author.mention, raza=raza["nombre"], coins=new_coins))
        imagen_raza = redimensionar_por_alto(obtener_imagen_raza(raza["nombre"]), alto=IMAGE_HEIGHT)
        await ctx.send(file=discord.File(imagen_raza))

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
        await ctx.send(obtener_dialogo("cambiar_clase_misma", user=ctx.author.mention))
        return
    coins = user.get("coins", 0)
    if coins < PRECIO_CAMBIO:
        await ctx.send(f"No tienes suficientes monedas. Necesitas {PRECIO_CAMBIO} monedas para cambiar de clase.")
        return
    new_coins = coins - PRECIO_CAMBIO
    if new_coins <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(obtener_dialogo("cambiar_clase_muerte", user=ctx.author.mention))
    else:
        await database.update_user(ctx.author.id, {"class": clase, "coins": new_coins})
        await ctx.send(obtener_dialogo("cambiar_clase_exito", user=ctx.author.mention, clase=clase["nombre"], coins=new_coins))
        imagen_clase = redimensionar_por_alto(obtener_imagen_clase(clase["nombre"]), alto=IMAGE_HEIGHT)
        await ctx.send(file=discord.File(imagen_clase))

@bot.command(name="perfil")
async def perfil(ctx):
    user = await database.read_user(ctx.author.id)
    if not user:
        await ctx.send(obtener_dialogo("perfil_vacio", user=ctx.author.mention))
        return
    if user.get("coins", 0) <= 0:
        await database.delete_user(ctx.author.id)
        await ctx.send(
            f"{ctx.author.mention}, tu alma ha sido reclamada por la pobreza. "
            "Tu perfil ha sido eliminado. Usa `!elegir <número de raza><letra de clase>` para renacer."
        )
        return
    raza = user.get("race", "No elegida")
    clase = user.get("class", "No elegida")
    coins = user.get("coins", 0)
    inventory = user.get("inventory", [])

    # if isinstance(clase, str):
    #     clase = next((c for c in CLASSES if c["nombre"] == clase), {"nombre": clase})

    # Añade emojis al inventario y muestra cada objeto en una línea
    if inventory:
        inventario_str = "\n" + "\n".join(
        f"- {next((obj['emoji'] for obj in OBJETOS_TIENDA if obj['nombre'] == item), '')} {item}"
        for item in inventory
        )
    else:
        inventario_str = obtener_dialogo(
            "perfil_inventario_vacio",
            user=ctx.author.mention,
            raza=raza["nombre"],
            clase=clase["nombre"],
            coins=coins
        )

    # Imágenes raza y clase
    imagen_raza = obtener_imagen_raza(raza["nombre"])
    imagen_clase = obtener_imagen_clase(clase["nombre"])
    ruta_combinada = combinar_imagenes_misma_altura(imagen_raza, imagen_clase, alto=IMAGE_HEIGHT)
    await ctx.send(file=discord.File(ruta_combinada))

    if inventory:
        await ctx.send(obtener_dialogo(
            "perfil",
            user=ctx.author.mention,
            raza=raza["nombre"],
            clase=clase["nombre"],
            coins=coins,
            inventario=inventario_str
        ))
    else:
        await ctx.send(inventario_str)

@bot.command(name="duelo")
async def duelo(ctx, oponente: discord.Member):

    try:
        retador = await database.read_user(ctx.author.id)
        rival = await database.read_user(oponente.id)

        if not retador:
            await ctx.send(
                f"No puedes desafiar a nadie, porque no eres más que un eco inexistente.\n"
                f"El tiempo de esconderse terminó. Crea tu personaje antes de enfrentar tu inevitable derrota.\n Usa `!elegir <número><letra>`"
            )
            logger.info(f"Duelo fallido: {ctx.author} no tiene perfil.")
            return

        if oponente.id == bot.user.id:
            if retador and retador.get("coins", 0) >= 100:
                await ctx.send(f"{ctx.author.mention}, ¿Tu osadía es fascinante, aventurero, pero todo en este mundo obedece a mi voluntad.\nUn simple aventurero que cree poder dictar las reglas del mundo que yo mismo he tejido.\n¿Acaso no ves que cada piedra, cada sombra y cada monstruo obedece a mi voluntad?\nAprende, mortal, que desafiarme es invocar tu propia condena.")
                await database.update_user(ctx.author.id, {"coins": retador["coins"] - 200})
                await ctx.send("- Un hechizo cae sobre ti y tu fortuna se desvanece: **§200 monedas desaparecen de tu alforja**")

                retador_actualizado = await database.read_user(ctx.author.id)
                if retador_actualizado.get("coins", 0) <= 0:
                    await database.delete_user(ctx.author.id)
                    await ctx.send(
                        f"{ctx.author.mention} ha perdido toda su fortuna y su historia se disuelve en el olvido perpetuo.\n"
                        "Crea un nuevo personaje con `!elegir <número de raza><letra de clase>`."
                    )
            logger.info(f"{ctx.author} intentó retar al bot.")
            return

        if not rival:
            await ctx.send(
                f"Tu rival debe tener su destino escrito en el grimorio. "
                f"{oponente.mention}, deja de esconderte y crea tu personaje antes de enfrentar tu inevitable derrota.\nRenace con `!elegir <número de raza><letra de clase>`"
            )
            return

        if oponente.id == retador["user_id"]:
            await ctx.send(f"¿Puede alguien ser más denso que un slime? No puedes batirte en duelo contigo mismo, aunque sería divertido verte perder. {oponente.mention}, busca un verdadero oponente.")
            return

        if retador.get("coins", 0) < 100 or rival.get("coins", 0) < 100:
            await ctx.send(
                "Ambos deben tener al menos §100 monedas para arriesgar en este duelo. "
                "Sin oro, solo les queda pelear por migajas... o por su dignidad."
            )
            return

        raza_retador = retador.get("race")
        raza_oponente = rival.get("race")

        # Imágenes duelo
        img_retador = redimensionar_por_alto(obtener_imagen_raza(raza_retador["nombre"]), alto=IMAGE_HEIGHT)
        img_versus = redimensionar_por_alto("assets/duelo_versus.png", alto=IMAGE_HEIGHT)
        img_oponente = redimensionar_por_alto(obtener_imagen_raza(raza_oponente["nombre"]), alto=IMAGE_HEIGHT)

        ruta_combinada = combinar_tres_horizontal(img_retador, img_versus, img_oponente, alto=IMAGE_HEIGHT)
        await ctx.send(file=discord.File(ruta_combinada))


        dado_jugador = random.randint(1, 20)
        dado_rival = random.randint(1, 20)
        logger.info(f"Duelo iniciado: {ctx.author} ({dado_jugador}) vs {oponente} ({dado_rival})")

        # Aplica el objeto especial (si existe) y recibe el efecto y mensaje
        efecto, mensaje_objeto = await aplicar_objeto_duelo(
            ctx, retador, rival, dado_jugador, dado_rival, oponente
        )

        # Construye el resultado base
        resultado = (
            f"En la Arena del Azar, {ctx.author.mention} lanza su dado y obtiene **{dado_jugador}**.\n"
            f"{oponente.mention} responde con un giro dramático y saca **{dado_rival}**.\n"
        )

        if mensaje_objeto:
            resultado += mensaje_objeto + "\n"

        if dado_jugador > dado_rival:
            # El retador gana el duelo
            saldo_previo = retador["coins"]

            # LÓGICA
            if efecto == "pizza_yogur":
                ganancia = 100 * 3
                saldo_final = saldo_previo + ganancia
                await database.update_user(ctx.author.id, {"coins": saldo_final})
                nuevo_saldo_oponente = rival["coins"] - 100
                await database.update_user(oponente.id, {"coins": nuevo_saldo_oponente})
            else:
                ganancia = 100
                saldo_final = saldo_previo + ganancia
                await database.update_user(ctx.author.id, {"coins": saldo_final})
                nuevo_saldo_oponente = rival["coins"] - ganancia
                await database.update_user(oponente.id, {"coins":  nuevo_saldo_oponente})

            # LÓGICA MANO
            if efecto == "mano_despojo":
                inventario_oponente = rival.get("inventory", [])
                # Excluye la Mano del robo
                robables = [item for item in inventario_oponente if item != "Mano del Despojo"]
                if robables:
                    robado = random.choice(robables)
                    # Quita el objeto al oponente y lo da al retador
                    inventario_oponente.remove(robado)
                    inventario_retador = retador.get("inventory", [])
                    inventario_retador.append(robado)
                    await database.update_user(oponente.id, {"inventory": inventario_oponente})
                    await database.update_user(ctx.author.id, {"inventory": inventario_retador})
                    # resultado += f"\n¡{ctx.author.mention} ha robado **{robado}** del inventario de {oponente.mention} gracias a la Mano del Despojo!\n"
                    resultado += obtener_dialogo(
                        "duelo_objeto_mano_despojo",
                        user=ctx.author.mention,
                        enemigo=oponente.mention,
                        objeto=robado
                    ) + "\n"
                else:
                    resultado += f"\n{ctx.author.mention} intentó robar un objeto, pero {oponente.mention} no tenía nada útil en su inventario."

            # Construye y envía el mensaje de resultado (incluyendo mensaje_objeto si aplica)
            resultado += (
                f"¡{ctx.author.mention} aplasta a su rival y saquea §{ganancia} monedas de su bolsa! {oponente.mention}, siempre puedes vender tu dignidad para recuperar el oro perdido.\n"
            )
            rival_actualizado = await database.read_user(oponente.id)
            if rival_actualizado and rival_actualizado.get("coins", 0) <= 0:
                await database.delete_user(oponente.id)
                resultado += (
                    f"\n{oponente.mention}, tus arcas se vaciaron en un suspiro, y tu nombre fue borrado de los pergaminos del tiempo.\n"
                    "Deberá crear un nuevo perfil con `!elegir <número de raza><letra de clase>`."
        )


            await ctx.send(resultado)
            return
        elif dado_rival > dado_jugador:
            if efecto == "elixir_bruma":
                # El retador NO pierde monedas
                await database.update_user(ctx.author.id, {"coins": retador["coins"]})
                await database.update_user(oponente.id, {"coins": rival["coins"] + 100})
                #resultado += mensaje_objeto
                await ctx.send(resultado)
                return
            elif efecto == "hongo_abismo":
                coins_jugador = max(1, retador["coins"] - 100)
                coins_oponente = max(1, rival["coins"] - 100)
                # El retador pierde monedas normalmente
                await database.update_user(ctx.author.id, {"coins": coins_jugador})
                # El oponente pierde 100 monedas extra (pero if dado_jugador > enos de 1)
                await database.update_user(oponente.id, {"coins": coins_oponente})
                await ctx.send(resultado)
                return
            else:
                # Lógica normal de duelo
                await database.update_user(ctx.author.id, {"coins": retador["coins"] - 100})
                await database.update_user(oponente.id, {"coins": rival["coins"] + 100})
                nuevo_saldo = retador["coins"] - 100
                await database.update_user(ctx.author.id, {"coins": nuevo_saldo})
                await database.update_user(oponente.id, {"coins": rival["coins"] + 100})
                if nuevo_saldo <= 0:
                    await database.delete_user(ctx.author.id)
                    resultado += (
                        f"\n{ctx.author.mention}, tus arcas se vaciaron en un suspiro, y tu nombre fue borrado de los pergaminos del tiempo.\n"
                        "Deberá crear un nuevo perfil con `!elegir <número de raza><letra de clase>`."
                    )
                else:
                    resultado += (
                        f"¡{oponente.mention} se alza victorioso y roba §100 monedas! "
                        f"{ctx.author.mention}, quizás la suerte te sonría en tu próxima vida... o no."
                    )
                await ctx.send(resultado)
                return
        else:
            # Empate
            resultado += (
                "¡Empate! Los dioses del azar se burlan de ambos y nadie gana ni pierde monedas. "
                "Quizás deberían dedicarse a la poesía."
            )

            await ctx.send(resultado)
    except Exception as e:
        logger.error(f"Error inesperado en duelo: {e}\n{traceback.format_exc()}")

@duelo.error
async def duelo_error(ctx, error):
    if isinstance(error, MemberNotFound):
        await ctx.send("¡Intentaste batirte en duelo con un fantasma! Ese usuario no existe en este servidor o no lo mencionaste correctamente. Usa `!duelo @usuario`.")
        logger.warning(f"MemberNotFound en duelo: {ctx.message.content}")
    else:
        logger.error(f"Error en duelo: {error}\n{traceback.format_exc()}")
        await ctx.send("Algo salió mal en el duelo. Los dioses del código están confundidos.")

# Uso de objetos en duelo
async def aplicar_objeto_duelo(ctx, user, oponente_db, dado_user, dado_oponente, oponente_member):
    inventario = user.get("inventory", [])
    efecto = None
    mensaje = ""

    especiales = [nombre for nombre in OBJETOS_ESPECIALES if nombre in inventario]
    if not especiales:
        return None, ""

    objeto_usado = random.choice(especiales)

    # Elixir de la Bruma: solo se elimina si pierde
    if objeto_usado == "Elixir de la Bruma" and dado_user < dado_oponente:
        inventario.remove(objeto_usado)
        await database.update_user(ctx.author.id, {"inventory": inventario})
        efecto = "elixir_bruma"
        mensaje = obtener_dialogo("duelo_objeto_elixir_bruma", user=ctx.author.mention)
    # Hongo del Abismo: solo se elimina si pierde
    elif objeto_usado == "Hongo del Abismo" and dado_user < dado_oponente:
        inventario.remove(objeto_usado)
        await database.update_user(ctx.author.id, {"inventory": inventario})
        efecto = "hongo_abismo"
        mensaje = obtener_dialogo("duelo_objeto_hongo_abismo", user=ctx.author.mention, enemigo=oponente_member.mention)
    # Pizza con yogur: solo se elimina si gana
    elif objeto_usado == "Pizza con yogur" and dado_user > dado_oponente:
        inventario.remove(objeto_usado)
        await database.update_user(ctx.author.id, {"inventory": inventario})
        efecto = "pizza_yogur"
        mensaje = obtener_dialogo("duelo_objeto_pizza_yogur", user=ctx.author.mention)
    # Mano de Despojo: solo se elimina si gana
    elif objeto_usado == "Mano del Despojo" and dado_user > dado_oponente:
        inventario.remove(objeto_usado)
        await database.update_user(ctx.author.id, {"inventory": inventario})
        efecto = "mano_despojo"
        mensaje = ""
    return efecto, mensaje


@bot.command(name="tienda")
async def mostrar_tienda(ctx):
    intro = obtener_dialogo("tienda_intro", user=ctx.author.mention)
    mensaje = f"{intro}\n\n"
    for i, obj in enumerate(OBJETOS_TIENDA, 1):
        mensaje += f"{i}. **{obj['emoji']} {obj['nombre']}** (§{obj['precio']}): {obj['descripcion']}\n"
    mensaje += "\nUsa `!comprar <número>` para adquirir un objeto."
    imagen_mercader = redimensionar_por_alto("assets/mercader.png", alto=IMAGE_HEIGHT)
    await ctx.send(file=discord.File(imagen_mercader))
    await ctx.send(mensaje)

@bot.command(name="comprar")
async def comprar_objeto(ctx, numero: int):
    try:
        user = await database.read_user(ctx.author.id)
        if not user:
            await ctx.send("Debes tener un perfil antes de comprar. Usa `!elegir <número de raza><letra de clase>` para crearlo.")
            logger.info(f"Intento de compra sin perfil por {ctx.author}")
            return
        if numero < 1 or numero > len(OBJETOS_TIENDA):
            await ctx.send("Ese objeto no existe en la tienda. Usa `!tienda` para ver las opciones.")
            logger.info(f"Intento de compra de objeto inexistente por {ctx.author}: {numero}")
            return
        objeto = OBJETOS_TIENDA[numero - 1]
        inventario = user.get("inventory", [])
        if objeto["nombre"] in inventario:
            imagen_mercader = redimensionar_por_alto("assets/mercader.png", alto=IMAGE_HEIGHT)
            await ctx.send(file=discord.File(imagen_mercader))
            await ctx.send(f"Ya tienes un **{objeto['emoji']} {objeto['nombre']}** en tu inventario. Apacigua tu codicia.")
            logger.info(f"{ctx.author} intentó comprar un objeto repetido: {objeto['nombre']}")
            return
        coins = user.get("coins", 0)
        if coins < objeto["precio"]:
            imagen_mercader = redimensionar_por_alto("assets/mercader.png", alto=IMAGE_HEIGHT)
            await ctx.send(file=discord.File(imagen_mercader))
            await ctx.send(obtener_dialogo("compra_fallo", user=ctx.author.mention))
            logger.info(f"{ctx.author} intentó comprar sin suficiente oro: {objeto['nombre']}")
            return
        nuevo_inventario = inventario + [objeto["nombre"]]
        await database.update_user(ctx.author.id, {
            "coins": coins - objeto["precio"],
            "inventory": nuevo_inventario
        })
        imagen_mercader = redimensionar_por_alto("assets/mercader.png", alto=IMAGE_HEIGHT)
        await ctx.send(file=discord.File(imagen_mercader))
        await ctx.send(
            obtener_dialogo("compra_exito", user=ctx.author.mention, objeto=f"{objeto['emoji']} {objeto['nombre']}")
        )
        logger.info(f"{ctx.author} compró {objeto['nombre']} por {objeto['precio']} monedas.")
    except Exception as e:
        logger.error(f"Error en comprar_objeto: {e}\n{traceback.format_exc()}")
        await ctx.send("Ocurrió un error inesperado al intentar comprar. Contacta al desarrollador.")

@bot.command(name="top")
async def top(ctx, top: int = 3):
    # Obtén todos los usuarios de la base de datos
    usuarios = await database.get_all_users()  # Debes implementar este método si no existe
    if not usuarios:
        await ctx.send("No hay usuarios registrados aún.")
        return

    # Ordena por monedas descendente
    usuarios.sort(key=lambda u: u.get("coins", 0), reverse=True)

    # Agrupa usuarios por cantidad de monedas
    ranking = []
    last_coins = None
    current_group = []
    for user in usuarios:
        coins = user.get("coins", 0)
        if coins != last_coins:
            if current_group:
                ranking.append((last_coins, current_group))
            current_group = [user]
            last_coins = coins
        else:
            current_group.append(user)
    if current_group:
        ranking.append((last_coins, current_group))

    emojis = ["🥇", "🥈", "🥉"]

    # Muestra solo los primeros 'top' puestos
    mensaje = "**El Panteón de la Opulencia:**\n\n"
    puesto = 1
    for idx, (coins, group) in enumerate(ranking[:top], 1):
        nombres = ", ".join(u.get("username", "Desconocido") for u in group)
        if idx <= 3:
            mensaje += f"{emojis[idx - 1]} {nombres} — **§{coins}** monedas\n"
        else:
            mensaje += f"{idx}. {nombres} — **§{coins}** monedas\n"

    await ctx.send(mensaje)

# Configuración logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("rpgbot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RPGbot")

@bot.event
async def on_ready():
    logger.info(f"Bot conectado como {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # await ctx.send("Ese comando no existe. Usa `!info` para ver los comandos disponibles.")
        logger.warning(f"Comando no encontrado: {ctx.message.content}")
    elif isinstance(error, commands.MissingRequiredArgument):
        # await ctx.send("Faltan argumentos en el comando. Consulta `!info`.")
        logger.warning(f"Argumentos faltantes en comando: {ctx.message.content}")
    elif isinstance(error, commands.BadArgument):
        # await ctx.send("Argumento inválido. Consulta el formato en `!info`.")
        logger.warning(f"Argumento inválido en comando: {ctx.message.content}")
    else:
        # await ctx.send("Ocurrió un error inesperado. Consulta al desarrollador.")
        logger.error(f"Error inesperado: {error}\n{traceback.format_exc()}")

bot.run(DISCORD_TOKEN)
