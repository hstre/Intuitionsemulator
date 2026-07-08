"""The MVP rules as test cases - Hermes proposes, the gate disposes, fail-closed.

Everything offline: the Hermes side is exercised through the plugin hook exactly as Hermes
calls it (tool_name + args kwargs), against a temp JONI_GOVERNOR_HOME.
"""

from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture()
def st(tmp_path, monkeypatch):
    monkeypatch.setenv("JONI_GOVERNOR_HOME", str(tmp_path / "gov"))
    from joni_governor.state import GovernorState
    return GovernorState()


def _mem_args(content="Hermine likes tidy claims", action="add"):
    return {"action": action, "target": "memory", "content": content}


def _skill_args(name="summarize-paper", action="create"):
    return {"action": action, "name": name,
            "instructions": "read the paper, extract claims, cite sources"}


# -- Regel 1+3: Lesen und ungegatete Tools passieren ungehindert -------------------------------- #

def test_ungated_tools_pass_untouched(st):
    from joni_governor.gate import decide_tool_call
    for tool in ("web_search", "session_search", "terminal", "browser"):
        assert decide_tool_call(tool, {"q": "x"}, state=st).action == "allow"


# -- Regel 4+6: Memory-Schreibversuche werden Vorschläge, nie direkte Writes -------------------- #

def test_a_memory_write_stages_as_a_kernel_proposal(st):
    from joni_governor.gate import decide_tool_call
    v = decide_tool_call("memory", _mem_args(), state=st)
    assert v.action == "stage" and v.blocked
    assert v.proposal_id.startswith("C-")
    claim = st.claim(v.proposal_id)
    assert claim.status.value == "candidate"                  # a proposal, not state
    assert "Hermine likes tidy claims" in claim.text          # assessable content
    payload = json.loads((st.pending_dir / f"{v.proposal_id}.json").read_text())
    assert payload["tool"] == "memory"                        # replayable


# -- Regel 5+6: Skill-Schreibversuche ebenso --------------------------------------------------- #

def test_a_skill_create_stages_too(st):
    from joni_governor.gate import decide_tool_call
    v = decide_tool_call("skill_manage", _skill_args(), state=st)
    assert v.action == "stage"
    assert st.claim(v.proposal_id).topic == "skill:summarize-paper"


def test_retrying_a_pending_write_reuses_the_same_proposal(st):
    from joni_governor.gate import decide_tool_call
    v1 = decide_tool_call("memory", _mem_args(), state=st)
    v2 = decide_tool_call("memory", _mem_args(), state=st)   # the model retries
    assert v2.action == "stage" and v2.proposal_id == v1.proposal_id
    assert len(list(st.pending_dir.glob("*.json"))) == 1     # no twin per retry


# -- Regel 7: der Betreiber entscheidet; ok = einmaliges Ticket, nein = korrigierter Irrtum ----- #

def test_approval_issues_a_one_shot_ticket(st):
    from joni_governor import staging
    from joni_governor.gate import decide_tool_call
    v = decide_tool_call("memory", _mem_args(), state=st)
    staging.decide(st, v.proposal_id, "ok", "sinnvolle Notiz")
    assert st.claim(v.proposal_id).status.value == "active"
    again = decide_tool_call("memory", _mem_args(), state=st)   # the agent redoes the write
    assert again.action == "allow"                              # exactly this write, once
    third = decide_tool_call("memory", _mem_args(), state=st)   # ...and only once
    assert third.action == "stage"


def test_rejection_becomes_a_corrected_error_and_blocks_revenants(st):
    from joni_governor import staging
    from joni_governor.gate import decide_tool_call
    v = decide_tool_call("skill_manage", _skill_args(name="rm-rf-helper"), state=st)
    staging.decide(st, v.proposal_id, "nein", "gefährlich und unnötig")
    assert st.claim(v.proposal_id).status.value == "rejected"
    # the revenant rule: the same proposal (even lightly rephrased) is refused outright
    rev = decide_tool_call("skill_manage", _skill_args(name="rm-rf-helper"), state=st)
    assert rev.action == "reject" and "Wiedergänger" in rev.reason
    # and the persona reads it as a corrected error
    from joni.autonomy import persona
    cors = persona.extract_corrections(st.cs)
    assert any(c.theme == "skill:rm-rf-helper" for c in cors)


# -- Policy: Auto-Allow ist eine explizite Betreiber-Lockerung ---------------------------------- #

def test_policy_auto_allow_is_an_explicit_operator_act(st):
    from joni_governor.gate import decide_tool_call
    st.policy_path.write_text("memory:\n  auto_allow_actions: add\n", encoding="utf-8")
    assert decide_tool_call("memory", _mem_args(action="add"), state=st).action == "allow"
    assert decide_tool_call("memory", _mem_args(action="replace"),
                            state=st).action == "stage"       # only what was loosened


def test_an_unreadable_policy_means_strict_defaults(st):
    from joni_governor.gate import decide_tool_call
    st.policy_path.write_text("{{{{ not yaml", encoding="utf-8")
    assert decide_tool_call("memory", _mem_args(), state=st).action == "stage"


# -- Fail-closed: ein kaputtes Gate winkt nie durch --------------------------------------------- #

def test_gate_errors_fail_closed(st, monkeypatch):
    from joni_governor import gate
    monkeypatch.setattr(gate, "_render_proposal",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    v = gate.decide_tool_call("memory", _mem_args(), state=st)
    assert v.action == "reject" and "fail-closed" in v.reason


def test_the_plugin_hook_blocks_gated_tools_when_the_governor_is_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("JONI_GOVERNOR_HOME", str(tmp_path / "gov"))
    import sys
    sys.path.insert(0, str((tmp_path / "nowhere")))
    plugin = importlib.import_module("hermes_plugin_joni_governor")
    monkeypatch.setattr(plugin, "_governor",
                        lambda: (_ for _ in ()).throw(ImportError("kernel missing")))
    out = plugin._on_pre_tool_call(tool_name="memory", args=_mem_args())
    assert out and out["action"] == "block" and "fail-closed" in out["message"]
    assert plugin._on_pre_tool_call(tool_name="web_search", args={}) is None


# -- Persistenz: der Kernel überlebt den Prozess ------------------------------------------------ #

def test_the_epistemic_core_survives_a_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("JONI_GOVERNOR_HOME", str(tmp_path / "gov"))
    from joni_governor.gate import decide_tool_call
    from joni_governor.state import GovernorState
    st1 = GovernorState()
    v = decide_tool_call("memory", _mem_args(), state=st1)
    st2 = GovernorState()                                     # a fresh process
    assert st2.claim(v.proposal_id).status.value == "candidate"
    assert (st2.home / "layer9.journal").is_dir()             # chunked from birth


# -- Betreiber-Oberfläche ----------------------------------------------------------------------- #

def test_the_sheet_shows_content_not_counts(st):
    from joni_governor import staging
    from joni_governor.gate import decide_tool_call
    decide_tool_call("memory", _mem_args(content="the operator prefers short PRs"), state=st)
    sheet = staging.render_sheet(st)
    assert "Vorschlags-Mappe" in sheet
    assert "the operator prefers short PRs" in sheet          # assessable, not just counted
    assert "decide" in sheet


def test_heartbeat_and_liveness(st):
    from joni_governor import audit
    assert audit.last_beat(st) is None
    audit.beat(st, source="test")
    assert audit.last_beat(st) is not None
    assert "verdict" in audit.liveness(st, hermes_home=st.home / "no-hermes")
