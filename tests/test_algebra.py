import pytest

from gc_reports.algebra import RealNumber, sum_real_numbers


@pytest.mark.parametrize(
    ("numbers", "expected"),
    [
        ([], RealNumber(0, 1)),
        ([RealNumber(1, 2), RealNumber(1, 3)], RealNumber(5, 6)),
        ([RealNumber(3, 4), RealNumber(1, 2)], RealNumber(5, 4)),
    ],
)
def test_sum_real_numbers(numbers: list[RealNumber], expected: RealNumber) -> None:
    assert sum_real_numbers(numbers) == expected


def test_sum_real_numbers_raises_for_zero_denominator() -> None:
    with pytest.raises(ValueError, match="Denominator cannot be zero"):
        sum_real_numbers([RealNumber(1, 2), RealNumber(3, 0)])
