from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Iterable
import datetime
import unittest


# ============ Data types ============

class DataType(ABC):
    @abstractmethod
    def validate(self, value: Any) -> bool:
        ...


class IntegerType(DataType):
    def validate(self, value: Any) -> bool:
        return isinstance(value, int)


class StringType(DataType):
    def __init__(self, max_length: Optional[int] = None):
        self.max_length = max_length

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        if self.max_length is not None and len(value) > self.max_length:
            return False
        return True


class BooleanType(DataType):
    def validate(self, value: Any) -> bool:
        return isinstance(value, bool)


class DateType(DataType):
    def validate(self, value: Any) -> bool:
        if isinstance(value, datetime.date):
            return True
        if isinstance(value, str):
            try:
                datetime.date.fromisoformat(value)
                return True
            except ValueError:
                return False
        return False


# ============ Column, Row ============

@dataclass
class Column:
    name: str
    data_type: DataType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[Tuple[str, str]] = None  # (table_name, column_name)

    def validate(self, value: Any) -> bool:
        if value is None:
            return self.nullable
        return self.data_type.validate(value)


class Row:
    def __init__(self, data: Dict[str, Any]):
        self.data: Dict[str, Any] = dict(data)
        self.id: Optional[int] = None

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def __repr__(self) -> str:
        return f"Row(id={self.id}, data={self.data})"


# ============ Table ============

class Table:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns: Dict[str, Column] = {c.name: c for c in columns}
        self.rows: List[Row] = []
        self.next_id: int = 1

    def _validate_row_data(self, row_data: Dict[str, Any]) -> None:
        for column_name, column in self.columns.items():
            value = row_data.get(column_name)
            if not column.validate(value):
                raise ValueError(f"Invalid value for column {column_name}: {value}")

    def insert(self, row_data: Dict[str, Any]) -> Row:
        self._validate_row_data(row_data)
        row = Row(row_data)
        row.id = self.next_id
        self.next_id += 1
        self.rows.append(row)
        return row

    def get_by_id(self, row_id: int) -> Optional[Row]:
        for row in self.rows:
            if row.id == row_id:
                return row
        return None

    def update(self, row_id: int, new_data: Dict[str, Any]) -> Row:
        row = self.get_by_id(row_id)
        if row is None:
            raise KeyError(f"Row with id {row_id} not found")

        candidate = dict(row.data)
        candidate.update(new_data)
        self._validate_row_data(candidate)

        row.data.update(new_data)
        return row

    def delete(self, row_id: int) -> bool:
        row = self.get_by_id(row_id)
        if row is None:
            return False
        self.rows.remove(row)
        return True

    def select_all(self) -> List[Row]:
        return list(self.rows)

    def __iter__(self) -> Iterable[Row]:
        return iter(self.rows)

    def __repr__(self) -> str:
        return f"Table(name={self.name}, rows={len(self.rows)})"


# ============ SimpleQuery ============

