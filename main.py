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


load_dotenv()

client = Together(api_key=os.environ.get("API_LLAMA"))

def execute_sql_query(conn, query):
    """
    Выполняет SQL-запрос в PostgreSQL и возвращает результаты
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            
            # Для SELECT запросов возвращаем результаты
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return results
            # Для других запросов (INSERT, UPDATE и т.д.) возвращаем статус
            else:
                conn.commit()
                return {"status": "success", "rows_affected": cursor.rowcount}
                
    except Exception as e:
        # В случае ошибки возвращаем сообщение об ошибке
        return {"status": "error", "message": str(e)}

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


def chat_interface(user_input, history=None):

    # Подключение к базе данных
    conn = init_db()

    response, history = get_request(user_input, semantic_search(user_input))

    db_results = execute_sql_query(conn, response)

    return str(db_results)


# Запрос пользователя
user_query = "Выведи информацию о завершении скважин за ноябрь 2024 года"


# Создание интерфейса с помощью Gradio
iface = gr.ChatInterface(
    fn=chat_interface,
    title="Чат с моделью для работы с базой данных",
    description="Задавайте вопросы, и модель поможет вам сформировать SQL-запросы."
)

# Запуск интерфейса
iface.launch()
