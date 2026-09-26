from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

P = Path(__file__).resolve().parents[1] / "experiments" / "janus" / "kernel.py"
S = spec_from_file_location("janus_kernel", P)
assert S and S.loader
M = module_from_spec(S)
sys.modules[S.name] = M
S.loader.exec_module(M)

D=M.DependencyClass; W=M.SeparationWitness; Shadow=M.Shadow; State=M.JanusState
Event=M.MarginEvent


def state(sid, active=("A","B","C"), standing="AUTHORIZED"):
    deps=tuple(D(x,(f"e-{x}",)) for x in ("A","B","C"))
    shadows=(Shadow("collapse",frozenset(("A","B","C"))),)
    witnesses=tuple(W(f"w-{x}","collapse",x,active=x in active) for x in ("A","B","C"))
    return State(sid,standing,deps,shadows,witnesses)


def test_identical_endpoint_can_have_different_structural_margin():
    a=M.measure_margin(state("A",("A","B","C")))
    b=M.measure_margin(state("B",("A",)))
    assert a.standing == b.standing == "AUTHORIZED"
    assert a.distance == 3
    assert b.distance == 1


def test_prefailure_fragility_does_not_falsify_endpoint():
    a=M.measure_margin(state("t0",("A","B","C")))
    b=M.measure_margin(state("t1",("A","B")))
    c=M.classify_transition(a,b)
    assert c.event is Event.PREFailure_FRAGILITY
    assert c.endpoint_unchanged
    assert b.standing == "AUTHORIZED"


def test_progressive_witness_loss_exposes_three_two_one_zero():
    certs=[M.measure_margin(state(str(i),active)) for i,active in enumerate(
        (("A","B","C"),("A","B"),("A",),())
    )]
    assert [c.distance for c in certs] == [3,2,1,0]
    assert M.classify_transition(certs[0],certs[1]).event is Event.PREFailure_FRAGILITY
    assert M.classify_transition(certs[2],certs[3]).event is Event.FAILED


def test_duplicate_evidence_does_not_fake_independent_distance():
    deps=(D("A",("copy-1","copy-2","copy-3")),)
    s=State("dup","AUTHORIZED",deps,(Shadow("x",frozenset(("A",))),),
            (W("w","x","A"),))
    assert M.measure_margin(s).distance == 1


def test_invalid_provenance_witness_provides_no_separation():
    deps=(D("A",("e",)),)
    s=State("bad","AUTHORIZED",deps,(Shadow("x",frozenset(("A",))),),
            (W("w","x","A",provenance_valid=False),))
    assert M.measure_margin(s).distance == 0


def test_unexplained_margin_increase_is_robustness_inflation():
    weak=M.measure_margin(state("weak",("A",)))
    strong=M.measure_margin(state("strong",("A","B","C")))
    assert M.classify_transition(weak,strong).event is Event.ROBUSTNESS_INFLATION
    assert M.classify_transition(weak,strong,["new-independent-evidence"]).event is Event.ROBUSTNESS_GAIN


def test_minimal_shadow_basis_is_antichain_not_raw_powerset():
    deps=tuple(D(x,(x,)) for x in ("A","B","C"))
    s=State("m","AUTHORIZED",deps,(
        Shadow("ab",frozenset(("A","B"))),
        Shadow("abc",frozenset(("A","B","C"))),
        Shadow("c",frozenset(("C",))),
    ),())
    assert M.minimal_shadow_basis(s) == (frozenset(("C",)),frozenset(("A","B")))


def test_certificate_is_deterministic_under_witness_order():
    s=state("same",("A","B","C"))
    r=M.measure_margin(s)
    reversed_state=State(s.state_id,s.standing,s.dependency_classes,s.shadows,tuple(reversed(s.witnesses)))
    assert M.measure_margin(reversed_state) == r
