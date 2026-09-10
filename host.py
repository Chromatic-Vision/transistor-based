import world
import net

s = net.NetServer('', 60_001)

level = world.Level((1, 1), s.update)

try:

    input()

finally:
    level._run = False
