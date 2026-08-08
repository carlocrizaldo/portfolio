import struct, zlib, math, os

BG = (10, 12, 16)
BLUE = (76, 141, 255)
BLUE2 = (110, 168, 254)
SIZES = [16, 32, 48, 64, 128, 256]

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def render_supersample(size):
    S = size * 4
    grid = [[BG for _ in range(S)] for _ in range(S)]
    cx = cy = S / 2.0
    R = S * 0.42
    r_in = S * 0.17
    for y in range(S):
        for x in range(S):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            theta = math.degrees(math.atan2(dy, dx)) % 360
            on_ring = r_in <= d <= R
            gap = (theta < 55 or theta > 305)   # open the RIGHT side -> "C"
            if on_ring and not gap:
                t = (d - r_in) / (R - r_in)
                grid[y][x] = lerp(BLUE, BLUE2, t)
    return grid, S

def downscale(grid, S):
    size = S // 4
    out = [[BG for _ in range(size)] for _ in range(size)]
    acc = [0, 0, 0]
    for y in range(size):
        for x in range(size):
            acc = [0, 0, 0]
            for yy in range(4):
                for xx in range(4):
                    r, g, b = grid[y*4+yy][x*4+xx]
                    acc[0]+=r; acc[1]+=g; acc[2]+=b
            out[y][x] = (acc[0]//16, acc[1]//16, acc[2]//16)
    return out, size

def to_png(grid, size):
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            r, g, b = grid[y][x]
            raw += bytes((r, g, b, 255))
    def chunk(typ, data):
        return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ+data) & 0xffffffff)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

pngs = {}
for s in SIZES:
    grid, S = render_supersample(s)
    small, _ = downscale(grid, S)
    pngs[s] = to_png(small, s)

# assemble .ico with PNG payloads
ico = bytearray()
ico += struct.pack("<HHH", 0, 1, len(SIZES))
offset = 6 + 16 * len(SIZES)
for s in SIZES:
    png = pngs[s]
    ico += bytes((s % 256, s // 256, 0, 0, 0, 0, 32, 0))
    ico += struct.pack("<I", len(png)) + struct.pack("<I", offset)
    offset += len(png)
for s in SIZES:
    ico += pngs[s]

with open("favicon.ico", "wb") as f:
    f.write(ico)
with open("favicon-196.png", "wb") as f:
    f.write(pngs[128])
with open("favicon-32.png", "wb") as f:
    f.write(pngs[32])

print("favicon.ico:", os.path.getsize("favicon.ico"), "bytes")
print("favicon-196.png:", os.path.getsize("favicon-196.png"), "bytes")
print("favicon-32.png:", os.path.getsize("favicon-32.png"), "bytes")
