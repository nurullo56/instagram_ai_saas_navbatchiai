import hashlib
import json
from typing import List, Dict, Any


def normalize_meta_webhook_payload(raw_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Bitta Meta webhook batch payload ichidagi barcha messaging[] va changes[]
    elementlarini mustaqil eventlarga ajratadi va har biriga deterministik ID beradi.
    """
    normalized_events: List[Dict[str, Any]] = []

    for entry in raw_payload.get("entry", []):
        account_id = str(entry.get("id", "unknown_account"))
        entry_time = entry.get("time", 0)

        # 1. Direct Messaging hodisalari
        for msg_event in entry.get("messaging", []):
            sender_id = str(msg_event.get("sender", {}).get("id", "unknown"))
            recipient_id = str(msg_event.get("recipient", {}).get("id", "unknown"))
            timestamp = msg_event.get("timestamp", entry_time)

            # A. Xabarlar (Message)
            if "message" in msg_event and "mid" in msg_event["message"]:
                mid = msg_event["message"]["mid"]
                event_id = f"meta:{account_id}:dm:{mid}"
            # B. Postback (Tugma bosilishi)
            elif "postback" in msg_event:
                pb = msg_event["postback"]
                payload_hash = hashlib.sha256(str(pb.get("payload", "")).encode("utf-8")).hexdigest()[:16]
                event_id = f"meta:{account_id}:pb:{sender_id}:{recipient_id}:{timestamp}:{payload_hash}"
            # C. Delivery kvitansiyasi
            elif "delivery" in msg_event:
                mids_joined = "_".join(msg_event["delivery"].get("mids", []))
                event_id = f"meta:{account_id}:delivery:{mids_joined}:{timestamp}"
            # D. Read kvitansiyasi
            elif "read" in msg_event:
                watermark = msg_event["read"].get("watermark", timestamp)
                event_id = f"meta:{account_id}:read:{sender_id}:{recipient_id}:{watermark}"
            # E. Boshqa messaging hodisalari
            else:
                canon = json.dumps(msg_event, sort_keys=True, separators=(',', ':'))
                event_id = f"meta:{account_id}:msg_other:{hashlib.sha256(canon.encode()).hexdigest()[:24]}"

            normalized_events.append({
                "source": "meta",
                "event_id": event_id,
                "payload": msg_event,
                "account_id": account_id
            })

        # 2. Changes (Post va Reels izohlari)
        for change in entry.get("changes", []):
            field = change.get("field", "unknown_field")
            val = change.get("value", {})

            if field == "comments" and "id" in val:
                comment_id = str(val["id"])
                comment_created = val.get("created_time", entry_time)
                event_id = f"meta:{account_id}:comment:{comment_id}:{comment_created}"
            else:
                canon = json.dumps(change, sort_keys=True, separators=(',', ':'))
                event_id = f"meta:{account_id}:change:{field}:{hashlib.sha256(canon.encode()).hexdigest()[:24]}"

            normalized_events.append({
                "source": "meta",
                "event_id": event_id,
                "payload": change,
                "account_id": account_id
            })

    return normalized_events
