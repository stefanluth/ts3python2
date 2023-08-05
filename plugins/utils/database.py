import sqlite3
import threading

TYPE_CONVERSIONS = {
    "BOOLEAN": bool,
    "INTEGER": int,
    "REAL": float,
    "BLOB": lambda x: f"'{x}'",
    "TEXT": lambda x: f"'{x}'",
}


def convert(func, value, typename):
    try:
        return func(value)
    except Exception as e:
        raise ValueError(f"Conversion of {value} to {typename} failed.") from e


class Database:
    """
    A simple database wrapper for SQLite3.
    """

    _lock = threading.Lock()
    tables = {}

    def __init__(self, name):
        """
        Create a new database.

        :param name: The name of the database.
        :type name: str
        """
        self.connection = sqlite3.connect(f"{name}.sqlite", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def close(self):
        """
        Close the database connection.
        """
        self.connection.close()

    def _execute(self, query: str) -> None:
        with self._lock:
            with self.connection:
                self.cursor.execute(query)

    def create_table(self, name: str, columns: dict[str, str]) -> None:
        """
        Create a table in the database.

        :param name: The name of the table.
        :type name: str
        :param columns: The columns of the table. Each column is a tuple of the column name and the column type.
        :type columns: dict[str, str]
        """
        self._execute(f"CREATE TABLE {name} ({', '.join([f'{col} {columns[col]}' for col in columns])})")
        self.tables[name] = columns

    def delete_table(self, name: str) -> None:
        """
        Delete a table from the database.

        :param name: The name of the table.
        :type name: str
        """
        self._execute(f"DROP TABLE {name}")
        self.tables.pop(name)

    def insert(self, table: str, data: dict[str, str]) -> None:
        """
        Insert values into a table.

        :param table: The name of the table.
        :type table: str
        :param data: The data to insert into the table. The keys are the column names and the values are the values to insert.
        :type data: dict[str, str]
        """

        if len(data) == 0:
            raise ValueError("At least one column must be specified.")

        columns = ", ".join(data.keys())
        values = [
            convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), data[col], self.tables[table][col])
            for col in data
        ]

        self._execute(f"INSERT INTO {table} ({columns}) VALUES ({', '.join([str(value) for value in values])})")

    def update(self, table: str, data: dict[str, str], where: dict[str, str]) -> None:
        """
        Update values in a table.

        :param table: The name of the table.
        :type table: str
        :param data: The data to update in the table. The keys are the column names and the values are the values to update.
        :type data: dict[str, str]
        :param where: The WHERE clause of the query.
        :type where: str
        """

        if len(data) == 0:
            raise ValueError("At least one column must be specified.")

        converted_data = [
            f"{col} = {convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), data[col], self.tables[table][col])}"
            for col in data
        ]
        converted_where = [
            f"{col} = {convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), where[col], self.tables[table][col])}"
            for col in where
        ]

        self._execute(f"UPDATE {table} SET {', '.join(converted_data)} WHERE {', '.join(converted_where)}")

    def delete(self, table: str, where: dict[str, str]) -> None:
        """
        Delete values from a table.

        :param table: The name of the table.
        :type table: str
        :param where: The WHERE clause of the query.
        :type where: str
        """

        if len(where) == 0:
            raise ValueError("At least one column must be specified.")

        converted_where = [
            f"{col} = {convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), where[col], self.tables[table][col])}"
            for col in where
        ]

        self._execute(f"DELETE FROM {table} WHERE {', '.join(converted_where)}")

    def select(self, table: str, columns: list[str], where: dict[str, str]) -> list[dict] | None:
        """
        Select values from a table.

        :param table: The name of the table.
        :type table: str
        :param columns: The columns to select.
        :type columns: list[str]
        :param where: The WHERE clause of the query.
        :type where: str
        :return: The selected values.
        :rtype: list[dict]
        """

        if len(columns) == 0:
            raise ValueError("At least one column must be specified.")

        converted_where = [
            f"{col} = {convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), where[col], self.tables[table][col])}"
            for col in where
        ]

        rows = self.cursor.execute(f"SELECT {', '.join(columns)} FROM {table} WHERE {', '.join(converted_where)}")
        result = [dict(row) for row in rows]

        return result if len(result) > 0 else None

    def select_first(self, table: str, columns: list[str], where: dict[str, str]) -> dict | None:
        """
        Select the first value from a table.

        :param table: The name of the table.
        :type table: str
        :param columns: The columns to select.
        :type columns: list[str]
        :param where: The WHERE clause of the query.
        :type where: str
        :return: The selected values.
        :rtype: dict
        """

        if len(columns) == 0:
            raise ValueError("At least one column must be specified.")

        converted_where = [
            f"{col} = {convert(TYPE_CONVERSIONS.get(self.tables[table][col], lambda x: x), where[col], self.tables[table][col])}"
            for col in where
        ]

        rows = self.cursor.execute(
            f"SELECT {', '.join(columns)} FROM {table} WHERE {', '.join(converted_where)}"
        ).fetchone()

        return dict(rows) if rows is not None else None

    def select_all(self, table: str) -> list[dict] | None:
        """
        Select all values from a table.

        :param table: The name of the table.
        :type table: str
        :return: The selected values.
        :rtype: list[dict]
        """
        rows = self.cursor.execute(f"SELECT * FROM {table}")
        result = [dict(row) for row in rows]

        return result if len(result) > 0 else None


if __name__ == "__main__":
    db = Database("test_db")
    db.create_table(
        "test_table",
        {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT",
            "age": "INTEGER",
            "height": "REAL",
            "is_cool": "BOOLEAN",
        },
    )

    db.insert("test_table", {"name": "John", "age": 20, "height": 1.8, "is_cool": True})
    db.insert("test_table", {"name": "Jane", "height": 1.7, "is_cool": False})
    db.insert("test_table", {"name": "Bob"})
    db.insert("test_table", {"name": "Bob"})

    print(db.select_all("test_table"))

    db.update("test_table", {"age": 21, "height": 1.9}, {"name": "John"})
    db.update("test_table", {"age": 5}, {"name": "Bob"})

    print(db.select_all("test_table"))

    db.delete("test_table", {"name": "Jane"})

    print(db.select("test_table", ["name", "age", "height", "is_cool"], {"name": "Bob"}))
    print(db.select_first("test_table", ["name", "age", "height", "is_cool"], {"name": "Bob"}))
    print(db.select_all("test_table"))

    print(db.select("test_table", ["name", "age", "height", "is_cool"], {"age": 123}))
    print(db.select_first("test_table", ["name", "age", "height", "is_cool"], {"age": 123}))

    db.close()
