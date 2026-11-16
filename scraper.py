import time
from urllib.parse import urljoin
import requests
import schedule
from bs4 import BeautifulSoup


def get_book_data(book_url: str) -> dict:
    """Функция парсинга одной книги
    Args:
        book_url: str - электронный адрес
    Returns: 
        book_data: dict - словарь метаданных книги
    """

    response = requests.get(book_url)
    response.encoding = 'utf-8'
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1").get_text(strip=True)

    price_tag = soup.find("p", class_="price_color")
    price = price_tag.get_text(strip=True) if price_tag else "Не найдено"

    rating_tag = soup.find("p", class_="star-rating")
    rating = rating_tag["class"][1] if rating_tag and len(rating_tag["class"]) > 1 else "Не найдено"
  
    availability_tag = soup.find("p", class_="instock availability")
    availability_text = availability_tag.get_text(strip=True) if availability_tag else ""
    quantity_in_stock = availability_text

    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"].strip() if meta_desc and meta_desc.has_attr("content") else "Описание не найдено"

    product_info = {}
    table = soup.find("table", class_="table table-striped")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True)
                value = td.get_text(strip=True)
                product_info[key] = value

    book_data = {
        "Название": title,
        "Цена": price,
        "Рейтинг": rating,
        "Наличие": quantity_in_stock,
        "Описание": description,
    }
    book_data.update(product_info)

    return book_data


def scrape_books(current_url: str, is_save: bool = True) -> dict:
    """Функция парсинга каталога книг
    Args:
        current_url: str - электронный адрес страницы
        is_save: bool - флаг необходимости сохранения информации в текстовый файл, по умолчанию True
    Returns: 
        books_data: dict - словарь c информацией обо всех книгах каталога
    """

    books_data = {}
    book_counter = 0

    while current_url:
      print(f'Обрабатываю страницу каталога: {current_url}')
      response = requests.get(current_url)
      response.encoding = 'utf-8'
      soup = BeautifulSoup(response.text, 'html.parser')

      # находим все карточки книг на текущей странице каталога
      articles = soup.find_all('article', class_='product_pod')

      for article in articles:
        # Получаем относительную ссылку на страницу книги и превращаем её в полную
        relative_book_url = article.find('h3').find('a')['href']
        book_url = urljoin(current_url, relative_book_url)

        # добавляем информацию по одной книге в словарь
        book_counter += 1
        book_info = get_book_data(book_url) 
        books_data[f'book_{book_counter}'] = book_info

      # переходим на следующую страницу каталога
      next_button = soup.find('li', class_='next')
      if next_button:
        next_page_relative = next_button.find('a')['href']
        current_url = urljoin(current_url, next_page_relative)
      else:
        current_url = None
    
    if is_save:
      with open("books_data.txt", "w", encoding="utf-8") as file:
        file.write(books_data)
    
    return books_data


if __name__ == "__main__":
    current_url = 'http://books.toscrape.com/catalogue/category/books_1/index.html'
    schedule.every().day.at("19:00").do(scrape_books, current_url=current_url)
    print("Планировщик запущен.")
    while True:
       schedule.run_pending()
       time.sleep(30)
    
    # если нужен просто разовый запуск:
    # data = scrape_books(current_url, is_save=True)
    # print(f"Собрано книг: {len(data)}")