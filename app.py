"""
Aplikasi Utama SISKA v2.1 - Sistem Informasi Manajemen Terintegrasi Akuntansi dan PoS untuk UMKM
Pengembang: M Nasri AW - email: nasriaw@gmail.com
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
from database import init_db, get_connection
from telegram_bot import send_telegram_notification

# Inisialisasi DB
init_db()

st.set_page_config(
    page_title="SISKA v2.1 - Sistem Informasi Keuangan & PoS UMKM",
    page_icon="📊",
    layout="wide"
)

# --- SIDEBAR NAVIGASI & KONFIGURASI CABANG ---
st.sidebar.title("🏢 SISKA v2.1 Malang")
st.sidebar.caption("Manajemen Terintegrasi Akuntansi & PoS")
st.sidebar.markdown("---")
st.sidebar.markdown("**Pengembang:**\nM Nasri AW\n📧 `nasriaw@gmail.com`")
st.sidebar.markdown("---")

conn = get_connection()
branches_df = pd.read_sql("SELECT * FROM branches", conn)
branch_dict = dict(zip(branches_df['name'], branches_df['id']))

selected_branch_name = st.sidebar.selectbox("Pilih Cabang Aktif:", list(branch_dict.keys()))
active_branch_id = branch_dict[selected_branch_name]

st.sidebar.divider()
menu = st.sidebar.radio("Navigasi Menu", [
    "🛒 Kasir (PoS)", 
    "📦 Manajemen Stok", 
    "📒 Jurnal & Akuntansi", 
    "📈 Laporan Laba Rugi", 
    "🤖 Pengaturan Telegram Bot"
])

# Ambil konfigurasi bot dari session state jika ada
if 'bot_token' not in st.session_state:
    st.session_state['bot_token'] = ""
if 'chat_id' not in st.session_state:
    st.session_state['chat_id'] = ""

# --- HALAMAN 1: KASIR (PoS) ---
if menu == "🛒 Kasir (PoS)":
    st.title(f"🛒 Titik Penjualan (PoS) - {selected_branch_name}")
    st.markdown("Catat transaksi harian pelanggan dan sistem akan otomatis menghasilkan jurnal akuntansi ganda.")

    # Ambil produk berdasarkan cabang aktif
    products_df = pd.read_sql(f"SELECT * FROM products WHERE branch_id = {active_branch_id}", conn)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Daftar Menu Tersedia")
        selected_items = []
        
        for idx, row in products_df.iterrows():
            c1, c2, c3, c4 = st.columns([3, 2, 1, 2])
            c1.write(f"**{row['name']}**")
            c2.write(f"Rp {row['price']:,.0f}")
            c3.write(f"Stok: {row['stock']}")
            qty = c4.number_input(f"Qty_{row['id']}", 0, row['stock'], 0, key=f"qty_{row['id']}")
            if qty > 0:
                selected_items.append({
                    "product_id": row['id'],
                    "name": row['name'],
                    "price": row['price'],
                    "cost": row['cost'],
                    "qty": qty,
                    "subtotal": row['price'] * qty,
                    "total_cost": row['cost'] * qty
                })

    with col2:
        st.subheader("Ringkasan Pesanan")
        cashier_name = st.text_input("Nama Kasir:", "Kasir 1")
        payment_method = st.selectbox("Metode Pembayaran:", ["Tunai", "QRIS / Transfer", "GoPay/OVO"])

        if selected_items:
            cart_df = pd.DataFrame(selected_items)
            st.dataframe(cart_df[['name', 'qty', 'subtotal']], hide_index=True)
            
            total_belanja = cart_df['subtotal'].sum()
            total_hpp = cart_df['total_cost'].sum()
            st.markdown(f"### **Total: Rp {total_belanja:,.0f}**")

            if st.button("Proses Transaksi & Jurnal Otomatis", type="primary"):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor = conn.cursor()
                
                # 1. Insert Transaksi Header
                cursor.execute("""
                INSERT INTO transactions (branch_id, date, cashier, total_amount, payment_method)
                VALUES (?, ?, ?, ?, ?)
                """, (active_branch_id, now_str, cashier_name, total_belanja, payment_method))
                tx_id = cursor.lastrowid

                # 2. Insert Transaksi Detail & Kurangi Stok
                for item in selected_items:
                    cursor.execute("""
                    INSERT INTO transaction_items (transaction_id, product_id, qty, subtotal)
                    VALUES (?, ?, ?, ?)
                    """, (tx_id, item['product_id'], item['qty'], item['subtotal']))
                    
                    cursor.execute("""
                    UPDATE products SET stock = stock - ? WHERE id = ?
                    """, (item['qty'], item['product_id']))

                # 3. OTOMATISASI PENJURNALAN AKUNTANSI (Double-Entry Bookkeeping)
                cursor.execute("INSERT INTO general_journal (branch_id, date, description, account_code, debit, credit) VALUES (?, ?, ?, ?, ?, ?)",
                               (active_branch_id, now_str, f"Penjualan POS #{tx_id}", "111", total_belanja, 0))
                cursor.execute("INSERT INTO general_journal (branch_id, date, description, account_code, debit, credit) VALUES (?, ?, ?, ?, ?, ?)",
                               (active_branch_id, now_str, f"Penjualan POS #{tx_id}", "411", 0, total_belanja))
                
                cursor.execute("INSERT INTO general_journal (branch_id, date, description, account_code, debit, credit) VALUES (?, ?, ?, ?, ?, ?)",
                               (active_branch_id, now_str, f"HPP Penjualan POS #{tx_id}", "511", total_hpp, 0))
                cursor.execute("INSERT INTO general_journal (branch_id, date, description, account_code, debit, credit) VALUES (?, ?, ?, ?, ?, ?)",
                               (active_branch_id, now_str, f"HPP Penjualan POS #{tx_id}", "114", 0, total_hpp))

                conn.commit()
                st.success(f"Transaksi #{tx_id} berhasil disimpan & dijurnal otomatis!")

                if st.session_state['bot_token'] and st.session_state['chat_id']:
                    msg = f"🔔 *Notifikasi Transaksi Baru*\n🏢 {selected_branch_name}\n💰 Total: Rp {total_belanja:,.0f}\n💳 Metode: {payment_method}\n🕒 {now_str}"
                    success, res_msg = send_telegram_notification(st.session_state['bot_token'], st.session_state['chat_id'], msg)
                    if success:
                        st.toast("Notifikasi Telegram terkirim!")
        else:
            st.info("Silakan pilih kuantiti menu di sebelah kiri.")

# --- HALAMAN 2: MANAJEMEN STOK ---
elif menu == "📦 Manajemen Stok":
    st.title(f"📦 Manajemen Persediaan - {selected_branch_name}")
    products_df = pd.read_sql(f"SELECT * FROM products WHERE branch_id = {active_branch_id}", conn)
    st.dataframe(products_df, use_container_width=True)

# --- HALAMAN 3: JURNAL & AKUNTANSI ---
elif menu == "📒 Jurnal & Akuntansi":
    st.title(f"📒 Buku Jurnal Umum (Double-Entry) - {selected_branch_name}")
    query = f"""
    SELECT j.date, j.description, c.name as account_name, j.debit, j.credit 
    FROM general_journal j 
    JOIN coa c ON j.account_code = c.code 
    WHERE j.branch_id = {active_branch_id}
    ORDER BY j.id DESC
    """
    journal_df = pd.read_sql(query, conn)
    if not journal_df.empty:
        st.dataframe(journal_df, use_container_width=True)
    else:
        st.info("Belum ada catatan jurnal untuk cabang ini.")

# --- HALAMAN 4: LAPORAN LABA RUGI ---
elif menu == "📈 Laporan Laba Rugi":
    st.title(f"📈 Laporan Laba Rugi - {selected_branch_name}")
    
    rev_query = f"SELECT SUM(credit) FROM general_journal WHERE branch_id = {active_branch_id} AND account_code = '411'"
    hpp_query = f"SELECT SUM(debit) FROM general_journal WHERE branch_id = {active_branch_id} AND account_code = '511'"
    
    cur = conn.cursor()
    cur.execute(rev_query)
    total_rev = cur.fetchone()[0] or 0.0
    
    cur.execute(hpp_query)
    total_hpp = cur.fetchone()[0] or 0.0
    
    net_profit = total_rev - total_hpp

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pendapatan F&B", f"Rp {total_rev:,.0f}")
    col2.metric("Total HPP", f"Rp {total_hpp:,.0f}")
    col3.metric("Laba Kotor", f"Rp {net_profit:,.0f}", delta=f"Margin: {(net_profit/total_rev*100) if total_rev > 0 else 0:.1f}%")

# --- HALAMAN 5: PENGATURAN TELEGRAM BOT ---
elif menu == "🤖 Pengaturan Telegram Bot":
    st.title("🤖 Konfigurasi Telegram Bot Notifikasi")
    st.markdown("Masukkan token bot Telegram dan Chat ID Anda agar sistem dapat mengirimkan notifikasi transaksi secara *real-time*.")

    token_input = st.text_input("Telegram Bot Token:", value=st.session_state['bot_token'], type="password")
    chat_id_input = st.text_input("Telegram Chat ID / Group ID:", value=st.session_state['chat_id'])

    if st.button("Simpan & Uji Koneksi Bot"):
        st.session_state['bot_token'] = token_input
        st.session_state['chat_id'] = chat_id_input
        
        success, msg = send_telegram_notification(token_input, chat_id_input, "✅ *Uji Koneksi SISKA v2.1 Berhasil!*\nSistem terhubung dengan Telegram Bot.")
        if success:
            st.success(msg)
        else:
            st.error(msg)