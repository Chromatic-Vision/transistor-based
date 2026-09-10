import time

import world
import net

s = net.NetServer('', 60_001)

level = world.Level((1, 1), s.update)

try:
    while level._run:
        time.sleep(.1)

finally:
    level._run = False
