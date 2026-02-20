# RPGbot

Un bot de Discord para juegos de rol estilo fantasía oscura.

## Requisitos

- Python 3.10+
- MongoDB Atlas o MongoDB local
- Un bot de Discord registrado

## Instalación

1. Clona este repositorio.
2. Crea un entorno virtual:
   ```
   python -m venv venv
   ```
3. Activa el entorno virtual:
   - En Windows:
     ```
     venv\Scripts\activate
     ```
   - En Linux/Mac:
     ```
     source venv/bin/activate
     ```
4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
   ```
   DISCORD_TOKEN=tu_token_de_discord
   MONGO_URI=tu_cadena_de_conexion_mongodb
   DB_NAME=RPGbot-db
   COLLECTION_NAME=players
   ```

## Uso

1. Ejecuta el bot:
   ```
   python src/bot.py
   ```

2. Invita el bot a tu servidor de Discord.

3. Usa los siguientes comandos en Discord:

   - `!razas`  
     Muestra la lista de razas disponibles.

   - `!clases`  
     Muestra la lista de clases disponibles.

   - `!elegir <número><letra>`  
     Elige tu raza y clase. Ejemplo: `!elegir 1A`

   - `!perfil`  
     Muestra tu perfil actual.

   - `!cambiar_raza <raza>`  
     Cambia tu raza después de crear tu perfil. Cuesta 200 monedas. Si tus monedas llegan a 0, tu personaje muere y debes crear uno nuevo.

   - `!cambiar_clase <clase>`  
     Cambia tu clase después de crear tu perfil. Cuesta 200 monedas. Si tus monedas llegan a 0, tu personaje muere y debes crear uno nuevo.

   - `!duelo @usuario`  
     Reta a otro jugador a un duelo de dados. Ambos deben tener al menos 100 monedas y perfil creado. El ganador recibe 100 monedas del perdedor. Si un jugador queda en 0 monedas, muere y debe crear un nuevo perfil.

   - `!info`  
     Muestra la ayuda con todos los comandos y reglas especiales.

## Notas

- Si tu personaje llega a 0 monedas, muere y debes crear un nuevo perfil con `!elegir`.
- Si retas a duelo a alguien que no tiene perfil, el bot lo mencionará y le dará instrucciones para crearlo.
- El bot utiliza un tono de fantasía oscura y humor negro en sus mensajes.
- Asegúrate de que tu bot tenga habilitado el intent de contenido de mensajes en el portal de desarrolladores de Discord.
- El bot almacena los perfiles de los usuarios en la colección y base de datos configuradas en el archivo `.env`.
- Puedes usar MongoDB Atlas o una instancia local de MongoDB para la persistencia.

## Licencia

MIT