from telegram import Bot
import requests
import asyncio
import os
from bs4 import BeautifulSoup

# Configura el bot de Telegram
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')  # Utiliza variables de entorno para el token
bot = Bot(token=bot_token)

# Archivo para almacenar enlaces enviados
ENVIADOS_FILE = 'anuncios_enviados.txt'

# Función para enviar mensajes por Telegram
async def enviar_mensaje(chat_id, texto):
    await bot.send_message(chat_id=chat_id, text=texto)

# Función para cargar los anuncios ya enviados
def cargar_enviados():
    if os.path.exists(ENVIADOS_FILE):
        with open(ENVIADOS_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

# Función para guardar nuevos anuncios enviados
def guardar_enviado(enlace):
    with open(ENVIADOS_FILE, 'a') as f:
        f.write(enlace + '\n')

# Función para buscar ofertas en Wallapop
def buscar_ofertas(keyword):
    # Construye la URL
    url = f"https://es.wallapop.com/app/search?condition=as_good_as_new,good,fair,has_given_it_all&time_filter=lastWeek&min_sale_price=40&max_sale_price=120&keywords={requests.utils.quote(keyword)}&filters_source=quick_filters&longitude=-3.69196&latitude=40.41956&order_by=newest&shipping=true"
    print(f"Buscando en URL: {url}")  # Agregado para verificar la URL

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extrae los elementos
    ofertas = []
    items = soup.select('a.ItemCardList__item')
    
    for item in items:
        try:
            # Título
            titulo = item.select_one('p.ItemCard__title').text.strip()
            
            # Precio
            try:
                precio = item.select_one('span.ItemCard__price.ItemCard__price--bold').text.strip()
            except Exception as e:
                print(f"Error al extraer precio: {e}")
                precio = 'Precio no disponible'
            
            # Enlace
            enlace = item['href']
            
            # Filtrar anuncios no deseados
            if not any(exclude_word in titulo.lower() for exclude_word in ["batería", "pantalla", "funda", "cargador", "reparación", "protectora"]):
                ofertas.append({'titulo': titulo, 'precio': precio, 'link': enlace})
            else:
                print(f"Anuncio filtrado: {titulo}")
        except Exception as e:
            print(f"Error al extraer información de un item: {e}")
    
    return ofertas

# Función para notificar ofertas por Telegram
async def notificar_ofertas(chat_id):
    enviados = cargar_enviados()
    ofertas = buscar_ofertas("iphone 11")
    if ofertas:
        for oferta in ofertas:
            if oferta['link'] not in enviados:
                mensaje = f"{oferta['titulo']} - {oferta['precio']}\nLink: {oferta['link']}"
                await enviar_mensaje(chat_id, mensaje)
                guardar_enviado(oferta['link'])
            else:
                print(f"Anuncio ya enviado: {oferta['link']}")
    else:
        await enviar_mensaje(chat_id, "No se encontraron ofertas para 'iPhone 11'.")

async def main():
    chat_id = int(os.getenv('TELEGRAM_CHAT_ID'))  # Utiliza variables de entorno para el chat_id
    await notificar_ofertas(chat_id)

if __name__ == '__main__':
    asyncio.run(main())
