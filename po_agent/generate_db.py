import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

DB_NAME = "purchase_orders.db"

def init_db(db_path: str = DB_NAME):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        DROP TABLE IF EXISTS po_items;
        DROP TABLE IF EXISTS purchase_orders;
        DROP TABLE IF EXISTS vendors;
        DROP TABLE IF EXISTS departments;

        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL UNIQUE,
            budget_usd REAL NOT NULL
        );

        CREATE TABLE vendors (
            vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            category TEXT NOT NULL,
            country TEXT NOT NULL,
            rating REAL CHECK(rating >= 1.0 AND rating <= 5.0)
        );

        CREATE TABLE purchase_orders (
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            department_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            expected_delivery_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Draft', 'Pending Approval', 'Approved', 'Fulfilled', 'Cancelled', 'Rejected')),
            total_amount REAL NOT NULL,
            payment_terms TEXT NOT NULL,
            created_by TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(department_id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        );

        CREATE TABLE po_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            item_description TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            received_quantity INTEGER NOT NULL DEFAULT 0,
            shipped_quantity INTEGER NOT NULL DEFAULT 0,
            transit_quantity INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
        );
    """)

    departments = [
        ("Information Technology", 1500000.0),
        ("Operations & Supply Chain", 3000000.0),
        ("Research & Development", 2000000.0),
        ("Marketing & Sales", 1200000.0),
        ("Human Resources", 500000.0),
        ("Facilities & Real Estate", 800000.0),
        ("Finance & Legal", 400000.0)
    ]
    cursor.executemany("INSERT INTO departments (department_name, budget_usd) VALUES (?, ?)", departments)

    categories = [
        "Hardware & Electronics", "Software & SaaS", "Office Supplies",
        "Industrial Machinery", "Raw Materials", "Consulting & Professional Services",
        "Logistics & Freight"
    ]
    vendors = []
    for _ in range(50):
        vendors.append((
            fake.company(),
            random.choice(categories),
            fake.country(),
            round(random.uniform(2.5, 5.0), 2)
        ))
    cursor.executemany("INSERT INTO vendors (vendor_name, category, country, rating) VALUES (?, ?, ?, ?)", vendors)

    print(f"Generating 10,000 Purchase Orders in SQLite database '{db_path}'...")

    statuses = ['Draft', 'Pending Approval', 'Approved', 'Fulfilled', 'Cancelled', 'Rejected']
    status_weights = [0.05, 0.15, 0.25, 0.45, 0.05, 0.05]
    payment_terms = ['Net 30', 'Net 60', 'Net 90', 'Due on Receipt', '2/10 Net 30']

    pos = []
    po_items_list = []
    start_date = datetime.now() - timedelta(days=730)

    for i in range(1, 10001):
        po_number = f"PO-{2023 + (i % 2)}-{i:05d}"
        dept_id = random.randint(1, len(departments))
        vendor_id = random.randint(1, len(vendors))

        ord_date = start_date + timedelta(days=random.randint(0, 720), hours=random.randint(0, 23))
        exp_del_date = ord_date + timedelta(days=random.randint(5, 45))

        status = random.choices(statuses, weights=status_weights)[0]
        p_terms = random.choice(payment_terms)
        created_by = fake.name()

        num_items = random.randint(1, 5)
        po_total = 0.0

        for _ in range(num_items):
            qty = random.randint(1, 100)
            u_price = round(random.uniform(10.0, 2500.0), 2)
            item_total = round(qty * u_price, 2)
            po_total += item_total

            # Realistically calculate shipping and receiving quantities
            received_qty = 0
            shipped_qty = 0
            transit_qty = 0

            if status == 'Fulfilled':
                received_qty = qty
                shipped_qty = qty
                transit_qty = 0
            elif status == 'Approved':
                roll = random.random()
                if roll < 0.15:  # 50% received
                    received_qty = int(qty * 0.5)
                    shipped_qty = qty
                    transit_qty = qty - received_qty
                elif roll < 0.25:  # fully received
                    received_qty = qty
                    shipped_qty = qty
                    transit_qty = 0
                elif roll < 0.50:  # in transit
                    received_qty = 0
                    shipped_qty = qty
                    transit_qty = qty

            po_items_list.append((
                i,
                fake.catch_phrase(),
                qty,
                u_price,
                item_total,
                received_qty,
                shipped_qty,
                transit_qty
            ))

        pos.append((
            po_number,
            dept_id,
            vendor_id,
            ord_date.strftime("%Y-%m-%d %H:%M:%S"),
            exp_del_date.strftime("%Y-%m-%d"),
            status,
            round(po_total, 2),
            p_terms,
            created_by
        ))

    cursor.executemany("""
        INSERT INTO purchase_orders 
        (po_number, department_id, vendor_id, order_date, expected_delivery_date, status, total_amount, payment_terms, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, pos)

    cursor.executemany("""
        INSERT INTO po_items 
        (po_id, item_description, quantity, unit_price, total_price, received_quantity, shipped_quantity, transit_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, po_items_list)

    conn.commit()
    conn.close()
    print(f"Successfully initialized '{db_path}' with 10,000 PO records and line items!")

if __name__ == "__main__":
    init_db()
