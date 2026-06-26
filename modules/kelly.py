import math
def kelly_fraction(win_rate, avg_win, avg_loss, frac=0.25):
    p = win_rate/100; q = 1-p; w = avg_win/100; l = avg_loss/100
    if w <= 0 or l <= 0: return 0,0,0
    b = w/l
    raw = max(0, (b*p-q)/b)
    return b, raw, raw*frac
def shares_for(amount, price):
    return max(0, math.floor(amount/price)) if price and price > 0 else 0
