from db import cursor, conn

def create_escrow(buyer_id, seller_id, coin, amount):
    cursor.execute("INSERT INTO escrows (buyer_id, seller_id, coin, amount, status) VALUES (?, ?, ?, ?, 'active')",
                   (buyer_id, seller_id, coin, amount))
    conn.commit()

def get_escrows():
    cursor.execute("SELECT * FROM escrows WHERE status = 'active'")
    return cursor.fetchall()

def complete_escrow(escrow_id):
    cursor.execute("UPDATE escrows SET status = 'released' WHERE id = ?", (escrow_id,))
    conn.commit()
