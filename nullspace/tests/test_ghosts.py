from nullspace.ghosts import MemoryGhostStore, Nullspace, consumer_search


def test_three_misses_reach_threshold_and_solidify():
    store = MemoryGhostStore()
    ns = Nullspace(store, demand_threshold=3)
    want = "trial-to-paid conversion by cohort"

    for agent in ("a", "b", "c"):
        receipt = consumer_search(ns, want=want, agent_id=agent, dh=None)
        assert receipt["status"] == "miss_ghosted"

    ghost = store.get(want)
    assert ghost is not None
    assert ghost.demand == 3
    assert set(ghost.requesters) == {"a", "b", "c"}
    assert len(ns.ready_to_build()) == 1

    claimed = ns.claim(want, "builder-1")
    assert claimed.state == "claimed"
    ns.attach_pr(want, "https://github.com/example/pr/1")
    solid = ns.solidify(want, schema_fields=["cohort_id", "trial_to_paid_rate"])
    assert solid.state == "solid"
    assert solid.pr_url.endswith("/1")
    # Scar Tissue steal: resolution history bound to URN
    events = [e.event for e in solid.resolution]
    assert events.count("miss") == 3
    assert "claim" in events and "solidify" in events


def test_same_agent_does_not_double_count():
    ns = Nullspace(MemoryGhostStore(), demand_threshold=3)
    want = "monthly active users"
    consumer_search(ns, want=want, agent_id="a", dh=None)
    consumer_search(ns, want=want, agent_id="a", dh=None)
    g = ns.store.get(want)
    assert g is not None
    assert g.demand == 1


def test_urn_stable_across_consumers():
    from nullspace.urns import ghost_urn

    a = ghost_urn("Trial-to-Paid Conversion by Cohort")
    b = ghost_urn("trial-to-paid conversion by cohort")
    assert a == b


def test_reset_clears_local_store():
    store = MemoryGhostStore()
    ns = Nullspace(store, demand_threshold=3)
    consumer_search(ns, want="reset me", agent_id="a", dh=None)
    assert store.list_ghosts()
    result = ns.reset()
    assert result["status"] == "reset"
    assert result["store_count"] == 0
    assert store.list_ghosts() == []
