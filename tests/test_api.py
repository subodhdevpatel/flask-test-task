import pytest
from app import app, db
from app.models import Author, Book, Storing
from datetime import datetime


@pytest.fixture
def client():
    """
    Fixture to set up a testing client with a temporary database.

    Yields:
        Flask test client: The test client for making HTTP requests.
    """
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:postgres@db:5432/postgres"
    )
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client


def test_add_author(client):
    data = {"name": "John Doe", "birth_date": "1980-01-01"}
    response = client.post("/author", json=data)
    assert response.status_code == 201
    assert response.get_json()["author_Id"] is not None


def test_get_author(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    db.session.commit()

    response = client.get(f"/author/{author.id}")
    assert response.status_code == 200
    assert response.get_json()["author_Id"] == author.id


def test_add_book(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    db.session.commit()

    data = {
        "barcode": "123456",
        "title": "Test Book",
        "publish_year": 2022,
        "author": "Jane Doe",
    }
    response = client.post("/book", json=data)
    assert response.status_code == 201
    assert response.get_json()["book_id"] is not None


def test_get_book(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    book = Book(barcode="123456", title="Test Book", publish_year=2022, author=author)
    db.session.add(book)
    db.session.commit()

    response = client.get(f"/book/{book.id}")
    assert response.status_code == 200
    assert response.get_json()["key"] == book.id


def test_search_by_barcode(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    book = Book(barcode="123456", title="Test Book", publish_year=2022, author=author)
    db.session.add(book)
    db.session.commit()

    response = client.get(f"/book?barcode=123456")
    assert response.status_code == 200
    assert response.get_json()["found"] == 1
    assert len(response.get_json()["items"]) == 1
    assert response.get_json()["items"][0]["barcode"] == "123456"


def test_add_storing(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    book = Book(barcode="123456", title="Test Book", publish_year=2022, author=author)
    db.session.add(book)
    db.session.commit()

    data = {"book": book.id, "quantity": 10}
    response = client.post("/leftover", json=data)
    assert response.status_code == 201
    assert response.get_json()["success"] is True


def test_get_history(client):
    author = Author(name="Jane Doe", birth_date="1990-01-01")
    db.session.add(author)
    book = Book(barcode="123456", title="Test Book", publish_year=2022, author=author)
    db.session.add(book)
    storing = Storing(book_id=book.id, quantity=10)
    db.session.add(storing)
    db.session.commit()

    response = client.get(f"/history/{book.id}")
    assert response.status_code == 200
    assert response.get_json()["book"]["book_id"] == book.id
    assert len(response.get_json()["history"]) == 1
    assert response.get_json()["history"][0]["quantity"] == 10
