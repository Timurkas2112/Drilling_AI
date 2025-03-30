from together import Together
from db import init_db, get_table_names, get_column_names
import gradio as gr
import json
from vectorizer import semantic_search
import pandas as pd
import os
from dotenv import load_dotenv 
load_dotenv()


with open('tables_3.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
for i in range(len(data)):
    data[i] = str(data[i])

# table_embeddings = create_table_embeddings(data)
print(os.environ.get("API_LLAMA"))
client = Together(api_key=os.environ.get("API_LLAMA"))


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
    tables = get_table_names(conn)


    # user_query = "Покажи данные о users"
    # relevant_tables = find_relevant_tables(user_input, table_embeddings)
    # print("Релевантные таблицы:", relevant_tables)
    # Обработка запроса пользователя
    response, history = get_request(user_input, semantic_search(user_input))
    # Закрытие соединения
    # sql_query, history = get_request(user_input, relevant_tables, history)
    
    # Выполняем запрос с проверкой
    # result, error = execute_query(sql_query)
    return response
    # if error:
    #     return f"Ошибка: {error}"
    # else:
    #     # Форматируем результат для вывода
    #     if isinstance(result, dict):  # Для SELECT запросов
    #         columns = result['columns']
    #         data = result['data']
    #         output = " | ".join(columns) + "\n" + "-"*50 + "\n"
    #         for row in data:
    #             output += " | ".join(str(item) for item in row) + "\n"
    #         return output, history
    #     else:  # Для других запросов
    #         return result


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

conn = init_db()
tables = get_table_names(conn)

# prom = ''
# new_prom = []
# for table in tables:
#     new_prom.append(f'{table}: {get_column_names(conn, table)}') 
#     prom += f"- Таблица: {table}, Столбцы: {get_column_names(conn, table)}\n"
# print(new_prom)
history = None
# while True:
#     query = str(input())
#     user_query = "Покажи данные о users"
#     relevant_tables = find_relevant_tables(query, table_embeddings)
#     print("Релевантные таблицы:", relevant_tables)
    # resp, history = get_request(query, prom)
    # print(resp)
    # print(execute_query(conn, resp))
    