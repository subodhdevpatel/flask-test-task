from flask import request, jsonify
from app.db import db, app
from app.models import Author, Book, Storing
from datetime import datetime


# dummmy api for test
@app.route("/", methods=["GET"])
def ping():
    """
    Endpoint to check if the server is running.

    Returns:
        str: 'Pong'
    """
    return "Pong"


# Authors
@app.route("/author", methods=["POST"])
def add_author():
    """
    Endpoint to add a new author.

    Request JSON:
        {
            "name": str,
            "birth_date": str (format: 'YYYY-MM-DD')
        }

    Returns:
        JSON: {"author_Id": int} or {"error": str}, HTTP status code
    """
    data = request.get_json()
    if data["birth_date"] <= datetime(1900, 1, 1).date():
        return (
            jsonify(
                {"error": "Birth date must be greater than January 1, 1900"}
            ),
            201,
        )
    author = Author(name=data["name"], birth_date=data["birth_date"])
    db.session.add(author)
    db.session.commit()
    return jsonify({"author_Id": author.id}), 201


@app.route("/author/<int:author_Id>", methods=["GET"])
def get_author(author_Id):
    """
    Endpoint to get information about a specific author.

    Parameters:
        author_Id (int): Author ID

    Returns:
        JSON: {"author_Id": int, "name": str} or {"error": str}, HTTP status code
    """
    author = Author.query.get(author_Id)
    if not author:
        return jsonify({"error": "Author not found"}), 404
    return jsonify({"author_Id": author.id, "name": author.name})


# Books
@app.route("/book", methods=["POST"])
def add_book():
    """
    Endpoint to add a new book.

    Request JSON:
        {
            "barcode": str,
            "title": str,
            "publish_year": int,
            "author": str (author's name)
        }

    Returns:
        JSON: {"book_id": int, "book_name": str, "author": str} or {"error": str}, HTTP status code
    """
    data = request.get_json()
    author = Author.query.filter(name=data["author"])
    if not author:
        return jsonify({"error": "Author not found"}), 404

    book = Book(
        barcode=data.get("barcode"),
        title=data["title"],
        publish_year=data["publish_year"],
        author=author,
    )
    db.session.add(book)
    db.session.commit()
    return (
        jsonify(
            {
                "book_id": book.id,
                "book_name": book.title,
                "author": book.author,
            }
        ),
        201,
    )


@app.route("/book/<int:key>", methods=["GET"])
def get_book(key):
    """
    Endpoint to get information about a specific book.

    Parameters:
        key (int): Book ID

    Returns:
        JSON: Book information or {"error": str}, HTTP status code
    """
    book = Book.query.get(key)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    storing_info = (
        Storing.query.filter_by(book_id=book.id)
        .order_by(Storing.date.desc())
        .first()
    )
    quantity = storing_info.quantity if storing_info else 0

    return jsonify(
        {
            "key": book.id,
            "barcode": book.barcode,
            "title": book.title,
            "publish_year": book.publish_year,
            "author": {
                "name": book.author.name,
                "birth_date": book.author.birth_date,
            },
            "quantity": quantity,
        }
    )


@app.route("/book", methods=["GET"])
def search_by_barcode():
    """
    Endpoint to search for books by barcode.

    Query Parameter:
        barcode (str): Book barcode

    Returns:
        JSON: {"found": int, "items": List} or {"error": str}, HTTP status code
    """
    barcode = request.args.get("barcode")
    books = Book.query.filter_by(barcode=barcode).all()
    if not books:
        return jsonify({"found": 0, "items": []})

    result = []
    for book in books:
        storing_info = (
            Storing.query.filter_by(book_id=book.id)
            .order_by(Storing.date.desc())
            .first()
        )
        quantity = storing_info.quantity if storing_info else 0
        result.append(
            {
                "key": book.id,
                "barcode": book.barcode,
                "title": book.title,
                "publish_year": book.publish_year,
                "author": {
                    "name": book.author.name,
                    "birth_date": book.author.birth_date,
                },
                "quantity": quantity,
            }
        )

    return jsonify({"found": len(result), "items": result})


# Storing
@app.route("/leftover", methods=["POST"])
def add_storing():
    """
    Endpoint to add information about book leftovers.

    Request JSON:
        {
            "book": int (book ID),
            "quantity": int
        }

    Returns:
        JSON: {"success": bool} or {"error": str}, HTTP status code
    """
    data = request.get_json()
    book = Book.query.get(data["book"])
    if not book:
        return jsonify({"error": "Book not found"}), 404

    storing = Storing(book_id=book.id, quantity=data["quantity"])
    db.session.add(storing)
    db.session.commit()
    return jsonify({"success": True}), 201


@app.route("/history/<int:key>", methods=["GET"])
def get_history(key):
    """
    Endpoint to get the storage history of a specific book.

    Parameters:
        key (int): Book ID

    Returns:
        JSON: Storage history or {"error": str}, HTTP status code
    """
    book = Book.query.get(key)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    history = (
        Storing.query.filter_by(book_id=book.id)
        .order_by(Storing.date.desc())
        .all()
    )
    result = {
        "book": {"book_id": book.id, "title": book.title},
        "history": [
            {"date": entry.date, "quantity": entry.quantity}
            for entry in history
        ],
    }
    return jsonify(result)
