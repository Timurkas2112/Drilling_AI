import os
from dotenv import load_dotenv
import psycopg2
load_dotenv()

def get_table_names(conn):
    """
    Возвращает список всех таблиц в базе данных.
    """

    cursor = conn.cursor()
    # SQL-запрос для получения списка таблиц
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    # Получаем результаты запроса
    tables = cursor.fetchall()
    # Возвращаем список названий таблиц
    return [table[0] for table in tables]

def get_column_names(conn, table_name):
    """
    Возвращает список всех столбцов для указанной таблицы.
    """
    cursor = conn.cursor()
    # SQL-запрос для получения списка столбцов
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = '{table_name}';
    """)
    # Получаем результаты запроса
    columns = cursor.fetchall()
    # Возвращаем список названий столбцов
    return [column[0] for column in columns]



def init_db():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except psycopg2.Error as e:
        return f"Ошибка при подключении к базе данных: {e}"