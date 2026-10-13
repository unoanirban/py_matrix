# ESP8266 Matrix Multiplication Calculator

A standalone matrix multiplication calculator for the **ESP8266** running **MicroPython**. It has a **128x64 SSD1306 OLED** for the display and a **TTP224 4-channel touch pad** for input, so it needs no keyboard and no computer once it is loaded.

You pick the matrix sizes, type in the elements of both matrices using touch pads, and the product `A x B` appears on the screen.

## Features

- Matrix sizes from 1x1 up to **4x4**; A and B can be non-square (`A` is `r x c`, `B` is `c x p`)
- Elements are entered one by one (`a00, a01, a02, a10, ...`) with large, easy-to-read numbers
- Values range from **-999 to 999**
- Fast-tap speed-up: tap quickly and the step grows from 1 to 5 to 20
- Go back and fix an earlier element at any time (double tap)
- Result shown on screen; if it is too big to fit, it falls back to one element per line and can be scrolled
- Works with the TTP224 in momentary or toggle mode (one setting)
- Detects the OLED's I2C address (`0x3C` or `0x3D`) automatically

## Hardware

| Part | Notes |
|---|---|
| ESP8266 board | NodeMCU, Wemos D1 mini or similar, with MicroPython installed |
| SSD1306 OLED, 128x64 | I2C version (4 pins) |
| TTP224 touch module, 4 channels | Powered from 3.3 V |
| Jumper wires | |

## Wiring

| Part | Pin | ESP8266 GPIO | Board label |
|---|---|---|---|
| OLED | SCL | GPIO4 | D2 |
| OLED | SDA | GPIO5 | D1 |
| OLED | VCC / GND | 3V3 / GND | |
| TTP224 | OUT1 (+) | GPIO14 | D5 |
| TTP224 | OUT2 (-) | GPIO12 | D6 |
| TTP224 | OUT3 (enter / back) | GPIO13 | D7 |
| TTP224 | OUT4 (scroll) | GPIO16 | D0 |
| TTP224 | VCC / GND | 3V3 / GND | |

> **Note:** MicroPython's `Pin(n)` uses **GPIO numbers**, not the "D" labels printed on the board. The OLED pins above (SCL = GPIO4, SDA = GPIO5) are the ones used in `ui.py`. If your OLED is wired the other way round, either swap the two wires or swap the numbers in `ui.py`. See [Troubleshooting](#troubleshooting) for a scanner that finds the right pins.
>
> Power the TTP224 from **3.3 V**, so its outputs are safe for the ESP8266. Avoid using D3, D4 and D8 for the touch outputs, because they affect booting.

## Files

| File | Purpose |
|---|---|
| `ui.py` | OLED setup, touch input handling, drawing helpers |
| `matcalc.py` | The calculator itself (menus, entry, multiplication, result screen) |
| `ssd1306.py` | OLED driver (from [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display/ssd1306)) |

The code is split in two so that each file compiles within the ESP8266's small RAM.

## Installation

1. Install [MicroPython](https://micropython.org/download/ESP8266_GENERIC/) on the ESP8266.
2. Copy `ssd1306.py`, `ui.py` and `matcalc.py` to the board (for example with Thonny, `mpremote` or `ampy`).
3. Wire everything as shown above.
4. Run it from the REPL:

   ```python
   import matcalc
   matcalc.main()
   ```

   To start it automatically at power-up, create a `main.py` on the board that contains:

   ```python
   import matcalc
   matcalc.main()
   ```

## How to use

| Touch channel | Action |
|---|---|
| **CH1** | Increase the value (+) |
| **CH2** | Decrease the value (-) |
| **CH3**, single tap | Enter / next |
| **CH3**, double tap | Go back one step |
| **CH4** | Scroll the result (up and down) |

1. **Choose the sizes.** The device asks for the number of rows of A, the columns of A, and the columns of B. The rows of B are set automatically to the columns of A, so the multiplication is always valid.
2. **Enter matrix A.** Each element is asked in turn (`a00`, `a01`, ...). Adjust it with CH1 / CH2 and confirm with CH3.
3. **Enter matrix B** in the same way (`b00`, `b01`, ...).
4. **Read the result.** The product appears as `Result RxC`.
   - If it fits, each screen line is one row of the result.
   - If it doesn't fit, each element is listed as `c00=...`. Touch CH4 to scroll down; when you reach the bottom, it scrolls back up. The `^` and `v` marks at the right edge show where more lines are.
5. Touch CH3 to start a new calculation.

Example, `A` (2x3) times `B` (3x2):

```
A = | 1 2 3 |     B = |  7  8 |
    | 4 5 6 |         |  9 10 |
                       | 11 12 |

Result 2x2
  58  64
 139 154
```

## Configuration

Settings are at the top of the files.

| Setting | File | Default | Meaning |
|---|---|---|---|
| `TOGGLE` | `ui.py` | `False` | `False` for a TTP224 in normal/momentary mode (the output is on while you touch). Set `True` if you put the module in toggle mode (TOG jumper closed). |
| `LOCK` | `ui.py` | `80` | Milliseconds to ignore repeated triggers of the same pad (reduces chatter). |
| `DBL` | `ui.py` | `350` | Time window for a double tap on CH3, in milliseconds. |
| I2C pins | `ui.py` | SCL = GPIO4, SDA = GPIO5 | The pins the OLED is connected to. |
| Touch pins | `ui.py` | `14, 12, 13, 16` | GPIOs for TTP224 OUT1 to OUT4. |
| `LO`, `HI` | `matcalc.py` | `-999`, `999` | Allowed range for each element. |
| `MAXN` | `matcalc.py` | `4` | Largest matrix dimension. |

## Troubleshooting

**`OSError: [Errno 19] ENODEV` when starting.** The OLED isn't answering on the I2C pins. Run this scanner in the REPL; it tries every pair of free pins and prints the one where the OLED responds:

```python
from machine import Pin, I2C
pins = [0, 2, 4, 5, 12, 13, 14]
for scl in pins:
    for sda in pins:
        if scl != sda:
            try:
                r = I2C(scl=Pin(scl), sda=Pin(sda), freq=100000).scan()
            except Exception:
                r = []
            if r:
                print('SCL=GPIO%d SDA=GPIO%d ->' % (scl, sda), [hex(a) for a in r])
print('done')
```

Then use the pins it reports in `ui.py`, or rewire the OLED to match. Disconnect the touch module while scanning. The firmware prints `I2C scan: [...]` each time it starts, which also helps with checking.

**One touch changes the value by 2, or CH3 never enters.** The code is counting two events per touch. Check the `TOGGLE` setting in `ui.py`: it must be `False` if the TTP224 is in normal mode and `True` only if it is really in toggle mode.

**A touch pad reacts without being touched, or is too sensitive.** Move wires away from the pads and keep the module off metal surfaces. Many TTP224 boards also have small solder pads for a sensitivity capacitor on each channel: with the pads open the channel is at its most sensitive, and adding a small capacitor across them lowers the sensitivity. Check your board's documentation for the pad positions and suitable values.

**`MemoryError` when importing.** The ESP8266 ran out of RAM while compiling the source. Restart the board so you begin with free memory, or compile the files on your computer with `mpy-cross` and copy the `.mpy` files instead of the `.py` files.

## License

Add the license you prefer (for example MIT) here.
