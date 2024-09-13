from flask import Flask
import requests

app = Flask(__name__)

# Замените на ваш Shopify Store URL и Access Token
SHOPIFY_STORE_URL = ''
ACCESS_TOKEN = ''

# Заголовки для авторизации
HEADERS = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': ACCESS_TOKEN
}

# URL API Shopify для получения продуктов
PRODUCTS_API_URL = f'{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json'


# Функция для получения всех продуктов
def get_products():
    response = requests.get(PRODUCTS_API_URL, headers=HEADERS)
    if response.status_code == 200:
        products = response.json()['products']
        print(f"Получено {len(products)} товаров.")
        return products
    else:
        print(f"Ошибка при получении продуктов: {response.status_code}")
        return []


# Функция для обновления тегов продукта
def update_product_tags(product_id, tags):
    update_url = f'{SHOPIFY_STORE_URL}/admin/api/2024-01/products/{product_id}.json'
    updated_product_data = {
        "product": {
            "id": product_id,
            "tags": tags
        }
    }

    response = requests.put(update_url, headers=HEADERS, json=updated_product_data)
    if response.status_code == 200:
        print(f"Теги продукта {product_id} успешно обновлены на: {tags}")
        return True
    else:
        print(f"Ошибка при обновлении тегов продукта {product_id}: {response.status_code}")
        return False


# Функция для обработки продуктов и вывода тех, которые имеют Compare-at price
def process_products():
    products = get_products()
    products_with_compare_at_price = []
    products_without_compare_at_price = []

    for product in products:
        product_id = product['id']
        product_title = product['title']
        tags = product.get('tags', '')

        # Проверяем наличие Compare-at price для всех вариантов товара
        has_compare_at_price = False
        for variant in product['variants']:
            if variant['compare_at_price']:
                has_compare_at_price = True
                print(f"Товар {product_title} (ID: {product_id}) имеет Compare-at price у варианта {variant['id']}: {variant['compare_at_price']}")
                products_with_compare_at_price.append(product)
                break  # Если хотя бы один вариант имеет compare_at_price, прекращаем проверку других вариантов

        if not has_compare_at_price:
            print(f"Товар {product_title} (ID: {product_id}) не имеет Compare-at price.")
            products_without_compare_at_price.append(product)

    print(f"Найдено {len(products_with_compare_at_price)} товаров с Compare-at price.")
    print(f"Найдено {len(products_without_compare_at_price)} товаров без Compare-at price.")

    # Добавляем тег without_compare для товаров без Compare-at price
    for product in products_without_compare_at_price:
        product_id = product['id']
        tags = product.get('tags', '')

        if 'without_compare' not in tags:
            new_tags = tags + ', without_compare' if tags else 'without_compare'
            print(f"Добавление тега without_compare к товару {product['title']} (ID: {product_id}).")
            update_product_tags(product_id, new_tags)


if __name__ == '__main__':
    print("Запуск проверки товаров с Compare-at price и добавление тегов.")
    process_products()  # Проверяем и выводим товары с Compare-at price, добавляем тег without_compare ко всем остальным
    app.run(debug=True)
