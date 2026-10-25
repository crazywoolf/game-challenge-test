"""Generate the game's compact pixel-art preference icons with only Python's stdlib."""

import json
import pathlib
import struct
import zlib


ROOT = pathlib.Path(__file__).parent
DATA_FILE = ROOT / "mock-character-data.json"
OUT = ROOT / "images" / "game-items"
SCALE = 4
SIZE = 32
PNG_SIZE = SIZE * SCALE
DARK = (39, 48, 67, 255)
WHITE = (255, 251, 232, 255)
RED = (235, 92, 76, 255)
YELLOW = (255, 211, 71, 255)
GREEN = (91, 183, 105, 255)
BLUE = (77, 158, 211, 255)
PURPLE = (150, 105, 207, 255)


class PixelImage:
    def __init__(self):
        self.pixels = bytearray(PNG_SIZE * PNG_SIZE * 4)

    def put(self, x, y, color):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            offset = (y * SCALE * PNG_SIZE + x * SCALE) * 4
            for yy in range(SCALE):
                row = offset + yy * PNG_SIZE * 4
                for xx in range(SCALE):
                    self.pixels[row + xx * 4:row + xx * 4 + 4] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, color)

    def disc(self, cx, cy, radius, color):
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                    self.put(x, y, color)

    def polygon(self, points, color):
        xs, ys = zip(*points)
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                inside = False
                j = len(points) - 1
                for i, (xi, yi) in enumerate(points):
                    xj, yj = points[j]
                    if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1) + xi:
                        inside = not inside
                    j = i
                if inside:
                    self.put(x, y, color)

    def line(self, x1, y1, x2, y2, color, width=1):
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        err = dx - dy
        while True:
            self.rect(x1 - width // 2, y1 - width // 2, width, width, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def png(self, path):
        rows = b"".join(b"\0" + self.pixels[y * PNG_SIZE * 4:(y + 1) * PNG_SIZE * 4] for y in range(PNG_SIZE))

        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)

        content = b"\x89PNG\r\n\x1a\n"
        content += chunk(b"IHDR", struct.pack(">IIBBBBB", PNG_SIZE, PNG_SIZE, 8, 6, 0, 0, 0))
        content += chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
        path.write_bytes(content)


