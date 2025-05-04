import psycopg2


class DBInterface:
    """
    Интерфейс для подключения и работы с PostgreSQL.
    Обеспечивает автоматическое управление ресурсами через протокол контекстного менеджера.
    """
    
    def __enter__(self):
        """
        Открывает соединение с базой данных и возвращает объект DBInterface.

        :return: Экземпляр DBInterface с открытым соединением.
        """
        self.connection = psycopg2.connect(
            dbname="review_recipient",
            user="postgres",
            password="123",
            host="localhost",
            port="5432"
        )
        self.cursor = self.connection.cursor()
        return self

    def execute(self, query):
        """
        Выполняет SQL-запрос и возвращает первую строку результата.

        :param query: SQL-запрос в виде строки.
        :return: Первая строка результата выполнения запроса.
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def execute_autocommit_query(self, query):
        """
        Выполняет SQL-запрос в режиме autocommit (без использования транзакции).

        :param query: SQL-запрос в виде строки.
        :return: Сообщение об успешном выполнении запроса или описание ошибки.
        """
        original_autocommit = self.connection.autocommit
        try:
            self.connection.autocommit = True
            self.cursor.execute(query)
            return f'{query} выполнен успешно'
        except Exception as e:
            return f'Ошибка выполнения VACUUM FULL: {e}'
        finally:
            self.connection.autocommit = original_autocommit

    def vacuum_full(self):
        """
        Выполняет команду VACUUM FULL для полной очистки и оптимизации базы данных.

        :return: Сообщение об успешном выполнении команды или описание ошибки.
        """
        return self.execute_autocommit_query('VACUUM FULL;')

    def analyze(self):
        """
        Выполняет команду ANALYZE для обновления статистики планировщика запросов.

        :return: Сообщение об успешном выполнении команды или описание ошибки.
        """
        return self.execute_autocommit_query('ANALYZE;')

    def fetch_db_load(self):
        """
        Получает общий объём транзакций.

        Возвращает сумму xact_commit и xact_rollback – суммарное количество транзакций,
        выполненных с момента сброса статистических данных (stats_reset).

        :return: Результат выполнения SQL-запроса из файла db_load.sql.
        """
        with open('db_load.sql', 'r') as sql_file:
            query = sql_file.read()

        return self.execute(query)

    def fetch_process_distribution(self):
        """
        Получает информацию по распределению работы серверных процессов.

        :return: Результат выполнения SQL-запроса из файла process_distribution.sql.
        """
        with open('process_distribution.sql', 'r') as sql_file:
            query = sql_file.read()

        return self.execute(query)

    def fetch_active_transactions_and_queries_duration(self):
        """
        Получает длительность текущих активных транзакций и запросов.

        :return: Результат выполнения SQL-запроса из файла active_transactions_and_queries_duration.sql.
        """
        with open('active_transactions_and_queries_duration.sql', 'r') as sql_file:
            query = sql_file.read()

        return self.execute(query)

    def fetch_most_loaded_tables(self):
        """
        Получает список таблиц с наибольшей нагрузкой.

        :return: Результат выполнения SQL-запроса из файла most_loaded_tables.sql.
        """
        with open('most_loaded_tables.sql', 'r') as sql_file:
            query = sql_file.read()

        return self.execute(query)

    def fetch_index_vs_seq_scan_ratio(self):
        """
        Получает соотношение между количеством индексных и последовательных сканирований таблиц.

        :return: Результат выполнения SQL-запроса из файла index_vs_seq_scan_ratio.sql.
        """
        with open('index_vs_seq_scan_ratio.sql', 'r') as sql_file:
            query = sql_file.read()

        return self.execute(query)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()


with DBInterface() as db:
    print(db.fetch_most_loaded_tables())
