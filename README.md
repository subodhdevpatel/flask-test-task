# Flask API README

This is a Flask API with endpoints for managing authors, books, and storing information. Below are instructions on how to set up and run the application using Docker Compose.

## Prerequisites

- Docker
- Docker Compose

## Running the App with Docker Compose

1. Build the Docker images:

    ```bash
    docker-compose build
    ```

2. Start the containers:

    ```bash
    docker-compose up
    ```

3. Access the API at [http://localhost:5000/](http://localhost:5000/)

## API Endpoints

- **Add Author:** POST [http://localhost:5000/author](http://localhost:5000/author)
- **Get Author:** GET [http://localhost:5000/author/{author_Id}](http://localhost:5000/author/{author_Id})
- **Add Book:** POST [http://localhost:5000/book](http://localhost:5000/book)
- **Get Book:** GET [http://localhost:5000/book/{key}](http://localhost:5000/book/{key})
- **Search by Barcode:** GET [http://localhost:5000/book?barcode={barcode}](http://localhost:5000/book?barcode={barcode})
- **Add Storing:** POST [http://localhost:5000/leftover](http://localhost:5000/leftover)
- **Get History:** GET [http://localhost:5000/history/{key}](http://localhost:5000/history/{key})

## Tests

```
pytest tests/test_app.py
```

## Stopping the App

To stop the running containers, use:

```bash
docker-compose down