def draw_glyph(img, kind, accent):
    a = accent
    d, w = DARK, WHITE
    if kind in {"book", "reading", "school", "english", "homework", "biology", "comic", "study"}:
        img.rect(7, 9, 8, 14, d); img.rect(17, 9, 8, 14, d)
        img.rect(8, 10, 6, 11, w); img.rect(18, 10, 6, 11, w)
        img.rect(15, 8, 2, 17, a)
        for y in (13, 16, 19):
            img.rect(9, y, 4, 1, BLUE if kind in {"biology", "english"} else a)
            img.rect(19, y, 4, 1, BLUE if kind in {"biology", "english"} else a)
        if kind == "comic":
            img.rect(10, 5, 5, 3, RED); img.rect(19, 5, 5, 3, YELLOW)
    elif kind in {"pizza", "food", "sweet", "drink", "lemonade"}:
        if kind == "pizza":
            img.polygon([(8, 8), (25, 23), (5, 24)], YELLOW)
            img.line(5, 24, 25, 23, d, 2)
            for x, y in ((12, 14), (17, 17), (10, 20)):
                img.disc(x, y, 1, RED)
        elif kind in {"drink", "lemonade"}:
            img.rect(10, 10, 12, 15, d); img.rect(12, 12, 8, 10, BLUE if kind == "drink" else YELLOW)
            img.line(17, 5, 21, 10, RED, 2); img.rect(12, 25, 8, 2, d)
        elif kind == "sweet":
            img.rect(10, 10, 12, 10, d); img.rect(12, 8, 8, 14, RED); img.rect(14, 22, 4, 5, d)
            img.rect(11, 27, 10, 2, YELLOW)
        else:
            img.rect(7, 12, 18, 4, d); img.rect(9, 8, 14, 4, YELLOW)
            img.rect(9, 16, 14, 4, GREEN); img.rect(11, 20, 10, 4, RED); img.rect(8, 24, 16, 3, d)
    elif kind in {"game", "phone", "internet", "tanks"}:
        if kind == "phone":
            img.rect(11, 5, 10, 22, d); img.rect(13, 8, 6, 15, BLUE); img.rect(15, 24, 2, 1, w)
        elif kind == "internet":
            for y, width in ((9, 6), (13, 12), (17, 18)):
                img.line(16 - width // 2, y + 4, 16, y, a, 2)
                img.line(16, y, 16 + width // 2, y + 4, a, 2)
            img.disc(16, 23, 2, d)
        elif kind == "tanks":
            img.rect(7, 17, 18, 7, d); img.rect(10, 13, 11, 5, GREEN); img.rect(16, 10, 11, 2, d)
            for x in (10, 16, 22): img.disc(x, 25, 2, YELLOW)
        else:
            img.rect(7, 10, 18, 12, d); img.rect(10, 8, 12, 3, d); img.rect(11, 12, 10, 7, a)
            img.rect(10, 14, 5, 1, d); img.rect(12, 12, 1, 5, d)
            img.disc(20, 14, 1, RED); img.disc(22, 17, 1, YELLOW)
    elif kind in {"music", "classical", "film"}:
        if kind == "film":
            img.rect(6, 8, 20, 18, d); img.rect(8, 14, 16, 10, a)
            for x in (8, 15, 22): img.rect(x, 9, 3, 4, w)
            img.line(8, 12, 16, 8, RED, 2); img.line(16, 8, 24, 12, RED, 2)
        else:
            img.rect(10, 8, 3, 14, d); img.rect(20, 6, 3, 13, d)
            img.rect(12, 8, 11, 2, a); img.rect(12, 14, 11, 2, a)
            img.disc(9, 23, 3, BLUE); img.disc(19, 20, 3, RED)
            if kind == "classical": img.rect(7, 5, 18, 2, d)
    elif kind in {"sports", "football", "tennis", "gymnastics", "skating", "swim", "dance"}:
        if kind == "football":
            img.disc(16, 16, 10, d); img.disc(16, 16, 8, w); img.polygon([(16, 12), (20, 14), (19, 19), (14, 19), (12, 15)], d)
            for x, y in ((9, 13), (22, 11), (23, 20), (8, 21)):
                img.rect(x, y, 3, 3, BLUE)
        elif kind == "tennis":
            img.disc(12, 12, 7, d); img.disc(12, 12, 5, GREEN)
            img.line(17, 17, 24, 24, d, 3); img.disc(24, 9, 4, YELLOW); img.rect(21, 8, 3, 1, w)
        elif kind == "skating":
            img.rect(7, 14, 17, 7, d); img.rect(10, 10, 10, 5, a); img.rect(22, 17, 5, 4, RED)
            for x in (10, 16, 22): img.disc(x, 24, 2, d)
        elif kind in {"swim", "dance"}:
            img.disc(16, 8, 3, YELLOW); img.line(16, 11, 16, 20, d, 3)
            img.line(16, 14, 9, 18, d, 2); img.line(16, 14, 23, 17, d, 2)
            if kind == "swim":
                for y in (23, 27): img.line(7, y, 25, y, BLUE, 2)
            else:
                img.line(16, 20, 10, 26, d, 2); img.line(16, 20, 22, 26, d, 2); img.disc(25, 8, 3, RED)
        else:
            img.rect(8, 11, 16, 12, d); img.rect(10, 13, 12, 8, a); img.rect(13, 9, 6, 2, YELLOW)
            img.rect(5, 16, 3, 3, BLUE); img.rect(24, 16, 3, 3, RED)
    elif kind in {"pencil", "draw", "paper", "copy"}:
        img.rect(9, 7, 15, 19, d); img.rect(11, 9, 11, 15, w)
        img.line(11, 21, 22, 10, a, 3); img.polygon([(20, 9), (24, 7), (23, 12)], d)
        if kind == "copy": img.rect(7, 5, 8, 2, BLUE)
    elif kind in {"cat", "catdraw", "friends", "green", "sun", "vacation", "holiday"}:
        if kind in {"cat", "catdraw"}:
            img.rect(9, 11, 14, 13, d); img.polygon([(9, 12), (9, 6), (14, 11)], d); img.polygon([(18, 11), (23, 6), (23, 12)], d)
            img.rect(12, 15, 2, 2, YELLOW); img.rect(18, 15, 2, 2, YELLOW); img.rect(14, 19, 4, 2, RED)
            if kind == "catdraw": img.line(23, 24, 27, 19, a, 2)
        elif kind == "friends":
            img.disc(11, 12, 5, YELLOW); img.disc(21, 12, 5, RED)
            img.rect(7, 18, 9, 8, BLUE); img.rect(17, 18, 9, 8, GREEN)
        elif kind in {"sun", "vacation", "holiday"}:
            img.disc(16, 15, 7, YELLOW)
            for x1, y1, x2, y2 in ((16, 4, 16, 7), (16, 23, 16, 27), (5, 15, 8, 15), (24, 15, 27, 15), (8, 7, 10, 9), (22, 21, 24, 23)):
                img.line(x1, y1, x2, y2, RED, 2)
            if kind == "vacation": img.line(7, 27, 25, 27, BLUE, 2)
        else:
            img.rect(12, 10, 8, 15, GREEN); img.polygon([(12, 16), (5, 10), (9, 20)], a); img.polygon([(20, 15), (27, 9), (23, 21)], GREEN)
    elif kind in {"fish", "fishing", "fishbroom"}:
        img.polygon([(8, 16), (14, 11), (22, 13), (25, 16), (22, 20), (14, 21)], BLUE if kind != "fishing" else GREEN)
        img.polygon([(8, 16), (4, 11), (4, 21)], RED); img.disc(20, 15, 1, DARK)
        if kind == "fishing": img.line(8, 6, 20, 12, DARK, 1); img.line(20, 12, 23, 14, RED, 1)
        if kind == "fishbroom": img.line(25, 20, 28, 27, RED, 2)
    elif kind in {"cabbage", "broom", "cleaning", "work", "briefcase", "sock", "clock", "ricochet", "lab", "ribbon"}:
        if kind == "cabbage":
            img.disc(16, 17, 9, GREEN); img.disc(12, 16, 5, a); img.disc(19, 14, 5, GREEN); img.rect(15, 23, 3, 4, RED)
        elif kind in {"broom", "cleaning"}:
            img.line(11, 6, 21, 22, d, 3); img.polygon([(17, 20), (24, 23), (27, 28), (15, 27)], a)
            for x in (17, 20, 23): img.line(x, 25, x - 1, 29, RED, 1)
        elif kind in {"work", "briefcase"}:
            img.rect(7, 13, 19, 13, d); img.rect(9, 16, 15, 8, a); img.rect(13, 9, 7, 4, d); img.rect(14, 10, 5, 2, w)
            img.rect(15, 18, 3, 3, YELLOW)
        elif kind == "sock":
            img.polygon([(11, 7), (20, 7), (20, 17), (24, 21), (24, 26), (13, 26), (13, 20), (10, 17)], d)
            img.polygon([(13, 9), (18, 9), (18, 18), (22, 22), (22, 24), (15, 24), (15, 18), (13, 16)], BLUE)
        elif kind == "clock":
            img.disc(16, 16, 10, d); img.disc(16, 16, 7, w); img.line(16, 16, 16, 10, RED, 2); img.line(16, 16, 21, 18, BLUE, 2)
        elif kind == "ricochet":
            img.rect(6, 17, 16, 7, d); img.rect(10, 13, 10, 5, GREEN); img.line(18, 14, 27, 8, RED, 2)
            img.line(26, 6, 29, 3, YELLOW, 2); img.line(27, 12, 30, 12, YELLOW, 2)
        elif kind == "lab":
            img.polygon([(11, 7), (21, 7), (21, 10), (19, 10), (19, 17), (25, 25), (25, 27), (7, 27), (7, 25), (13, 17), (13, 10), (11, 10)], d)
            img.rect(11, 22, 10, 3, BLUE); img.rect(13, 11, 6, 6, w)
        else:
            img.disc(11, 11, 4, YELLOW); img.disc(22, 11, 4, RED); img.line(11, 14, 16, 27, PURPLE, 2); img.line(22, 14, 16, 27, BLUE, 2)
    else:
        img.rect(8, 9, 16, 16, d); img.rect(11, 12, 10, 10, a); img.disc(16, 16, 2, YELLOW)


def category(label, obstacle=False):
    text = label.casefold()
    if obstacle:
        if "англий" in text: return "english"
        if "биолог" in text: return "biology"
        if "домаш" in text: return "homework"
        if "инструкц" in text: return "clock"
        if "капуст" in text: return "cabbage"
        if "носить синие носки" in text: return "sock"
        if "работ" in text: return "briefcase"
        if "рикош" in text: return "ricochet"
        if "скукот" in text: return "clock"
        if "классик" in text: return "classical"
        if "убир" in text or "уборк" in text:
            return "fishbroom" if "рыб" in text else "broom"
        if "урок" in text or "учить" in text: return "school"
        if "футбол" in text: return "football"
        if "чтение" in text: return "reading"
        return "school"
    if "пицц" in text: return "pizza"
    if "теннис" in text: return "tennis"
    if "футбол" in text: return "football"
    if "вкусн" in text and "лимонад" in text: return "lemonade"
    if "лимонад" in text: return "drink"
    if "сладк" in text: return "sweet"
    if "танки" in text or "tanks" in text: return "tanks"
    if "телефон" in text: return "phone"
    if "интернет" in text: return "internet"
    if "манг" in text or "аниме" in text: return "comic"
    if "робlox" in text or "roblox" in text or "brawl" in text or "minecraft" in text or "игр" in text: return "game"
    if "музык" in text or "слушать" in text: return "music"
    if "друз" in text or "подруг" in text or "общаться" in text: return "friends"
    if "купаться" in text: return "swim"
    if "кататься" in text or "ролик" in text: return "skating"
    if "танцев" in text: return "dance"
    if "смотреть фильм" in text or "фильм" in text: return "film"
    if "рисоват" in text and "кот" in text: return "catdraw"
    if "кот" in text: return "cat"
    if "рисоват" in text or "рисовать" in text: return "pencil"
    if "читать" in text or "чтение" in text: return "book"
    if "рыбал" in text: return "fishing"
    if "солнц" in text or "каникул" in text or "отпуск" in text: return "sun"
    if "зелён" in text or "зелен" in text: return "green"
    if "гимнаст" in text: return "ribbon"
    if "есть" in text or "вкусно" in text: return "food"
    if "плав" in text: return "swim"
    if "гулять" in text or "бег" in text: return "sports"
    if "списыв" in text: return "copy"
    if "67" in text: return "game"
    return "sun"


def draw_tile(label, obstacle, variant):
    img = PixelImage()
    accent = [RED, BLUE, GREEN, PURPLE, YELLOW][variant % 5]
    if obstacle:
        img.rect(2, 2, 28, 28, DARK)
        img.rect(3, 3, 26, 26, (255, 193, 174, 255))
    else:
        img.disc(16, 16, 15, DARK)
        img.disc(16, 16, 13, (255, 226, 117, 255))
    draw_glyph(img, category(label, obstacle), accent)
    return img


def main():
    data = json.loads(DATA_FILE.read_text())
    likes = sorted({c.get("likes", "").strip() for c in data["characters"] if c.get("likes", "").strip() not in ("", "Не указано")}, key=str.casefold)
    dislikes = sorted({c.get("dislikes", "").strip() for c in data["characters"] if c.get("dislikes", "").strip() not in ("", "Не указано")}, key=str.casefold)
    art = {"collectibles": {}, "obstacles": {}}
    for kind, labels, obstacle in (("collectibles", likes, False), ("obstacles", dislikes, True)):
        for index, label in enumerate(labels, 1):
            subdir = "collectibles" if not obstacle else "obstacles"
            filename = f"{subdir[:-1]}-{index:03d}.png"
            path = OUT / subdir / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            draw_tile(label, obstacle, index).png(path)
            art[kind][label] = f"images/game-items/{subdir}/{filename}"
    (OUT / "item-art.json").write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n")
    js = "window.gameItemArt = " + json.dumps(art, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ROOT / "game-item-art.js").write_text(js)
    data["game_item_art"] = art
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Generated {len(likes)} collectible and {len(dislikes)} obstacle icons.")


if __name__ == "__main__":
    main()
