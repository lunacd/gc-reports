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

    def __neg__(self) -> RealNumber:
        return RealNumber(num=-self.num, denom=self.denom)

    def __add__(self, rhs: RealNumber):
        if self.denom == 0 or rhs.denom == 0:
            raise ValueError("Denominator cannot be zero.")
        
        gcd = math.gcd(self.denom, rhs.denom)
        common_denom = (self.denom * rhs.denom) // gcd

        result_num = ((self.num * rhs.denom) + (rhs.num * self.denom)) // gcd
        return RealNumber(result_num, common_denom)

    def __sub__(self, rhs: RealNumber):
        return self + (-rhs)


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