class SimpleQuery:
    def __init__(self, table: Iterable[Row]):
        self.table = table
        self.selected_columns: Optional[List[str]] = None
        self.filter_conditions: List[Tuple[str, str, Any]] = []
        self.sort_column: Optional[str] = None
        self.sort_ascending: bool = True

    def select(self, columns: List[str]) -> "SimpleQuery":
        self.selected_columns = columns
        return self

    def where(self, column: str, operator: str, value: Any) -> "SimpleQuery":
        self.filter_conditions.append((column, operator, value))
        return self

    def order_by(self, column: str, ascending: bool = True) -> "SimpleQuery":
        self.sort_column = column
        self.sort_ascending = ascending
        return self

    def _matches(self, row: Row) -> bool:
        for column, operator, value in self.filter_conditions:
            row_value = row[column]
            if operator == "=" and row_value != value:
                return False
            elif operator == ">" and not (row_value > value):
                return False
            elif operator == "<" and not (row_value < value):
                return False
            elif operator == ">=" and not (row_value >= value):
                return False
            elif operator == "<=" and not (row_value <= value):
                return False
            elif operator == "!=" and not (row_value != value):
                return False
        return True

    def _filtered_rows(self) -> List[Row]:
        filtered: List[Row] = []
        for row in self.table:
            if self._matches(row):
                filtered.append(row)

        if self.sort_column is not None:
            def key_func(r: Row):
                v = r[self.sort_column]
                return (v is None, v)
            filtered.sort(key=key_func, reverse=not self.sort_ascending)

        return filtered

    def execute(self) -> List[Row]:
        results: List[Row] = []
        filtered_rows = self._filtered_rows()

        if self.selected_columns:
            for row in filtered_rows:
                new_row_data = {
                    col: row[col]
                    for col in self.selected_columns
                    if col in row.keys()
                }
                results.append(Row(new_row_data))
        else:
            results = filtered_rows

        return results

    # агрегатні функції як розширена можливість
    def count(self) -> int:
        return len(self._filtered_rows())

    def sum(self, column: str) -> Any:
        total = 0
        for row in self._filtered_rows():
            value = row[column]
            if value is not None:
                total += value
        return total

    def avg(self, column: str) -> float:
        values: List[float] = []
        for row in self._filtered_rows():
            value = row[column]
            if value is not None:
                values.append(value)
        if not values:
            return 0.0
        return sum(values) / len(values)


# ============ JoinedTable (inner join) ============

class JoinedTable:
    def __init__(self, left: Table, right: Table, left_column: str, right_column: str, name: Optional[str] = None):
        self.left = left
        self.right = right
        self.left_column = left_column
        self.right_column = right_column
        self.name = name or f"{left.name}_join_{right.name}"
        self.rows: List[Row] = []
        self._build_rows()

    def _build_rows(self) -> None:
        self.rows.clear()
        for l in self.left:
            for r in self.right:
                if l[self.left_column] == r[self.right_column]:
                    data: Dict[str, Any] = {}
                    for k, v in l.items():
                        data[f"{self.left.name}.{k}"] = v
                    for k, v in r.items():
                        data[f"{self.right.name}.{k}"] = v
                    row = Row(data)
                    self.rows.append(row)

    def __iter__(self) -> Iterable[Row]:
        return iter(self.rows)


# ============ Database (Singleton + Factory Method) ============

class Database:
    _instance: Optional["Database"] = None

    def __new__(cls, name: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name: str):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.name = name
        self.tables: Dict[str, Table] = {}
        self._initialized = True

    def create_table(self, name: str, columns: List[Column]) -> Table:
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")

        # перевірка foreign key
        for col in columns:
            if col.foreign_key is not None:
                ref_table_name, ref_column_name = col.foreign_key
                if ref_table_name not in self.tables:
                    raise ValueError(f"Referenced table {ref_table_name} does not exist")
                ref_table = self.tables[ref_table_name]
                if ref_column_name not in ref_table.columns:
                    raise ValueError(f"Referenced column {ref_column_name} does not exist in table {ref_table_name}")
                if not ref_table.columns[ref_column_name].primary_key:
                    raise ValueError("Foreign key must reference a primary key column")

        table = Table(name, columns)
        self.tables[name] = table
        return table

    def get_table(self, name: str) -> Table:
        return self.tables[name]

    # Factory Method: створення таблиці з декларативної схеми
    def create_table_with_factory(self, name: str, schema: Dict[str, Any]) -> Table:
        columns_def = schema.get("columns", [])
        columns: List[Column] = []

        for col_def in columns_def:
            col_name = col_def["name"]
            col_type = col_def["type"]
            nullable = col_def.get("nullable", True)
            primary_key = col_def.get("primary_key", False)
            fk = col_def.get("foreign_key")  # ("table", "column") or None

            if col_type == "int":
                dt = IntegerType()
            elif col_type == "string":
                dt = StringType(col_def.get("max_length"))
            elif col_type == "bool":
                dt = BooleanType()
            elif col_type == "date":
                dt = DateType()
            else:
                raise ValueError(f"Unknown type {col_type}")

            column = Column(
                name=col_name,
                data_type=dt,
                nullable=nullable,
                primary_key=primary_key,
                foreign_key=tuple(fk) if fk is not None else None,
            )
            columns.append(column)

        return self.create_table(name, columns)


