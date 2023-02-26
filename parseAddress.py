from typing import Tuple
import random
import math


def getBits(bitvector: int, upperIdx: int, lowerIdx: int) -> int:
    assert upperIdx > lowerIdx

    # upperIdx = 2
    # 1 << (upperIdx + 1) = 1 << 3 = 0b1000
    # 0b1000 - 0b1000 = 0b0111
    mask: int = (1 << (upperIdx + 1)) - 1

    return (mask & bitvector) >> lowerIdx


class DummySifiveCache:
    def __init__(self, tagBits, setBits, offsetBits, numCores) -> None:
        self.offsetBits = offsetBits
        self.setBits = setBits
        self.tagBits = tagBits
        self.coreBits = math.ceil(math.log2(numCores))

    def parseAddress(self, x: int, coreID: int, numCores: int) -> Tuple[int, int, int]:
        offset: int = x
        setIdx: int = offset >> self.offsetBits
        coreBits: int = math.ceil(math.log2(numCores))
        updated_set: int
        tag: int
        up_tag: int

        if coreID >= 0:
            updated_set = getBits(setIdx, self.setBits - 1 - coreBits, 0) + (
                coreID << (self.setBits - coreBits)
            )
            tag = setIdx >> (self.setBits - coreBits)
            up_tag = getBits(tag, self.tagBits - 1 + coreBits, 0)
        else:
            updated_set = getBits(setIdx, self.setBits - 1, 0)
            tag = setIdx >> self.setBits
            up_tag = getBits(tag, self.tagBits - 1, 0)

        return (up_tag, updated_set, getBits(offset, self.offsetBits - 1, 0))

    def pAddr(self, x: int, coreId: int) -> Tuple[int, int, int]:
        offset = getBits(x, self.offsetBits - 1, 0)
        setIdx = getBits(x, self.offsetBits + self.setBits - 1, self.offsetBits)
        tag = getBits(
            x,
            self.offsetBits + self.setBits + self.tagBits - 1,
            self.offsetBits + self.setBits,
        )

        tag = (tag << self.coreBits) | getBits(
            setIdx,
            # Get upper <coreBits> bits from setIdx
            self.setBits - 1,
            self.setBits - self.coreBits,
        )
        setIdx = getBits(setIdx, self.setBits - self.coreBits - 1, 0) | coreId << (
            self.setBits - self.coreBits
        )

        return (tag, setIdx, offset)


def printSplitAddr(addr: int, splitAddr: Tuple[int, int, int]):
    print(f"=======================")
    print(f"Adr: 0x{addr:x}")
    print(f"Tag: 0x{splitAddr[0]:x}")
    print(f"Set: 0x{splitAddr[1]:x}")
    print(f"Ofs: 0x{splitAddr[2]:x}")
    print(f"=======================")


if __name__ == "__main__":
    assert getBits(0x1234, 11, 4) == 0x23

    # 1010 1011 1100 1101
    #    ^        ^
    #    0 1011 110
    # 0b01011110
    assert getBits(0xABCD, 12, 5) == 0b01011110

    # 0b10101010
    #   76543210
    #     ^   ^
    #     10101
    assert getBits(0b10101010, 5, 1) == 0b10101

    NUM_CORES: int = 4
    dut: DummySifiveCache = DummySifiveCache(8, 4, 4, NUM_CORES)

    assert dut.pAddr(0xAAAA, 3) == (0x2AA, 0xE, 0xA)
    assert dut.pAddr(0x5ABC, 2) == (0x16A, 0xB, 0xC)

    for x in range(1024):
        addr = random.randrange(0, 2**16)
        core = random.randrange(0, NUM_CORES)

        parseAddress_result = dut.parseAddress(addr, core, NUM_CORES)
        pAddr_result = dut.pAddr(addr, core)

        if pAddr_result != parseAddress_result:
            printSplitAddr(addr, parseAddress_result)
            printSplitAddr(addr, pAddr_result)
            print(f"MISMATCH (coreId = {core})")
