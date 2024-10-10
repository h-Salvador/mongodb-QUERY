from flask import Flask, request, jsonify
import pymongo
import json
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set up OpenAI client
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)

# Connect to MongoDB
def connect_to_mongo():
    mongo_uri = os.getenv('URI')
    client = pymongo.MongoClient(mongo_uri)
    db = client["interns-db"]
    return db

db = connect_to_mongo()

# Function to interact with OpenAI for generating the MongoDB query
def query_openai(document_structure, user_input):
    messages = [
        {"role": "system", "content": f"Here is the first MongoDB document structure: {document_structure}. Use the exact field names from this structure for the query."},
        {"role": "user", "content": f"""
        Generate a MongoDB query for this request: '{user_input}'. Follow these rules:
        - Use the correct MongoDB operators like $gt, $in, and $or where necessary.
        - Only return the JSON inside 'find()' without db.collection.find or any explanations.
        - If there are multiple conditions, combine them with $and or $or appropriately.
        - Do not include projection fields unless specifically requested.Ensure property name is enclosed in double quotes
        """}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=1000
    )

    return response.choices[0].message.content.strip()

# Function to execute the MongoDB query
def execute_query(query, collection):
    try:
        # Clean up any unnecessary quotes or structures if needed
        query = query.strip()  # Ensure no extra spaces
        query = query.replace("'", '"')  # Replace single quotes with double quotes if necessary
        
        # Parse the query string as JSON
        query_dict = json.loads(query)  # This expects valid JSON, which is the content inside 'find()'

        # Access the correct MongoDB collection and exclude '_class' and '_id' if not needed
        projection = {"_class": 0, "_id": 0}

        # Execute the query on the collection
        result = db[collection].find(query_dict, projection)

        return list(result)  # Convert the cursor to a list
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error while parsing query: {e}")
        return None
    except Exception as e:
        print(f"Error while executing query: {e}")
        return None

# Route to handle the query request
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    user_input = data.get('query', '')
    collection = data.get('collection', '')

    # Fetch the first document structure from the selected MongoDB collection
    first_document = db[collection].find_one()
    document_structure = json.dumps(first_document, default=str)

    # Generate the MongoDB query using OpenAI
    generated_query = query_openai(document_structure, user_input)
    print(f"Generated query: {generated_query}")

    # Execute the query and return the result
    result = execute_query(generated_query, collection)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to execute query"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
