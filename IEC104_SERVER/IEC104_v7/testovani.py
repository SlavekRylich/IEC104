import asyncio
import sys

import select


class TKbdTerm():
    def __init__(self):
        self.Poller = select.poll()
        self.Poller.register(sys.stdin, select.POLLIN)

    def GetChr(self):
        for s, ev in self.Poller.poll(500):
            return s.read(1)

    async def Input(self, aPrompt = ''):
        R = ''
        while True:
            K = self.GetChr()
            if (K):
                if (ord(K) == 10): # enter
                    print()
                    return R
                elif (ord(K) == 27): # esc
                    return ''
                elif (ord(K) == 127): # bs
                    R = R[:-1]
                else:
                    R += K
                sys.stdout.write("%s%s   \r" % (aPrompt, R))
            await asyncio.sleep(0.2)

if __name__ == "__main__":
    term = TKbdTerm()
    try:
        asyncio.run(term.Input())
    except KeyboardInterrupt:
        pass
    finally:
        pass