# ============ Tests ============

class TestMiniDB(unittest.TestCase):
    def setUp(self):
        # скидати Singleton (для тестів)
        Database._instance = None
        self.db = Database("testdb")

    def test_singleton(self):
        db2 = Database("another")
        self.assertIs(self.db, db2)
        self.assertEqual(self.db.name, "testdb")

    def test_create_tables_and_fk(self):
        users_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "name", "type": "string", "nullable": False, "max_length": 50},
            ]
        }
        users = self.db.create_table_with_factory("users", users_schema)
        self.assertIn("users", self.db.tables)
        self.assertEqual(len(users.columns), 2)

        orders_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "user_id", "type": "int", "nullable": False, "foreign_key": ("users", "id")},
                {"name": "amount", "type": "int", "nullable": False},
            ]
        }
        orders = self.db.create_table_with_factory("orders", orders_schema)
        self.assertIn("orders", self.db.tables)
        self.assertEqual(len(orders.columns), 3)

        bad_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "user_id", "type": "int", "nullable": False, "foreign_key": ("unknown", "id")},
            ]
        }
        with self.assertRaises(ValueError):
            self.db.create_table_with_factory("bad_orders", bad_schema)

    def test_crud_on_table(self):
        users_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "name", "type": "string", "nullable": False, "max_length": 50},
            ]
        }
        users = self.db.create_table_with_factory("users", users_schema)

        r1 = users.insert({"id": 1, "name": "Alice"})
        self.assertEqual(r1.id, 1)
        self.assertEqual(len(users.rows), 1)

        r_get = users.get_by_id(1)
        self.assertIsNotNone(r_get)
        self.assertEqual(r_get["name"], "Alice")

        users.update(1, {"name": "Bob"})
        self.assertEqual(users.get_by_id(1)["name"], "Bob")

        deleted = users.delete(1)
        self.assertTrue(deleted)
        self.assertIsNone(users.get_by_id(1))

    def test_simple_query_and_aggregates(self):
        schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "value", "type": "int", "nullable": False},
            ]
        }
        t = self.db.create_table_with_factory("numbers", schema)
        t.insert({"id": 1, "value": 10})
        t.insert({"id": 2, "value": 20})
        t.insert({"id": 3, "value": 30})

        q = SimpleQuery(t).where("value", ">", 10)
        results = q.execute()
        self.assertEqual(len(results), 2)

        self.assertEqual(q.count(), 2)
        self.assertEqual(q.sum("value"), 50)
        self.assertAlmostEqual(q.avg("value"), 25.0)

    def test_joined_table(self):
        users_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "name", "type": "string", "nullable": False, "max_length": 50},
            ]
        }
        users = self.db.create_table_with_factory("users", users_schema)
        users.insert({"id": 1, "name": "Alice"})
        users.insert({"id": 2, "name": "Bob"})

        orders_schema = {
            "columns": [
                {"name": "id", "type": "int", "nullable": False, "primary_key": True},
                {"name": "user_id", "type": "int", "nullable": False, "foreign_key": ("users", "id")},
                {"name": "amount", "type": "int", "nullable": False},
            ]
        }
        orders = self.db.create_table_with_factory("orders", orders_schema)
        orders.insert({"id": 100, "user_id": 1, "amount": 50})
        orders.insert({"id": 101, "user_id": 1, "amount": 70})
        orders.insert({"id": 102, "user_id": 2, "amount": 30})

        joined = JoinedTable(users, orders, "id", "user_id")
        rows = list(joined)
        self.assertEqual(len(rows), 3)
        self.assertTrue(any(row["users.name"] == "Alice" for row in rows))


if __name__ == "__main__":
    unittest.main()
