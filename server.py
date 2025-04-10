from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from uuid import uuid4
from datetime import datetime
from db import init_db, get_table_names, get_column_names
from vectorizer import semantic_search
from main import get_request, execute_sql_query
import json

app = Flask(__name__)
CORS(app)

messages = []

def get_sql(user_input):
    conn = init_db()
    search, docs = semantic_search(user_input)
    sql_query, _ = get_request(user_input, search)
    db_results = execute_sql_query(conn, sql_query)
    answer = f"SQL: {sql_query}\nResults: {json.dumps(db_results, indent=2)}"
    return answer


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.json
    if 'text' in data and data['text'].strip():
        msg = {
            "id": str(uuid4()),
            "text": data['text'],
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "sender": data.get("sender", "user"),
            "processed": False  # Новый флаг обработки
        }
        messages.append(msg)
        return jsonify({"status": "OK", "message": msg})
    return jsonify({"error": "Empty message"}), 400

@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify({"messages": messages})

@app.route('/api/mark_processed/<message_id>', methods=['POST'])
def mark_processed(message_id):
    for msg in messages:
        if msg["id"] == message_id:
            msg["processed"] = True
            return jsonify({"status": "OK"})
    return jsonify({"error": "Message not found"}), 404

@app.route('/api/external/send', methods=['POST'])
def external_send():
    data = request.json
    if 'text' in data and data['text'].strip():
        # Обрабатываем сообщение функцией x
        result = get_sql(data['text'])
        
        # Возвращаем только результат, не сохраняя в общий чат
        return jsonify({
            "status": "OK",
            "original_text": data['text'],
            "processed_result": result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    return jsonify({"error": "Empty message"}), 400
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)