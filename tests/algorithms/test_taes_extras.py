"""Extra TAES tests to cover edge paths not exercised by main tests."""

from types import SimpleNamespace

from nedc_bench.algorithms.taes import TAESScorer


def test_taes_calc_hf_zero_duration_ref():
    # Call the internal calculation directly with a zero-duration ref
    # Use a SimpleNamespace to bypass EventAnnotation validation constraints
    ref = SimpleNamespace(start_time=1.0, stop_time=1.0)
    hyp = SimpleNamespace(start_time=0.0, stop_time=2.0)

    hit, fa = TAESScorer._calc_hf(ref, hyp)  # type: ignore[arg-type]
    assert hit == 0.0 and fa == 0.0
