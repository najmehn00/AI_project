First of all if you dont know about Ollama 
watch this youtube video https://www.youtube.com/watch?v=GWB9ApTPTv4&t=5328s

This code is a Flask-based web application that provides an API for submitting and managing API requests in a background process. Let's go through the key components and explain how the code works:

### 1. **Flask App Setup:**
   - **Flask Configuration:**
     The Flask app is configured to use SQLAlchemy, which is an ORM (Object-Relational Mapper) that interacts with a database. In this case, it uses an SQLite database (`api_requests.db`), but it can easily be switched to PostgreSQL or MySQL if needed.
   
   - **Database Model (`APIRequest`):**
     The `APIRequest` model represents an entry in the database. Each request is stored with the following attributes:
     - `id`: Unique identifier for each request.
     - `prompt`: The prompt text sent to the API.
     - `model`: The model used to generate a response (e.g., `llama3`).
     - `status`: The status of the request (`pending`, `completed`, `failed`).
     - `response`: The response data from the API if the request is successful.
     - `error_message`: The error message if the request fails.
     - `created_at`: Timestamp of when the request was created.
     - `completed_at`: Timestamp of when the request was completed.

   - **Database Initialization:**
     The `db.create_all()` statement creates the necessary database tables based on the model when the app starts.

### 2. **Processing API Requests in Background:**
   - The function `process_api_request` processes the request asynchronously in a separate thread. When a new request is made, a background thread is spawned to handle the API request to an external server (`http://87.107.110.5:11434/api/generate`).

   - The function uses the `requests` library to send a POST request with the provided `model` and `prompt`. If the request succeeds, it updates the database with the response and marks the request as `completed`. If there's an error, it updates the request status to `failed` and logs the error message.

   - **Threading:**
     The background processing is done using Python's `threading` module. This allows the main Flask app to remain responsive while the request is being processed in the background.

### 3. **API Endpoints:**

   - **`/generate` (POST):**
     - This endpoint receives a `model` and `prompt` as JSON, creates a new `APIRequest` record in the database, and starts a background thread to process the request.
     - Once the background thread starts, it returns a response with the `request_id`, status `pending`, and a message indicating the request is being processed.

   - **`/status/<int:request_id>` (GET):**
     - This endpoint checks the status of a specific request by its `request_id`.
     - It returns the current status (`pending`, `completed`, or `failed`) and other related details like the `response` (if completed) or `error_message` (if failed).

   - **`/requests` (GET):**
     - This endpoint fetches all requests with optional filtering based on status (`pending`, `completed`, `failed`) and pagination parameters (`page`, `per_page`).
     - It returns a list of all requests, their statuses, and timestamps, along with metadata about pagination.

### 4. **Error Handling:**
   - The app uses `try-except` blocks to handle potential exceptions at various points in the code (e.g., API request failure, database errors, etc.). If an exception occurs, it returns an error message with a `500` HTTP status code.

### 5. **Database Operations:**
   - SQLAlchemy is used to interact with the SQLite database. The `APIRequest.query.get()` method is used to fetch a specific request by its `request_id`, and the `db.session.commit()` method commits changes to the database.

### 6. **Running the Flask App:**
   - Finally, the app is run with `app.run()`, which makes the app available on `http://0.0.0.0:5000/`. It listens for incoming requests and serves responses based on the defined routes.

### **Summary:**
This Flask app acts as an API manager that:
- Accepts user input (`model` and `prompt`).
- Stores the request in a database.
- Processes the request asynchronously in the background.
- Provides an endpoint to check the status of the request.
- Allows retrieving a list of all requests with optional filtering and pagination.

This setup is useful for managing large or time-consuming API requests where processing happens asynchronously, and the user can check the progress later without blocking the main application.
