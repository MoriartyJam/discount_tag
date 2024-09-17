import os
import logging
from flask import Flask, request, jsonify
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

app = Flask(__name__)

# Замените на ваш Shopify Store URL и Access Token
shopify_store_url = os.getenv('SHOPIFY_STORE_URL')
access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

# Проверяем наличие переменных окружения
logging.info(f"Shopify Store URL: {shopify_store_url}")
logging.info(f"Access Token: {access_token}")

# Заголовки для авторизации
HEADERS = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': access_token
}


# Функция для обновления тегов продукта
def update_product_tags(product_id, tags):
    update_url = f'{shopify_store_url}/admin/api/2024-01/products/{product_id}.json'
    updated_product_data = {
        "product": {
            "id": product_id,
            "tags": tags
        }
    }

    logging.info(f"Отправка данных для обновления тегов: {updated_product_data}")

    response = requests.put(update_url, headers=HEADERS, json=updated_product_data)
    if response.status_code == 200:
        logging.info(f"Теги продукта {product_id} успешно обновлены на: {tags}")
    else:
        logging.error(f"Ошибка при обновлении тегов продукта {product_id}: {response.status_code}, {response.text}")


# Обработчик для обновлений продуктов через вебхук
@app.route('/webhook/product-update', methods=['POST'])
def product_update():
    data = request.json
    logging.info(f"Получены данные от вебхука: {data}")

    product_id = data.get('id')
    product_title = data.get('title')
    tags = data.get('tags', '')

    # Проверяем наличие Compare-at price
    has_compare_at_price = any(variant.get('compare_at_price') for variant in data.get('variants', []))

    if has_compare_at_price and 'without_compare' in tags:
        # Удаляем тег without_compare
        new_tags = ', '.join(tag for tag in tags.split(', ') if tag != 'without_compare')
        update_product_tags(product_id, new_tags)
        logging.info(f"Товар {product_title} (ID: {product_id}) обновлен, тег without_compare удален.")
    elif not has_compare_at_price and 'without_compare' not in tags:
        # Если у товара нет Compare-at price и тега нет, добавляем тег without_compare
        new_tags = tags + ', without_compare' if tags else 'without_compare'
        update_product_tags(product_id, new_tags)
        logging.info(f"Товар {product_title} (ID: {product_id}) обновлен, тег without_compare добавлен.")

    return jsonify({"status": "success"}), 200


# Обработчик для создания новых продуктов через вебхук
@app.route('/webhook/product-create', methods=['POST'])
def product_create():
    data = request.json
    logging.info(f"Получены данные о создании нового продукта от вебхука: {data}")

    product_id = data.get('id')
    product_title = data.get('title')
    tags = data.get('tags', '')

    # Проверяем наличие Compare-at price
    has_compare_at_price = any(variant.get('compare_at_price') for variant in data.get('variants', []))

    if not has_compare_at_price:
        # Если у нового товара нет Compare-at price, добавляем тег without_compare
        new_tags = tags + ', without_compare' if tags else 'without_compare'
        update_product_tags(product_id, new_tags)
        logging.info(f"Новый товар {product_title} (ID: {product_id}) создан, тег without_compare добавлен.")

    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

