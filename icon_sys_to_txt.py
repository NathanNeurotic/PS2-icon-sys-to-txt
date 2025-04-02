import sys
import struct
import unicodedata
import os

def scale_sys_value(v):
    return round(min(128, v) * 255 / 128)

def read_rgb_rgba_block(data, offset):
    # PS2 stores RGBA as: [R, _, _, _, G, _, _, _, B, _, _, _, A, _, _, _]
    r = scale_sys_value(data[offset])
    g = scale_sys_value(data[offset + 4])
    b = scale_sys_value(data[offset + 8])
    return (r, g, b)

def read_light_rgb_floats(data, offset):
    # Each light color is 3 float32 values (R, G, B)
    return tuple(round(struct.unpack('<f', data[offset + i*4:offset + i*4 + 4])[0] * 255) for i in range(3))

def read_light_direction(data, offset):
    # 3 consecutive float32 values: X, Y, Z
    return struct.unpack('<fff', data[offset:offset+12])

def decode_title(data, offset=0xC0, length=68):
    raw = data[offset:offset+length].split(b'\x00')[0]
    try:
        decoded = raw.decode('shift_jis')
        return unicodedata.normalize('NFKC', decoded)
    except Exception:
        return ""

def parse_icon_sys(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    if data[:4] != b"PS2D":
        raise ValueError("This is not a valid icon.sys file (missing PS2D header).")

    parsed = {
        "title0": decode_title(data),
        "title1": "",
        "bgcola": data[0x0C],
        "bgcol0": read_rgb_rgba_block(data, 0x10),
        "bgcol1": read_rgb_rgba_block(data, 0x20),
        "bgcol2": read_rgb_rgba_block(data, 0x30),
        "bgcol3": read_rgb_rgba_block(data, 0x40),
        "lightdir0": read_light_direction(data, 0x50),
        "lightdir1": read_light_direction(data, 0x60),
        "lightdir2": read_light_direction(data, 0x70),
        "lightcol0": read_light_rgb_floats(data, 0x80),
        "lightcol1": read_light_rgb_floats(data, 0x90),
        "lightcol2": read_light_rgb_floats(data, 0xA0),
        "lightcolamb": read_light_rgb_floats(data, 0xB0),
        "uninstallmes0": "",
        "uninstallmes1": "",
        "uninstallmes2": ""
    }

    return parsed

def write_icon_txt(parsed, output_path):
    lines = [
        "PS2X",
        f"title0={parsed['title0']}",
        f"title1={parsed['title1']}",
        f"bgcola={parsed['bgcola']}",
        f"bgcol0={','.join(map(str, parsed['bgcol0']))}",
        f"bgcol1={','.join(map(str, parsed['bgcol1']))}",
        f"bgcol2={','.join(map(str, parsed['bgcol2']))}",
        f"bgcol3={','.join(map(str, parsed['bgcol3']))}",
        f"lightdir0={','.join(f'{v:.6f}' for v in parsed['lightdir0'])}",
        f"lightdir1={','.join(f'{v:.6f}' for v in parsed['lightdir1'])}",
        f"lightdir2={','.join(f'{v:.6f}' for v in parsed['lightdir2'])}",
        f"lightcolamb={','.join(map(str, parsed['lightcolamb']))}",
        f"lightcol0={','.join(map(str, parsed['lightcol0']))}",
        f"lightcol1={','.join(map(str, parsed['lightcol1']))}",
        f"lightcol2={','.join(map(str, parsed['lightcol2']))}",
        f"uninstallmes0={parsed['uninstallmes0']}",
        f"uninstallmes1={parsed['uninstallmes1']}",
        f"uninstallmes2={parsed['uninstallmes2']}"
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[U+2713.] icon.txt successfully written to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python icon_sys_to_txt.py path/to/icon.sys")
        sys.exit(1)

    icon_sys_path = sys.argv[1]
    out_path = os.path.join(os.path.dirname(icon_sys_path), "icon.txt")

    try:
        parsed_data = parse_icon_sys(icon_sys_path)
        write_icon_txt(parsed_data, out_path)
    except Exception as e:
        print(f"[!] Failed to parse icon.sys: {e}")
