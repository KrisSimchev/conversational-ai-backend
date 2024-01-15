import os
from time import sleep
from packaging import version
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
from models import db, User, GeneratedText
from config import Config

# Check OpenAI version is correct
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
OPENAI_API_KEY = Config.OPENAI_API_KEY
if current_version < required_version:
    raise ValueError(f"Error: OpenAI version {openai.__version__}"
                    " is less than the required version 1.1.1")
else:
    print("OpenAI version is compatible.")

secret_key = Config.SECRET_KEY

# Start Flask app
app = Flask(__name__)

db.init_app(app)

# Init client
client = OpenAI(
    api_key=OPENAI_API_KEY)

# Create new assistant or load existing
assistant_id = functions.create_assistant(client)

# Register new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required data"}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    # Create new user
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})

# Login user
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing required data"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Generate token
    token = generate_token(user.id)

    return jsonify({"message": "Login successful"})

# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
    thread = client.beta.threads.create()
    return jsonify({"thread_id": thread.id})

# Generate response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    if not thread_id:
        return jsonify({"error": "Missing thread_id"}), 400

    # Add the user's message to the thread
    client.beta.threads.messages.create(thread_id=thread_id,
                                        role="user",
                                        content=user_input)

    # Run the Assistant
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    # Check if the Run requires action (function call)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                      run_id=run.id)
        if run_status.status == 'completed':
            break
        sleep(1)  # Wait for a second before checking again

    # Retrieve and return the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    return jsonify({"response": response})

# Save generated text to the database
@app.route('/save_text', methods=['POST'])
def save_text():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')
    token = data.get('token')  

    if not thread_id or not user_input or not token:
        return jsonify({"error": "Missing required data"}), 400

    # Validate token
    user_id = validate_token(token)
    if user_id is None:
        return jsonify({"error": "Invalid or expired token"}), 401

    # Add the user's message to the thread
    client.beta.threads.messages.create(thread_id=thread_id,
                                        role="user",
                                        content=user_input)

    # Run the Assistant
    run = client.beta.threads.runs.create(thread_id=thread_id,
                                          assistant_id=assistant_id)

    # Check if the Run requires action (function call)
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                      run_id=run.id)
        if run_status.status == 'completed':
            break
        sleep(1)  # Wait for a second before checking again

    # Retrieve and return the latest message from the assistant
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    # Save the generated text to the database
    user = User.query.get(user_id)
    if user:
        generated_text = GeneratedText(content=response, user_id=user.id)
        db.session.add(generated_text)
        db.session.commit()

    return jsonify({"response": response, "message": "Text saved to the database"})

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
