import dataclasses
import math
import typing


@dataclasses.dataclass
class RealNumber:
    num: int
    denom: int

    def __float__(self) -> float:
        if self.denom == 0:
            raise ValueError("Denominator cannot be zero.")
        return self.num / self.denom


def sum_real_numbers(numbers: typing.Iterable[RealNumber]) -> RealNumber:
    total_num = 0
    total_denom = 1

    for number in numbers:
        if number.denom == 0:
            raise ValueError("Denominator cannot be zero.")

        gcd = math.gcd(total_denom, number.denom)
        common_denom = (total_denom * number.denom) // gcd

        total_num = ((total_num * number.denom) + (number.num * total_denom)) // gcd
        total_denom = common_denom

    return RealNumber(total_num, total_denom)
