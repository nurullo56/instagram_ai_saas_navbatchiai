from app.services.webhook_normalizer import normalize_meta_webhook_payload


def test_normalize_batch_payload_with_multiple_events():
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "1784140001",
                "time": 1700000000,
                "messaging": [
                    {
                        "sender": {"id": "user_1"},
                        "recipient": {"id": "1784140001"},
                        "timestamp": 1700000001,
                        "message": {"mid": "mid.123456", "text": "Salom, kurs narxi qancha?"}
                    },
                    {
                        "sender": {"id": "user_2"},
                        "recipient": {"id": "1784140001"},
                        "timestamp": 1700000002,
                        "postback": {"title": "Boshlash", "payload": "START_PAYLOAD"}
                    }
                ],
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comm_999888",
                            "created_time": 1700000003,
                            "text": "Zo'r post!"
                        }
                    }
                ]
            }
        ]
    }

    events = normalize_meta_webhook_payload(payload)
    assert len(events) == 3

    # 1. Direct Message
    dm_event = events[0]
    assert dm_event["source"] == "meta"
    assert dm_event["event_id"] == "meta:1784140001:dm:mid.123456"
    assert dm_event["payload"]["message"]["text"] == "Salom, kurs narxi qancha?"

    # 2. Postback
    pb_event = events[1]
    assert pb_event["source"] == "meta"
    assert pb_event["event_id"].startswith("meta:1784140001:pb:user_2:1784140001:1700000002:")

    # 3. Comment Change
    comm_event = events[2]
    assert comm_event["source"] == "meta"
    assert comm_event["event_id"] == "meta:1784140001:comment:comm_999888:1700000003"


def test_normalize_empty_payload():
    assert normalize_meta_webhook_payload({}) == []
    assert normalize_meta_webhook_payload({"entry": []}) == []
