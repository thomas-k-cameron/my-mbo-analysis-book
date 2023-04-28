# https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html
# target rate predictions for 14 Jun 2023
rates = list(map(lambda x: x/100, range(475, 550, 25)))

# currnet fed rate
R = 5.3
CASH = 100
X = 45


def future_fair_val(target, r, x) -> int:
    return target - (r*(x/360))

R=5.4
future_fair_val(CASH-5.1, R/100, X)