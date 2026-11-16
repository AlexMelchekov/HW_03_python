import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper import get_book_data, scrape_books


SAMPLE_BOOK_HTML = """
<html>
    <head>
        <meta name="description" content="Тестовое описание увлекательной книги." />
    </head>
    <body>
        <h1>A Light in the Attic</h1>
        <p class="price_color">£51.77</p>
        <p class="star-rating Three"></p>
        <p class="instock availability">In stock (22 available)</p>
        <table class="table table-striped">
            <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
            <tr><th>Product Type</th><td>Books</td></tr>
        </table>
    </body>
</html>
"""

SAMPLE_CATALOG_HTML = """
<html>
    <body>
        <article class="product_pod">
            <h3><a href="a-light-in-the-attic_1000/index.html">A Light in the Attic</a></h3>
        </article>
        <article class="product_pod">
            <h3><a href="tipping-the-velvet_999/index.html">Tipping the Velvet</a></h3>
        </article>
    </body>
</html>
"""


def test_get_book_data_returns_dict_with_expected_keys(monkeypatch):
    """Проверка, что функция возвращает словарь со всеми ожидаемыми ключами."""
    mock_response = MagicMock()
    mock_response.text = SAMPLE_BOOK_HTML
    monkeypatch.setattr("scraper.requests.get", lambda url: mock_response)

    result = get_book_data("https://books.toscrape.com/")

    assert isinstance(result, dict)
    expected_keys = {
        "Название",
        "Цена",
        "Рейтинг",
        "Наличие",
        "Описание",
        "UPC",
        "Product Type",
    }
    assert expected_keys.issubset(result.keys())


def test_get_book_data_values_accuracy(monkeypatch):
    """Проверка корректности извлечения значений отдельных полей (название, цена, рейтинг)."""
    mock_response = MagicMock()
    mock_response.text = SAMPLE_BOOK_HTML
    monkeypatch.setattr("scraper.requests.get", lambda url: mock_response)

    result = get_book_data("https://books.toscrape.com/")

    assert result["Название"] == "A Light in the Attic"
    assert result["Цена"] == "£51.77"
    assert result["Рейтинг"] == "Three"
    assert result["Наличие"] == "In stock (22 available)"
    assert result["Описание"] == "Тестовое описание увлекательной книги."
    assert result["UPC"] == "a897fe39b1053632"


def test_scrape_books_count_and_structure(monkeypatch):
    """Проверка количества собранных книг и структуры итогового словаря каталога."""
    def mock_get(url):
        response = MagicMock()
        if "catalogue/category" in url:
            response.text = SAMPLE_CATALOG_HTML
        else:
            response.text = SAMPLE_BOOK_HTML
        return response

    monkeypatch.setattr("scraper.requests.get", mock_get)

    catalog_url = "http://books.toscrape.com/catalogue/category/books_1/index.html"
    books = scrape_books(catalog_url, is_save=False)

    assert isinstance(books, dict)
    assert len(books) == 2
    assert "book_1" in books
    assert "book_2" in books
    assert books["book_1"]["Название"] == "A Light in the Attic"


def test_get_book_data_missing_optional_tags(monkeypatch):
    """Проверка обработки страницы, если опциональные теги (цена, рейтинг, описание) отсутствуют."""
    minimal_html = "<html><body><h1>Minimal Book</h1></body></html>"
    mock_response = MagicMock()
    mock_response.text = minimal_html
    monkeypatch.setattr("scraper.requests.get", lambda url: mock_response)

    result = get_book_data("https://books.toscrape.com/")

    assert result["Название"] == "Minimal Book"
    assert result["Цена"] == "Не найдено"
    assert result["Рейтинг"] == "Не найдено"
    assert result["Описание"] == "Описание не найдено"
