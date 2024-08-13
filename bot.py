from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from telegram import Bot
import requests
import asyncio
import os
import time

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
    # Configura opciones de Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecuta el navegador en modo headless
    chrome_options.add_argument("--no-sandbox")  # Opciones adicionales para evitar problemas en entornos de CI/CD
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Configura el WebDriver
    service = Service('/usr/bin/chromedriver')  # Asegúrate de que la ruta sea correcta para tu entorno
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Construye la URL
    url = f"https://es.wallapop.com/app/search?condition=as_good_as_new,good,fair,has_given_it_all&time_filter=lastWeek&min_sale_price=40&max_sale_price=120&keywords={requests.utils.quote(keyword)}&filters_source=quick_filters&longitude=-3.69196&latitude=40.41956&order_by=newest&shipping=true"
    print(f"Buscando en URL: {url}")  # Agregado para verificar la URL

    driver.get(url)
    
    # Espera a que se cargue la página
    driver.implicitly_wait(10)
    
    # Simula desplazamiento para cargar más anuncios
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Espera un poco para que carguen más anuncios
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Extrae los elementos
    ofertas = []
    items = driver.find_elements(By.CSS_SELECTOR, 'a.ItemCardList__item')
    for item in items:
        try:
            # Título
            titulo = item.find_element(By.CSS_SELECTOR, 'p.ItemCard__title').text.strip()
            
            # Precio usando el método de find
            try:
                precio = item.find_element(By.CSS_SELECTOR, 'span.ItemCard__price.ItemCard__price--bold').text.strip()
            except Exception as e:
                print(f"Error al extraer precio: {e}")
                precio = 'Precio no disponible'
            
            # Enlace
            enlace = item.get_attribute('href')
            
            # Filtrar anuncios no deseados
            if not any(exclude_word in titulo.lower() for exclude_word in ["batería", "pantalla", "funda", "cargador", "reparación", "protectora"]):
                ofertas.append({'titulo': titulo, 'precio': precio, 'link': enlace})
            else:
                print(f"Anuncio filtrado: {titulo}")
        except Exception as e:
            print(f"Error al extraer información de un item: {e}")
    
    driver.quit()
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
