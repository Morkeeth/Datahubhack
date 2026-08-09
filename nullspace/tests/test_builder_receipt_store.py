"""Builder review receipts bind to the ghost URN — /tmp is only a cache."""

from nullspace.builder import (
    _persist_receipt_to_catalog,
    _write_review_receipt,
    load_review_receipt,
)


def test_write_and_load_receipt_via_file_cache(tmp_path, monkeypatch):
    receipt_path = tmp_path / "receipt.json"
    import nullspace.builder as builder

    monkeypatch.setattr(builder, "_RECEIPT_PATH", receipt_path)
    monkeypatch.setattr(
        builder,
        "_persist_receipt_to_catalog",
        lambda want, receipt: None,
    )
    path = _write_review_receipt(
        want="catalog-receipt-unit",
        reason="unit decline",
        plan=None,
        result={"status": "declined", "reason": "unit decline"},
    )
    assert path == str(receipt_path)
    loaded = load_review_receipt("catalog-receipt-unit", dh=None)
    assert loaded is not None
    assert loaded["outcome"] == "declined"
    assert loaded["want"] == "catalog-receipt-unit"
    assert loaded["refusal"] == "unit decline"


def test_persist_receipt_skips_when_no_ghost(monkeypatch):
    """Catalog write is a no-op when the ghost URN has no DatasetProperties yet."""

    class _Dead:
        def healthy(self):
            return True

        class graph:
            @staticmethod
            def get_aspect(urn, cls):
                return None

    monkeypatch.setattr(
        "nullspace.builder.DataHubClient",
        lambda: _Dead(),
    )
    # Must not raise.
    _persist_receipt_to_catalog("no-such-ghost-yet", {"want": "no-such-ghost-yet"})
