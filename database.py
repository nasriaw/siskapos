import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "siska_malang.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabel Cabang
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT NOT NULL
    )""")

    # 2. Tabel Chart of Accounts (COA) SAK EMKM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coa (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL
    )""")

    # 3. Tabel Produk / Menu F&B
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        cost REAL,
        stock INTEGER,
        FOREIGN KEY(branch_id) REFERENCES branches(id)
    )""")

    # 4. Tabel Transaksi PoS (Header)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        date TEXT,
        cashier TEXT,
        total_amount REAL,
        payment_method TEXT,
        FOREIGN KEY(branch_id) REFERENCES branches(id)
    )""")

    # 5. Tabel Detail Transaksi PoS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        qty INTEGER,
        subtotal REAL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")

    # 6. Tabel Jurnal Akuntansi (Double-Entry)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS general_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_id INTEGER,
        date TEXT,
        description TEXT,
        account_code TEXT,
        debit REAL,
        credit REAL,
        FOREIGN KEY(branch_id) REFERENCES branches(id),
        FOREIGN KEY(account_code) REFERENCES coa(code)
    )""")

    conn.commit()

    # Seed Default Data jika kosong
    cursor.execute("SELECT COUNT(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        # Seed Cabang di Malang
        branches = [
            ("Cabang Ijen", "Jl. Besar Ijen No. 12, Malang"),
            ("Cabang Soekarno-Hatta", "Jl. Soekarno Hatta Indah A-4, Malang"),
            ("Cabang Sawojajar", "Jl. Danau Bratan Raya E2/15, Malang")
        ]
        cursor.executemany("INSERT INTO branches (name, location) VALUES (?, ?)", branches)

        # Seed COA (Chart of Accounts)
        coas = [
            ("111", "Kas & Setara Kas", "Asset"),
            ("114", "Persediaan Barang Dagang", "Asset"),
            ("411", "Pendapatan Penjualan F&B", "Revenue"),
            ("511", "Harga Pokok Penjualan (HPP)", "Expense"),
            ("611", "Biaya Operasional & Utilitas", "Expense")
        ]
        cursor.executemany("INSERT INTO coa (code, name, type) VALUES (?, ?, ?)", coas)

        # Seed Produk F&B Malang
        products = [
            (1, "Ayam Bakar Madu Special", "Makanan", 35000, 20000, 100),
            (1, "Rawon Ngalam", "Makanan", 30000, 18000, 80),
            (1, "Es Teler Durian", "Minuman", 22000, 12000, 150),
            (2, "Ayam Bakar Madu Special", "Makanan", 35000, 20000, 90),
            (2, "Nasi Goreng Kampung", "Makanan", 25000, 14000, 120),
            (2, "Es Teh Solo", "Minuman", 5000, 2000, 300),
            (3, "Bakwan Malang Komplit", "Makanan", 28000, 15000, 110),
            (3, "Kopi Tubruk Robusta Malang", "Minuman", 12000, 4000, 200)
        ]
        cursor.executemany("INSERT INTO products (branch_id, name, category, price, cost, stock) VALUES (?, ?, ?, ?, ?, ?)", products)

        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database SQLite 'siska_malang.db' berhasil diinisialisasi dengan data simulasi F&B Malang.")