def format_order(order):
    return f"[Order {order[0]}] {order[3].upper()} {order[4]} @ ${order[5]} by User {order[1]}"

def format_escrow(escrow):
    return f"[Escrow {escrow[0]}] {escrow[3].upper()} {escrow[4]} | Buyer: {escrow[1]} | Seller: {escrow[2]}"
