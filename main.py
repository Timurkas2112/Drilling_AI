from together import Together
from db import init_db, get_table_names, get_column_names
import gradio as gr
import json
from vectorizer import semantic_search
import pandas as pd
import os
from dotenv import load_dotenv 
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import time
load_dotenv()
print("TEST!")
SERVER_URL = os.environ.get("SERVER_URL")

client = Together(api_key=os.environ.get("API_LLAMA"))

def execute_sql_query(conn, query):
    """
    Выполняет SQL-запрос в PostgreSQL и возвращает результаты с названиями столбцов
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            
            # Получаем названия столбцов
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return {
                    "columns": column_names,
                    "data": results,
                    "status": "success"
                }
            else:
                conn.commit()
                return {
                    "status": "success",
                    "rows_affected": cursor.rowcount,
                    "columns": column_names  # Для не-SELECT запросов
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def get_request(user_query, tables, history=None):
    prompt = """
    Ты — помощник для работы с базой данных PostgreSQL. Твоя задача — принимать запросы от пользователя, формировать SQL-запросы и выводить их.
    ### Вот список таблиц, которые существуют в базе данных: {tables}
    ### Пример:
    - user: "Выведи пользователей", query: "SELECT * FROM users"
    - user: "Покажи количество записей в таблице 'orders'", query: "SELECT COUNT(*) FROM orders"
    ### Инструкция:
    1. Выводи только sql запрос, без другой информации
    2. Если что-то не понятно, то можешь уточнить у пользователя
    3. Ты должен выдавать данные только с тех таблиц, которые я тебе отправил, ничего своего не придумывай.
    """

    messages = [
        {"role": "system", "content": prompt.format(tables=tables)},  # Промпт как системное сообщение
    ]

    # Добавляем историю чата, если она есть
    if history:
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})

    # Добавляем текущий запрос пользователя
    messages.append({"role": "user", "content": user_query})

    # Отправляем запрос к модели
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
        messages=messages,
    )

        # Получаем ответ модели
    sql_query = response.choices[0].message.content

    # Обновляем историю чата
    if history is None:
        history = []
    history.append((user_query, sql_query))  # Добавляем текущий запрос и ответ в историю

    return sql_query, history

def process_query():
    """Проверяет и обрабатывает новые сообщения"""
    while True:
        try:
            # Получаем только непроцессированные пользовательские сообщения
            response = requests.get(f"{SERVER_URL}/messages")
            unprocessed = [msg for msg in response.json().get("messages", []) 
                         if msg["sender"] == "user" and not msg.get("processed", False)]
            
            if unprocessed:
                latest_msg = unprocessed[-1]
                user_input = latest_msg["text"]
                
                # Обработка SQL-запроса
                conn = init_db()
                search, docs = semantic_search(user_input)
                sql_query, _ = get_request(user_input, search)
                db_results = execute_sql_query(conn, sql_query)
                answer = f"SQL: {sql_query}\nResults: {json.dumps(db_results, indent=2)}"
                
                # Отправляем ответ
                requests.post(
                    f"{SERVER_URL}/send",
                    json={"text": answer, "sender": "client"},
                    headers={"Content-Type": "application/json"}
                )
                
                # Помечаем сообщение как обработанное
                requests.post(
                    f"{SERVER_URL}/mark_processed/{latest_msg['id']}"
                )
                
        except Exception as e:
            print(f"Ошибка: {e}")
        
        time.sleep(1)  # Проверяем каждую секунду

if __name__ == "__main__":
    print("SQL-ассистент запущен...")
    process_query()