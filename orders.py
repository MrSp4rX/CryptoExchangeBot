from db import cursor, conn

def create_order(user_id, order_type, coin, amount, price):
    cursor.execute("INSERT INTO orders (user_id, type, coin, amount, price, status) VALUES (?, ?, ?, ?, ?, 'open')",
                   (user_id, order_type, coin, amount, price))
    conn.commit()

def get_open_orders(coin):
    cursor.execute("SELECT * FROM orders WHERE coin = ? AND status = 'open'", (coin,))
    return cursor.fetchall()

def cancel_order(user_id, order_id):
    cursor.execute("SELECT * FROM orders WHERE id = ? AND user_id = ? AND status = 'open'", (order_id, user_id))
    if cursor.fetchone():
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        conn.commit()
        return True
    return False

def get_order(order_id):
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    return cursor.fetchone()

def update_order_status(order_id, status):
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
