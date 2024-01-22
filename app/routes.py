from flask import request, jsonify
from app.db import db, app
from app.models import Author, Book, Storing, History
from datetime import datetime
import pandas as pd
from app.utils import is_positive_integer, is_valid_quantity


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

    # Convert the input birth_date string to a datetime.date object
    birth_date = datetime.strptime(data["birth_date"], '%Y-%m-%d').date()

    if birth_date <= datetime(1900, 1, 1).date():
        return (
            jsonify(
                {"error": "Birth date must be greater than January 1, 1900"}
            ),
            201,
        )
    author = Author(name=data["name"], birth_date=birth_date)
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

    author = Author.query.filter_by(id=data["author"]).first()

    if not author:
        return jsonify({"error": "Author not found"}), 404
    book = Book(
        barcode=data.get("barcode"),
        title=data["title"],
        publish_year=data["publish_year"],
        author_id=author.id,
    )
    db.session.add(book)
    db.session.commit()
    return (
        jsonify(
            {
                "book_id": book.id,
                "book_name": book.title,
                "author": book.author_id,
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


@app.route("/leftover/add", methods=["POST"])
def add_quantity():
    """
    Endpoint to add quantity to book leftovers.

    Request JSON:
        {
            "barcode": str (book barcode),
            "quantity": int
        }

    Returns:
        JSON: {"success": bool} or {"error": str}, HTTP status code
    """
    data = request.get_json()
    if not is_positive_integer(data.get("quantity")):
        return jsonify({"error": "Quantity must be a positive integer"}), 400
    
    book = Book.query.filter_by(barcode=data["barcode"]).first()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    storing = Storing.query.filter_by(book_id=book.id).first()
    quantity = data["quantity"]
    if not storing:
        storing = Storing(book_id=book.id, quantity=quantity)
        db.session.add(storing)
    else:
        storing.quantity += quantity
    db.session.commit()
    storing = Storing.query.filter_by(id=storing.id).first()
    history = History(
        book_id=book.id, quantity=f'+{data["quantity"]}', date=storing.date
    )
    db.session.add(history)
    db.session.commit()

    return jsonify({"success": True}), 201

@app.route("/leftover/remove", methods=["POST"])
def remove_quantity():
    """
    Endpoint to remove quantity from book leftovers.

    Request JSON:
        {
            "barcode": str (book barcode),
            "quantity": int
        }

    Returns:
        JSON: {"success": bool} or {"error": str}, HTTP status code
    """
    data = request.get_json()

    if not is_positive_integer(data.get("quantity")):
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    book = Book.query.filter_by(barcode=data["barcode"]).first()
    
    if not book:
        return jsonify({"error": "Book not found"}), 404

    storing = Storing.query.filter_by(book_id=book.id).first()
    if not storing:
        return jsonify({"error": "Book leftovers not found"}), 404

    if storing.quantity < data["quantity"]:
        return jsonify({"error": "Not enough quantity to remove"}), 400

    storing.quantity -= data["quantity"]
    storing = Storing.query.filter_by(id=storing.id).first()
    history = History(
        book_id=book.id, quantity=f'-{data["quantity"]}', date=storing.date
    )
    db.session.add(history)
    db.session.commit()
    return jsonify({"success": True}), 200


@app.route("/leftover/bulk", methods=["POST"])
def bulk_upload_leftovers():
    """
    Endpoint to save leftovers from Excel or text file.

    Returns:
        JSON: {"success": bool} or {"error": str}, HTTP status code
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
            for index, row in df.iterrows():
                barcode = str(row['barcode']).strip() if not pd.isna(row['barcode']) else None
                quantity = row['quantity']
                if not barcode:
                    continue
                book = Book.query.filter_by(barcode=barcode).first()
                if not book:
                    return jsonify({"error": f"Book not found for barcode '{barcode}' at row {index + 2}"}), 404
                storing = Storing.query.filter_by(book_id=book.id).first()
                if not is_valid_quantity(quantity):
                    return jsonify({"error": f"Invalid quantity at row {index + 2}"}), 400
                
                # resultant query is less than 0 
                if int(storing.quantity)+int(quantity) < 0:
                    return jsonify({"error": f"Invalid quantity at row {index + 2}"}), 400
                
                quantity = int(quantity)
                if not storing:
                    storing = Storing(book_id=book.id, quantity=quantity)
                    db.session.add(storing)
                else:
                    storing.quantity += quantity
                db.session.commit()
                storing = Storing.query.filter_by(id=storing.id).first()
                history = History(
                    book_id=book.id, quantity=quantity, date=storing.date
                )
                db.session.add(history)
                db.session.commit()

        elif file.filename.endswith('.txt'):
            lines = file.read().decode('utf-8').splitlines()
            current_barcode = None
            current_quantity = None
            for index, line in enumerate(lines):
                line = line.strip()
                if line.startswith("BRC"):
                    current_barcode = line[3:]
                elif line.startswith("QNT"):
                    try:
                        current_quantity = int(line[3:])
                        if not is_valid_quantity(current_quantity):
                            return jsonify({"error": f"Invalid quantity at row {index + 1}"}), 400
                    except ValueError:
                        return jsonify({"error": f"Invalid quantity at row {index + 1}"}), 400
                    if current_barcode:
                        book = Book.query.filter_by(barcode=current_barcode).first()
                        if not book:
                            return jsonify({"error": f"Book not found for barcode '{current_barcode}' at row {index + 1}"}), 404
                        storing = Storing.query.filter_by(book_id=book.id).first()
                        if not storing:
                            storing = Storing(book_id=book.id, quantity=current_quantity)
                            db.session.add(storing)
                        else:
                            storing.quantity += current_quantity
                        current_barcode = None
                        current_quantity = None
                        storing = Storing.query.filter_by(id=storing.id).first()
                        history = History(
                            book_id=book.id, quantity=quantity, date=storing.date
                        )
                        db.session.add(history)
                db.session.commit(history)
            db.session.commit()

        else:
            return jsonify({"error": "Invalid file format"}), 400

        return jsonify({"success": True}), 201

    except Exception as e:
        return jsonify({"error": f"Error processing the file: {str(e)}"}), 500


@app.route("/history", methods=["GET"])
def get_history():
    """
    Endpoint to get the storage history based on optional parameters.

    Parameters (optional):
        start (str): Start date in YYYY-MM-DD format
        end (str): End date in YYYY-MM-DD format
        book (int): Book ID

    Returns:
        JSON: Storage history or {"error": str}, HTTP status code
    """
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    book_key = request.args.get("book")

    filters = []
    if start_date:
        filters.append(History.date >= start_date)
    if end_date:
        filters.append(History.date <= end_date)
    if book_key:
        filters.append(History.book_id == book_key)

    query = History.query
    if filters:
        query = query.filter(*filters)

    result = []
    history = query.all()
    book = Book.query.get(book_key)
    result.append(
        {
            "book": {"key": book.id, "title": book.title, "barcode": book.barcode},
            "history": [{"date": entry.date, "quantity": int(entry.quantity)} for entry in history ]
        }
    )
    return jsonify(result)
