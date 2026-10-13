# matcalc.py - matrix multiplication calculator, touch version (module 2 of 2)
# Needs ui.py and ssd1306.py on the board.
#   import matcalc; matcalc.main()
# Touch channels: 1 = +, 2 = -, 3 = enter (tap) / back (double tap), 4 = scroll result
import gc
gc.collect()
import time
from ui import oled, header, big, ev

LO, HI = -999, 999      # allowed element range
MAXN = 4                # largest matrix dimension
LBL = ('A rows', 'A cols', 'B cols')


def mat(r, c):
    return [[0] * c for _ in range(r)]


def mul(A, B, n, m, p):
    return [[sum(A[i][k] * B[k][j] for k in range(m)) for j in range(p)]
            for i in range(n)]


def ask_sizes():
    v = [2, 2, 2]
    i = 0
    while i < 3:
        oled.fill(0)
        header('Matrix size')
        if i == 2:
            oled.text('B cols (rows=%d)' % v[1], 0, 13)
        else:
            oled.text(LBL[i], 0, 13)
        big(str(v[i]), 25)
        oled.text('ch3 x2 = back', 0, 55)
        oled.show()
        d, e, s = ev()
        if d:
            v[i] = max(1, min(MAXN, v[i] + d))
        if e == 1:
            i += 1
        elif e == 2 and i:
            i -= 1
    return v[0], v[1], v[2]


def enter_matrix(nm, M, r, c):
    """Ask for every element. Returns False if the user backed out of the first one."""
    n = r * c
    i = 0
    while 0 <= i < n:
        ri, ci = divmod(i, c)
        v = M[ri][ci]
        while True:
            oled.fill(0)
            header('Matrix %s  %dx%d' % (nm.upper(), r, c))
            oled.text('%s%d%d' % (nm, ri, ci), 0, 13)
            big(str(v), 25)
            oled.text('%d/%d ch3x2:back' % (i + 1, n), 0, 55)
            oled.show()
            d, e, s = ev()
            if d:
                v = max(LO, min(HI, v + d))
            if e:
                M[ri][ci] = v
                i += 1 if e == 1 else -1
                break
    return i >= n


def show_result(C, r, c):
    st = [[str(x) for x in row] for row in C]
    w = max(len(s) for row in st for s in row) + 1
    if c * w <= 14:                                   # whole rows fit on screen
        lines = [''.join(' ' * (w - len(s)) + s for s in row) for row in st]
    else:                                             # otherwise one element per line
        lines = ['c%d%d=%s' % (i, j, st[i][j]) for i in range(r) for j in range(c)]
    vis = 6
    mx = max(0, len(lines) - vis)                     # furthest the view can scroll
    top = 0
    dn = 1                                            # ch4 direction: 1 = down, -1 = up
    while True:
        oled.fill(0)
        header('Result %dx%d' % (r, c))
        for k in range(vis):
            if top + k < len(lines):
                oled.text(lines[top + k], 0, 12 + 8 * k)
        if top > 0:
            oled.text('^', 120, 12)
        if top < mx:
            oled.text('v', 120, 52)
        oled.show()
        d, e, s = ev()
        if e:
            return
        if s and mx:                                  # ch4: scroll, bounce at the ends
            top += dn
            if top >= mx:
                top = mx
                dn = -1
            elif top <= 0:
                top = 0
                dn = 1


def splash():
    oled.fill(0)
    header('Matrix Calc')
    oled.text('CH1 : +', 0, 16)
    oled.text('CH2 : -', 0, 26)
    oled.text('CH3: OK 2x=back', 0, 36)
    oled.text('CH4 : scroll', 0, 46)
    oled.show()
    time.sleep_ms(2500)


def main():
    splash()
    while True:
        ra, ca, cb = ask_sizes()
        A = mat(ra, ca)
        B = mat(ca, cb)
        st = 0
        while 0 <= st < 2:
            if st == 0:
                st = 1 if enter_matrix('a', A, ra, ca) else -1
            else:
                st = 2 if enter_matrix('b', B, ca, cb) else 0
        if st == 2:
            show_result(mul(A, B, ra, ca, cb), ra, cb)
        gc.collect()


if __name__ == "__main__":
    main()
