"""
KilnLink Tamper-Evident Delivery Receipt Ledger
Cryptographic SHA-256 hash chaining and cross-table invariant verification for statutory audit records.
"""
import os
import hmac
import hashlib
import secrets
import datetime
import sqlite3
from typing import Dict, Any, List, Tuple, Optional

GENESIS_HASH = "GENESIS_BLOCK_000000000000000000000000000000000000000000000000000000"

def get_hmac_key() -> Optional[bytes]:
    """Retrieves optional HMAC signing key from environment."""
    k = os.environ.get("RECEIPT_HMAC_KEY", "").strip()
    return k.encode("utf-8") if k else None

def canonical_receipt_payload(
    receipt_id: str,
    delivery_id: str,
    kiln_id: str,
    supplier_id: str,
    date: str,
    tonnes: float,
    form: str,
    prev_hash: str
) -> str:
    """
    Constructs an immutable canonical UTF-8 representation of the delivery record for hashing.
    """
    return f"{receipt_id.strip()}:{delivery_id.strip()}:{kiln_id.strip()}:{supplier_id.strip()}:{date.strip()}:{float(tonnes):.2f}:{form.strip().lower()}:{prev_hash.strip()}"

def compute_hash(payload: str) -> str:
    """Computes SHA-256 or HMAC-SHA-256 digest based on configuration."""
    hmac_key = get_hmac_key()
    if hmac_key:
        return hmac.new(hmac_key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def get_latest_receipt_hash(cur: sqlite3.Cursor) -> Tuple[str, str]:
    """
    Retrieves the latest receipt ID and hash from the chain.
    Returns (latest_receipt_id, latest_hash).
    """
    cur.execute("SELECT receipt_id, current_hash FROM delivery_receipts ORDER BY rowid DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        return row[0], row[1]
    return "R000", GENESIS_HASH

def record_tamper_evident_receipt(
    cur: sqlite3.Cursor,
    delivery_id: str,
    kiln_id: str,
    supplier_id: str,
    date: str,
    tonnes: float,
    form: str
) -> Dict[str, Any]:
    """
    Appends a new verified receipt to the cryptographic chain inside an active transaction.
    Synchronizes the persistent chain_head_tracker table.
    """
    cur.execute("SELECT COUNT(*) FROM delivery_receipts;")
    count = cur.fetchone()[0] + 1
    random_entropy = secrets.token_hex(2).upper()
    receipt_id = f"R{count:03d}-{random_entropy}"

    _, prev_hash = get_latest_receipt_hash(cur)
    payload = canonical_receipt_payload(receipt_id, delivery_id, kiln_id, supplier_id, date, tonnes, form, prev_hash)
    current_hash = compute_hash(payload)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cur.execute(
        """
        INSERT INTO delivery_receipts (
            receipt_id, delivery_id, kiln_id, supplier_id, date, tonnes, form, prev_hash, current_hash, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (receipt_id, delivery_id, kiln_id, supplier_id, date, float(tonnes), form, prev_hash, current_hash, timestamp)
    )

    # Atomically update chain_head_tracker
    cur.execute(
        """
        INSERT OR REPLACE INTO chain_head_tracker (id, head_hash, receipt_count, updated_at)
        VALUES (1, ?, ?, datetime('now'));
        """,
        (current_hash, count)
    )

    return {
        "receipt_id": receipt_id,
        "delivery_id": delivery_id,
        "current_hash": current_hash,
        "prev_hash": prev_hash,
        "timestamp": timestamp
    }

def get_chain_head(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Returns the latest chain head hash and receipt count from delivery_receipts and chain_head_tracker.
    """
    cur = conn.cursor()
    cur.execute("SELECT receipt_id, current_hash, timestamp FROM delivery_receipts ORDER BY rowid DESC LIMIT 1;")
    latest = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM delivery_receipts;")
    total = cur.fetchone()[0]

    cur.execute("SELECT head_hash, receipt_count, updated_at FROM chain_head_tracker WHERE id = 1;")
    tracker = cur.fetchone()

    return {
        "chain_head": latest[1] if latest else GENESIS_HASH,
        "latest_receipt_id": latest[0] if latest else None,
        "timestamp": latest[2] if latest else None,
        "total_receipts": total,
        "tracker_head_hash": tracker[0] if tracker else (latest[1] if latest else GENESIS_HASH),
        "tracker_count": tracker[1] if tracker else total
    }

def verify_receipt_chain(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Verifies the integrity of the entire receipt chain from genesis to head.
    Detects:
    1. Broken hash links between adjacent receipts
    2. Modified receipt content (tonnes, kiln, supplier, date, form)
    3. Mismatch between deliveries table and delivery_receipts table
    4. Truncation of tail receipts against stored chain_head_tracker
    5. Orphan deliveries (deliveries missing receipts)
    """
    cur = conn.cursor()

    # Retrieve all receipts
    cur.execute(
        "SELECT receipt_id, delivery_id, kiln_id, supplier_id, date, tonnes, form, prev_hash, current_hash FROM delivery_receipts ORDER BY rowid ASC;"
    )
    receipt_rows = cur.fetchall()

    # Retrieve all deliveries for cross-table invariant checks
    cur.execute(
        "SELECT delivery_id, kiln_id, supplier_id, date, tonnes, form, receipt FROM deliveries ORDER BY delivery_id ASC;"
    )
    delivery_rows = {r["delivery_id"]: dict(r) for r in cur.fetchall()}

    # Retrieve chain head tracker
    cur.execute("SELECT head_hash, receipt_count FROM chain_head_tracker WHERE id = 1;")
    tracker = cur.fetchone()

    if not receipt_rows and not delivery_rows:
        return {
            "is_valid": True,
            "total_receipts": 0,
            "broken_links_count": 0,
            "chain_head": GENESIS_HASH,
            "receipts": [],
            "message": "Chain is empty. Ready for new audit receipts."
        }

    expected_prev = GENESIS_HASH
    broken_links = []
    receipt_items = []
    seen_delivery_ids = set()

    for r in receipt_rows:
        r_id = r["receipt_id"]
        d_id = r["delivery_id"]
        k_id = r["kiln_id"]
        s_id = r["supplier_id"]
        dt = r["date"]
        t = float(r["tonnes"])
        form = r["form"]
        stored_prev = r["prev_hash"]
        stored_curr = r["current_hash"]

        link_valid = (stored_prev == expected_prev)
        payload = canonical_receipt_payload(r_id, d_id, k_id, s_id, dt, t, form, stored_prev)
        hash_valid = (compute_hash(payload) == stored_curr)

        # Cross-table verification against deliveries table
        delivery_match = False
        if d_id in delivery_rows:
            d = delivery_rows[d_id]
            delivery_match = (
                d["kiln_id"] == k_id and
                d["supplier_id"] == s_id and
                d["date"] == dt and
                abs(float(d["tonnes"]) - t) < 1e-4 and
                d["form"].strip().lower() == form.strip().lower()
            )
            seen_delivery_ids.add(d_id)

        is_item_valid = link_valid and hash_valid and delivery_match
        if not is_item_valid:
            broken_links.append(r_id)

        receipt_items.append({
            "receipt_id": r_id,
            "delivery_id": d_id,
            "date": dt,
            "tonnes": t,
            "current_hash": stored_curr,
            "prev_hash": stored_prev,
            "is_valid": is_item_valid
        })

        expected_prev = stored_curr

    # Check for orphan deliveries (deliveries without a valid receipt)
    orphan_deliveries = [d_id for d_id in delivery_rows if d_id not in seen_delivery_ids]
    if orphan_deliveries:
        broken_links.extend([f"ORPHAN_DELIVERY_{d_id}" for d_id in orphan_deliveries])

    # Truncation check against tracker
    truncation_detected = False
    if tracker:
        expected_head, expected_count = tracker[0], int(tracker[1])
        if len(receipt_rows) < expected_count:
            truncation_detected = True
            broken_links.append("CHAIN_TRUNCATION_DETECTED")
        elif len(receipt_rows) == expected_count and receipt_rows and receipt_rows[-1]["current_hash"] != expected_head:
            truncation_detected = True
            broken_links.append("CHAIN_HEAD_TAMPER_DETECTED")

    is_chain_intact = (len(broken_links) == 0) and not truncation_detected
    last_hash = receipt_rows[-1]["current_hash"] if receipt_rows else GENESIS_HASH

    return {
        "is_valid": is_chain_intact,
        "total_receipts": len(receipt_rows),
        "broken_links_count": len(broken_links),
        "chain_head": last_hash,
        "receipts": receipt_items,
        "message": "Cryptographic receipt chain verified intact (SHA-256)." if is_chain_intact else f"Tampering detected! Anomalies at: {broken_links}"
    }


