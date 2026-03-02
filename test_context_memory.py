"""
Test multi-turn conversational memory features:
1. Context resolution  — "delete that" after discussing an order
2. Product name lookup — "delete my gaming mouse order"
3. Duplicate handling  — multiple orders with same product name
"""
from bot_engine import ChatbotEngine
import sqlite3

def setup_test_orders(db_path="orders.db"):
    """Insert test orders for context-memory testing."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Clean up previous test orders
    cur.execute("DELETE FROM orders WHERE order_id LIKE 'TORD%'")
    # Insert test orders (including duplicates)
    test_orders = [
        ("TORD001", "test_ctx", 1, "Gaming Mouse", 49.99, 1, "2026-03-01", "Pending"),
        ("TORD002", "test_ctx", 1, "Gaming Mouse", 49.99, 2, "2026-03-02", "Shipped"),
        ("TORD003", "test_ctx", 2, "Wireless Keyboard", 79.99, 1, "2026-03-01", "Delivered"),
    ]
    cur.executemany(
        "INSERT OR REPLACE INTO orders (order_id, session_id, product_id, product_name, price, quantity, order_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        test_orders
    )
    conn.commit()
    conn.close()
    print("✅ Test orders inserted: TORD001 (Gaming Mouse/Pending), TORD002 (Gaming Mouse/Shipped), TORD003 (Wireless Keyboard/Delivered)")

def cleanup_test(db_path="orders.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE order_id LIKE 'TORD%'")
    cur.execute("DELETE FROM conversation_history WHERE session_id = 'test_ctx'")
    conn.commit()
    conn.close()

def test_all():
    print("=" * 60)
    print("🧪 CONVERSATIONAL MEMORY TEST SUITE")
    print("=" * 60)

    setup_test_orders()

    bot = ChatbotEngine()
    bot.load_model()
    bot.load_data()
    sid = "test_ctx"

    # ── Test 1: Context resolution ──────────────────────────────
    print("\n" + "─" * 60)
    print("📋 Test 1: Context resolution — ask about order, then 'delete that'")
    print("─" * 60)

    r1 = bot.get_response("Show me details of order TORD003", session_id=sid)
    print(f"  User: Show me details of order TORD003")
    print(f"  Bot:  {r1[:150]}...")

    r2 = bot.get_response("Delete that order", session_id=sid)
    print(f"\n  User: Delete that order")
    print(f"  Bot:  {r2[:200]}")
    has_tord003 = "TORD003" in r2
    print(f"  ✅ PASS — resolved TORD003 from context" if has_tord003 else f"  ❌ FAIL — did not resolve TORD003")

    # Cancel delete if pending
    if sid in bot._pending:
        bot.get_response("no", session_id=sid)

    # ── Test 2: Product name lookup (single match) ──────────────
    print("\n" + "─" * 60)
    print("📋 Test 2: Delete by product name (single match — Wireless Keyboard)")
    print("─" * 60)

    r3 = bot.get_response("Delete my wireless keyboard order", session_id=sid)
    print(f"  User: Delete my wireless keyboard order")
    print(f"  Bot:  {r3[:200]}")
    has_keyboard = "Wireless Keyboard" in r3 or "TORD003" in r3
    print(f"  ✅ PASS — found Wireless Keyboard order" if has_keyboard else f"  ❌ FAIL — did not find order by product name")

    if sid in bot._pending:
        bot.get_response("no", session_id=sid)

    # ── Test 3: Duplicate product name → asks for order number ──
    print("\n" + "─" * 60)
    print("📋 Test 3: Delete by product name (duplicate — Gaming Mouse)")
    print("─" * 60)

    r4 = bot.get_response("Delete my gaming mouse order", session_id=sid)
    print(f"  User: Delete my gaming mouse order")
    print(f"  Bot:  {r4[:300]}")
    has_both = "TORD001" in r4 and "TORD002" in r4
    asks_which = "which" in r4.lower() or "specify" in r4.lower() or "order ID" in r4
    print(f"  ✅ PASS — listed both orders and asked for clarification" if (has_both and asks_which) else f"  ❌ FAIL — did not handle duplicates correctly")

    # ── Test 4: Update by product name ──────────────────────────
    print("\n" + "─" * 60)
    print("📋 Test 4: Update order by product name (single match)")
    print("─" * 60)

    r5 = bot.get_response("Update my wireless keyboard order to cancelled", session_id=sid)
    print(f"  User: Update my wireless keyboard order to cancelled")
    print(f"  Bot:  {r5[:200]}")
    updated = "cancel" in r5.lower() or "Cancelled" in r5
    print(f"  ✅ PASS — updated by product name" if updated else f"  ❌ FAIL — did not update by product name")

    # ── Cleanup ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    cleanup_test()
    print("🧹 Test data cleaned up.")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
