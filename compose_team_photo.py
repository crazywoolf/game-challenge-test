"""Composite every community runner sprite into one team picture (stdlib only)."""

import json
import pathlib
import struct
import zlib


ROOT = pathlib.Path(__file__).parent
BACKGROUND = ROOT / "images/characters/team-photo-background.png"
ROSTER = ROOT / "images/community-characters/characters.json"
OUTPUT = ROOT / "images/characters/team-photo-running.png"
WIDTH, HEIGHT = 2400, 1600


def read_png(path):
    blob = path.read_bytes()
    pos = 8
    chunks = []
    width = height = color_type = bit_depth = None
    while pos < len(blob):
        length = struct.unpack(">I", blob[pos:pos + 4])[0]
        kind = blob[pos + 4:pos + 8]
        payload = blob[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if bit_depth != 8 or compression or filtering or interlace:
                raise ValueError(f"Unsupported PNG encoding in {path}")
        elif kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            break
    bpp = {2: 3, 6: 4}.get(color_type)
    if not bpp:
        raise ValueError(f"Expected RGB/RGBA PNG in {path}")
    raw = zlib.decompress(b"".join(chunks))
    stride = width * bpp
    rows = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        mode = raw[offset]
        offset += 1
        scan = bytearray(raw[offset:offset + stride])
        offset += stride
        for i in range(stride):
            left = scan[i - bpp] if i >= bpp else 0
            above = previous[i]
            upper_left = previous[i - bpp] if i >= bpp else 0
            if mode == 1:
                scan[i] = (scan[i] + left) & 255
            elif mode == 2:
                scan[i] = (scan[i] + above) & 255
            elif mode == 3:
                scan[i] = (scan[i] + ((left + above) // 2)) & 255
            elif mode == 4:
                p = left + above - upper_left
                pa, pb, pc = abs(p - left), abs(p - above), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else above if pb <= pc else upper_left
                scan[i] = (scan[i] + predictor) & 255
            elif mode != 0:
                raise ValueError(f"Unknown PNG filter {mode} in {path}")
        rows.append(scan)
        previous = scan
    rgba = bytearray(width * height * 4)
    for i in range(width * height):
        source = i * bpp
        target = i * 4
        rgba[target:target + 3] = rows[source // stride][source % stride:source % stride + 3]
        rgba[target + 3] = rows[source // stride][source % stride + 3] if bpp == 4 else 255
    return width, height, rgba


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def write_png(path, width, height, rgba):
    rows = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(rows, 8)) + png_chunk(b"IEND", b"")
    path.write_bytes(data)


def blend_pixel(canvas, offset, color, alpha):
    if alpha == 0:
        return
    inverse = 255 - alpha
    canvas[offset] = (color[0] * alpha + canvas[offset] * inverse) // 255
    canvas[offset + 1] = (color[1] * alpha + canvas[offset + 1] * inverse) // 255
    canvas[offset + 2] = (color[2] * alpha + canvas[offset + 2] * inverse) // 255
    canvas[offset + 3] = 255


def fill_rect(canvas, x, y, width, height, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(WIDTH, x + width), min(HEIGHT, y + height)
    row = bytes(color) * max(0, x1 - x0)
    for py in range(y0, y1):
        start = (py * WIDTH + x0) * 4
        canvas[start:start + len(row)] = row


def composite_sprite(canvas, x, y, size, sprite):
    source_width, source_height, pixels = sprite
    left = max(0, x)
    top = max(0, y)
    right = min(WIDTH, x + size)
    bottom = min(HEIGHT, y + size)
    for dy in range(top, bottom):
        sy = min(source_height - 1, (dy - y) * source_height // size)
        for dx in range(left, right):
            sx = min(source_width - 1, (dx - x) * source_width // size)
            source = (sy * source_width + sx) * 4
            alpha = pixels[source + 3]
            if alpha:
                blend_pixel(canvas, (dy * WIDTH + dx) * 4, pixels[source:source + 3], alpha)


def main():
    bg_width, bg_height, bg = read_png(BACKGROUND)
    canvas = bytearray(WIDTH * HEIGHT * 4)
    for y in range(HEIGHT):
        sy = min(bg_height - 1, y * bg_height // HEIGHT)
        for x in range(WIDTH):
            sx = min(bg_width - 1, x * bg_width // WIDTH)
            src, dst = (sy * bg_width + sx) * 4, (y * WIDTH + x) * 4
            canvas[dst:dst + 4] = bg[src:src + 4]

    people = json.loads(ROSTER.read_text())
    row_counts = [5, 6, 7, 8, 8, 7]
    row_sizes = [140, 155, 170, 185, 200, 215]
    row_gaps = [72, 66, 58, 45, 42, 48]
    row_baselines = [700, 850, 1000, 1150, 1300, 1450]
    platform_widths = [1050, 1320, 1600, 1880, 2020, 1950]
    offset = 0
    for row, count in enumerate(row_counts):
        size, gap, baseline = row_sizes[row], row_gaps[row], row_baselines[row]
        group_width = count * size + (count - 1) * gap
        start_x = round((WIDTH - group_width) / 2)
        platform_x = round((WIDTH - platform_widths[row]) / 2)
        fill_rect(canvas, platform_x, baseline, platform_widths[row], 8, (103, 190, 87, 255))
        fill_rect(canvas, platform_x, baseline + 8, platform_widths[row], 18, (112, 84, 56, 255))
        fill_rect(canvas, platform_x, baseline + 8, platform_widths[row], 4, (82, 147, 73, 255))
        for col in range(count):
            person = people[offset + col]
            x = start_x + col * (size + gap)
            y = baseline - size
            sprite = read_png(ROOT / "images" / "community-characters" / person["image"])
            composite_sprite(canvas, x, y, size, sprite)
        offset += count
    write_png(OUTPUT, WIDTH, HEIGHT, canvas)
    print(f"Saved {OUTPUT} with {len(people)} characters ({WIDTH}x{HEIGHT}).")


if __name__ == "__main__":
    main()
