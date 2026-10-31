#!/usr/bin/env python3
"""
Generates the Gazebo world of our college robotics lab (from lab_images_reference/).

    python3 generate_lab_world.py      ->  worlds/mahadev_lab.world
                                           models/mahadev_lab_media/  (textures + OGRE materials)

Coordinates (metres). Origin = room centre, floor = z 0. Standing in the room facing the TV:
    +x  front wall : TV, podium, glass double door        (x = +6.5)
    -x  back wall  : windows, orange mat, faculty desk     (x = -6.5)
    -y  right wall : PC counter + shelf unit/whiteboard    (y = -4.5)
    +y  left wall  : long empty counter + stools, blue desk (y = +4.5)
    centre         : long white conference table, planters, monitors, chairs
Sizes are estimated from photos (floor tiles ~0.6 m). Edit the numbers below and re-run.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
MEDIA = os.path.join(PKG, "models", "mahadev_lab_media")
WORLD_FILE = os.path.join(HERE, "mahadev_lab.world")

ROOM_X, ROOM_Y, ROOM_H, WALL_T = 13.0, 9.0, 3.2, 0.15
HX, HY = ROOM_X / 2, ROOM_Y / 2
TILE = 0.6

random.seed(7)

# ------------------------------------------------------------------ textures
def make_textures():
    tex = os.path.join(MEDIA, "materials", "textures")
    os.makedirs(tex, exist_ok=True)

    # floor: 4x4 slate tiles in two grey-green shades, thin grout
    px = 128
    img = Image.new("RGB", (4 * px, 4 * px))
    d = ImageDraw.Draw(img)
    for i in range(4):
        for j in range(4):
            base = (84, 90, 86) if (i + j) % 2 else (100, 106, 101)
            jit = random.randint(-6, 6)
            d.rectangle([i * px, j * px, (i + 1) * px - 1, (j + 1) * px - 1],
                        fill=tuple(c + jit for c in base))
    for _ in range(6000):
        x, y = random.randrange(4 * px), random.randrange(4 * px)
        v = random.randint(-14, 14)
        r, g, b = img.getpixel((x, y))
        img.putpixel((x, y), (r + v, g + v, b + v))
    for k in range(5):
        d.line([k * px, 0, k * px, 4 * px], fill=(70, 72, 70), width=2)
        d.line([0, k * px, 4 * px, k * px], fill=(70, 72, 70), width=2)
    img.filter(ImageFilter.SMOOTH).save(os.path.join(tex, "floor_tiles.png"))

    # light oak laminate with fine grain
    img = Image.new("RGB", (256, 256), (214, 180, 150))
    d = ImageDraw.Draw(img)
    for x in range(256):
        v = random.randint(-14, 10)
        d.line([x, 0, x, 255], fill=(214 + v, 180 + v, 150 + v))
    img.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(tex, "wood_light.png"))

    # wall slat panel (dado): vertical brown slats with dark gaps, ~0.6 m per image
    img = Image.new("RGB", (240, 64), (60, 42, 30))
    d = ImageDraw.Draw(img)
    for x in range(0, 240, 16):
        d.rectangle([x + 2, 0, x + 13, 63], fill=(150 + random.randint(-12, 12), 115, 80))
    img.save(os.path.join(tex, "wall_slats.png"))

    # rattan lattice (diamond weave) used on faculty desk and counter arches
    img = Image.new("RGB", (128, 128), (200, 160, 100))
    d = ImageDraw.Draw(img)
    for k in range(-128, 256, 16):
        d.line([k, 0, k + 128, 128], fill=(140, 100, 55), width=3)
        d.line([k, 128, k + 128, 0], fill=(140, 100, 55), width=3)
    img.save(os.path.join(tex, "lattice.png"))

    # window blinds: horizontal mauve-grey bands
    img = Image.new("RGB", (64, 256), (150, 135, 135))
    d = ImageDraw.Draw(img)
    for y in range(0, 256, 12):
        d.rectangle([0, y, 63, y + 7], fill=(178, 165, 165))
    img.save(os.path.join(tex, "blinds.png"))


# texture materials: name -> (texture file, u_repeats, v_repeats)
TEX_MATS = {}


def tex_mat(texture, ru=1.0, rv=1.0):
    name = "Mahadev/%s_%g_%g" % (texture.split(".")[0], round(ru, 1), round(rv, 1))
    TEX_MATS[name] = (texture, max(ru, 0.1), max(rv, 0.1))
    return ("script", name)


def write_material_script():
    scripts = os.path.join(MEDIA, "materials", "scripts")
    os.makedirs(scripts, exist_ok=True)
    with open(os.path.join(scripts, "mahadev_lab.material"), "w") as f:
        for name, (texture, ru, rv) in sorted(TEX_MATS.items()):
            f.write("material %s\n{\n  technique\n  {\n    pass\n    {\n"
                    "      ambient 0.8 0.8 0.8 1\n      diffuse 1 1 1 1\n      specular 0.1 0.1 0.1 1 5\n"
                    "      texture_unit\n      {\n        texture %s\n        filtering anisotropic\n"
                    "        max_anisotropy 8\n        scale %.4f %.4f\n      }\n    }\n  }\n}\n\n"
                    % (name, texture, 1.0 / ru, 1.0 / rv))
    with open(os.path.join(MEDIA, "model.config"), "w") as f:
        f.write("<?xml version='1.0'?>\n<model>\n  <name>mahadev_lab_media</name>\n  <version>1.0</version>\n"
                "  <sdf version='1.6'>model.sdf</sdf>\n  <description>Textures for Mahadev's lab world</description>\n</model>\n")
    with open(os.path.join(MEDIA, "model.sdf"), "w") as f:
        f.write("<?xml version='1.0'?>\n<sdf version='1.6'><model name='mahadev_lab_media'><static>true</static>"
                "<link name='l'/></model></sdf>\n")


# ------------------------------------------------------------------ colours
C = {
    "wall": (0.93, 0.91, 0.87, 1), "white": (0.92, 0.92, 0.92, 1), "black": (0.05, 0.05, 0.05, 1),
    "screen": (0.02, 0.02, 0.03, 1), "chrome": (0.75, 0.75, 0.78, 1), "grey": (0.45, 0.45, 0.47, 1),
    "darkgrey": (0.25, 0.25, 0.27, 1), "blue": (0.10, 0.32, 0.85, 1), "orange": (0.93, 0.45, 0.20, 1),
    "skirting": (0.45, 0.25, 0.15, 1), "planter": (0.25, 0.18, 0.13, 1), "red": (0.85, 0.08, 0.06, 1),
    "green1": (0.20, 0.50, 0.18, 1), "green2": (0.35, 0.62, 0.22, 1), "green3": (0.55, 0.70, 0.30, 1),
    "glass": (0.75, 0.85, 0.85, 1), "outside": (0.55, 0.75, 0.55, 1), "wood": (0.84, 0.70, 0.58, 1),
    "stool": (0.85, 0.62, 0.40, 1), "whiteboard": (0.97, 0.95, 0.92, 1), "poster": (0.95, 0.95, 0.92, 1),
    "frame_wood": (0.85, 0.72, 0.55, 1),
}


def material_xml(mat):
    if isinstance(mat, tuple) and mat[0] == "script":
        return ("<material><script><uri>model://mahadev_lab_media/materials/scripts</uri>"
                "<uri>model://mahadev_lab_media/materials/textures</uri><name>%s</name></script></material>" % mat[1])
    r, g, b, a = C[mat] if isinstance(mat, str) else mat
    return ("<material><ambient>%g %g %g %g</ambient><diffuse>%g %g %g %g</diffuse>"
            "<specular>0.1 0.1 0.1 1</specular></material>" % (r, g, b, a, r, g, b, a))


# ------------------------------------------------------------------ SDF builders
class Model:
    """A static model: list of visuals and (simple) collisions in local coords."""

    def __init__(self, name, x=0.0, y=0.0, yaw=0.0):
        self.name, self.pose = name, (x, y, 0, 0, 0, yaw)
        self.parts, self.n = [], 0

    def _add(self, geom, pose, mat, collide, transparency=0.0):
        self.n += 1
        p = " ".join("%.4f" % v for v in pose)
        s = "<visual name='v%d'><pose>%s</pose><geometry>%s</geometry>%s%s</visual>" % (
            self.n, p, geom, material_xml(mat),
            "<transparency>%g</transparency>" % transparency if transparency else "")
        if collide:
            s += ("<collision name='c%d'><pose>%s</pose><geometry>%s</geometry><surface><friction><ode>"
                  "<mu>100</mu><mu2>100</mu2></ode></friction></surface></collision>" % (self.n, p, geom))
        self.parts.append(s)

    def collision_only(self, geom, pos):
        """Invisible simple collision shape (keeps physics cheap for detailed furniture)."""
        self.n += 1
        self.parts.append("<collision name='c%d'><pose>%s 0 0 0</pose><geometry>%s</geometry></collision>"
                          % (self.n, " ".join("%.4f" % v for v in pos), geom))

    def box(self, pos, size, mat, collide=False, rpy=(0, 0, 0), transparency=0.0):
        self._add("<box><size>%g %g %g</size></box>" % size, tuple(pos) + tuple(rpy), mat, collide, transparency)

    def cyl(self, pos, r, length, mat, collide=False, rpy=(0, 0, 0)):
        self._add("<cylinder><radius>%g</radius><length>%g</length></cylinder>" % (r, length),
                  tuple(pos) + tuple(rpy), mat, collide)

    def sphere(self, pos, r, mat, collide=False):
        self._add("<sphere><radius>%g</radius></sphere>" % r, tuple(pos) + (0, 0, 0), mat, collide)

    def sdf(self):
        return ("<model name='%s'><static>true</static><pose>%s</pose><link name='link'>%s</link></model>"
                % (self.name, " ".join("%.4f" % v for v in self.pose), "".join(self.parts)))


MODELS = []


def new(name, x=0.0, y=0.0, yaw=0.0):
    m = Model(name, x, y, yaw)
    MODELS.append(m)
    return m


# ------------------------------------------------------------------ furniture
def stool(name, x, y):
    m = new(name, x, y, random.uniform(0, 2))
    m.cyl((0, 0, 0.64), 0.17, 0.04, "stool")
    phi = math.atan2(0.10, 0.62)
    for k in range(3):
        t = k * 2 * math.pi / 3
        m.cyl((0.15 * math.cos(t), 0.15 * math.sin(t), 0.31), 0.022, 0.63, "stool", rpy=(0, -phi, t))
    m.box((0.0, 0.0, 0.22), (0.30, 0.02, 0.02), "black")
    m.collision_only("<cylinder><radius>0.2</radius><length>0.66</length></cylinder>", (0, 0, 0.33))
    return m


def office_chair(name, x, y, yaw, style="white"):
    """yaw = direction the person sitting faces."""
    m = new(name, x, y, yaw)
    for k in range(5):
        t = k * 2 * math.pi / 5
        m.box((0.15 * math.cos(t), 0.15 * math.sin(t), 0.06), (0.30, 0.04, 0.03), "chrome", rpy=(0, 0, t))
        m.sphere((0.29 * math.cos(t), 0.29 * math.sin(t), 0.03), 0.03, "black")
    m.cyl((0, 0, 0.27), 0.03, 0.4, "chrome" if style == "white" else "black")
    m.box((0, 0, 0.48), (0.48, 0.48, 0.08), "black" if style == "white" else "grey")
    frame = "white" if style == "white" else "darkgrey"
    m.box((-0.24, 0, 0.80), (0.05, 0.46, 0.52), frame)
    m.box((-0.215, 0, 0.80), (0.01, 0.38, 0.42), "black" if style == "white" else "grey")
    for s in (-1, 1):
        m.box((-0.02, s * 0.25, 0.62), (0.36, 0.04, 0.03), frame)
    m.collision_only("<cylinder><radius>0.3</radius><length>0.55</length></cylinder>", (0, 0, 0.275))
    return m


def monitor(m, x, y, z, yaw, w=0.55, h=0.33):
    """Monitor standing on a surface at height z, screen facing yaw."""
    c, s = math.cos(yaw), math.sin(yaw)
    m.box((x - 0.04 * c, y - 0.04 * s, z + 0.01), (0.18, 0.2, 0.02), "black", rpy=(0, 0, yaw))
    m.box((x - 0.04 * c, y - 0.04 * s, z + 0.09), (0.03, 0.05, 0.16), "black", rpy=(0, 0, yaw))
    m.box((x, y, z + 0.1 + h / 2), (0.03, w, h), "black", rpy=(0, 0, yaw))
    m.box((x + 0.016 * c, y + 0.016 * s, z + 0.1 + h / 2), (0.002, w - 0.02, h - 0.02), "screen", rpy=(0, 0, yaw))


def counter(m, x0, x1, y_wall, depth, h, side):
    """Wooden storage counter along a y-wall from x0..x1. side=+1 if room is towards +y."""
    L = x1 - x0
    yc = y_wall + side * depth / 2
    m.box(((x0 + x1) / 2, yc, (h - 0.1) / 2 + 0.1), (L, depth, h - 0.1), tex_mat("wood_light.png", L / 1.0), True)
    m.box(((x0 + x1) / 2, y_wall + side * (depth - 0.06), 0.05), (L - 0.1, depth - 0.15, 0.1), "skirting")
    front = y_wall + side * (depth + 0.003)
    n = int(L / 0.9)
    for k in range(1, n):  # door gaps
        m.box((x0 + k * L / n, front, h / 2 + 0.05), (0.008, 0.004, h - 0.25), "darkgrey")
    for k in range(n):  # knobs
        m.sphere((x0 + (k + 0.5) * L / n, front, h - 0.2), 0.02, "wood")
    return front


def wall(name, x, y, sx, sy):
    m = new(name, x, y)
    m.box((0, 0, ROOM_H / 2), (sx, sy, ROOM_H), "wall", True)
    return m


def slats(m, x, y, length, along_x):
    size = (length, 0.02, 0.9) if along_x else (0.02, length, 0.9)
    m.box((x, y, 0.45), size, tex_mat("wall_slats.png", length / 0.6))
    top = (length, 0.04, 0.03) if along_x else (0.04, length, 0.03)
    m.box((x, y, 0.915), top, "skirting")


def skirting(m, x, y, length, along_x):
    m.box((x, y, 0.05), (length, 0.02, 0.1) if along_x else (0.02, length, 0.1), "skirting")


def window(m, x, y, w, along_x, blinds=True):
    size = (w, 0.03, 1.3) if along_x else (0.03, w, 1.3)
    m.box((x, y, 1.75), size, tex_mat("blinds.png") if blinds else "outside")
    frame = (w + 0.08, 0.035, 0.05) if along_x else (0.035, w + 0.08, 0.05)
    for z in (1.08, 2.42):
        m.box((x, y, z), frame, "white")


# ------------------------------------------------------------------ the room
def build_room():
    T = WALL_T
    front = wall("wall_front_tv", HX + T / 2, 0, T, ROOM_Y + 2 * T)
    back = wall("wall_back_windows", -HX - T / 2, 0, T, ROOM_Y + 2 * T)
    right = wall("wall_right_pcs", 0, -HY - T / 2, ROOM_X, T)
    left = wall("wall_left_counter", 0, HY + T / 2, ROOM_X, T)

    # front wall: slats full width, TV, door
    slats(front, -T / 2 - 0.01, 0, ROOM_Y, False)
    front.box((-T / 2 - 0.04, 1.0, 1.75), (0.05, 1.95, 1.12), "black")
    front.box((-T / 2 - 0.066, 1.0, 1.75), (0.002, 1.89, 1.06), "screen")
    dy, dw = -2.95, 1.9
    front.box((-T / 2 - 0.03, dy, 1.2), (0.05, dw, 2.4), "frame_wood")
    for s in (-1, 1):
        for z, hh in ((1.65, 1.0), (0.6, 0.8)):
            front.box((-T / 2 - 0.06, dy + s * dw / 4, z), (0.01, dw / 2 - 0.25, hh), "glass", transparency=0.3)
        front.box((-T / 2 - 0.08, dy + s * 0.06, 1.1), (0.03, 0.02, 0.45), "frame_wood")

    # back wall: two windows, skirting
    skirting(back, T / 2 + 0.01, 0, ROOM_Y, False)
    window(back, T / 2 + 0.02, -1.4, 2.0, False, blinds=False)
    window(back, T / 2 + 0.02, 2.4, 2.0, False)

    # right wall: slats near door, AC units, switch board
    skirting(right, 0, T / 2 + 0.01, ROOM_X, True)
    slats(right, 5.0, T / 2 + 0.012, 3.0, True)
    for ax in (-1.5, 2.2):
        right.box((ax, T / 2 + 0.13, 2.75), (0.95, 0.25, 0.3), "white")
    right.box((5.2, T / 2 + 0.01, 1.3), (0.15, 0.02, 0.3), "white")

    # left wall: slats near TV corner, windows
    skirting(left, 0, -T / 2 - 0.01, ROOM_X, True)
    slats(left, 4.8, -T / 2 - 0.012, 3.4, True)
    window(left, 5.0, -T / 2 - 0.02, 1.8, True)
    window(left, -5.0, -T / 2 - 0.02, 1.6, True)

    # floor visual (collision is the ground plane, same as the original sim world)
    fl = new("floor_tiles")
    fl.box((0, 0, -0.005), (ROOM_X, ROOM_Y, 0.01), tex_mat("floor_tiles.png", ROOM_X / (4 * TILE), ROOM_Y / (4 * TILE)))


def build_pc_counter():
    m = new("pc_counter")
    x0, x1 = -3.0, 3.5
    front = counter(m, x0, x1, -HY, 0.65, 0.85, +1)
    for ax in (-1.0, 1.6):  # arched lattice panels
        m.box((ax, front + 0.003, 0.5), (0.4, 0.004, 0.55), tex_mat("lattice.png", 2, 3))
    for k in range(7):
        x = -2.6 + k * 0.85
        monitor(m, x, -HY + 0.3, 0.85, math.pi / 2, w=0.45, h=0.3)
        m.box((x + 0.35, -HY + 0.3, 0.85 + 0.19), (0.18, 0.38, 0.38), "black")
        m.box((x, -HY + 0.52, 0.86), (0.42, 0.14, 0.02), "darkgrey")
    # small robot arm on the counter
    ax, ay = 3.1, -HY + 0.3
    m.box((ax, ay, 0.9), (0.25, 0.25, 0.1), "black")
    m.cyl((ax, ay, 1.05), 0.05, 0.2, "darkgrey")
    m.box((ax + 0.1, ay, 1.17), (0.25, 0.05, 0.05), "darkgrey", rpy=(0, -0.4, 0))
    for k, x in enumerate((-2.2, -1.3, -0.3, 0.7, 1.7, 2.6)):
        stool("stool_pc_%d" % k, x, -HY + 1.05)


def build_shelf_unit():
    m = new("shelf_unit")
    x0, x1 = -HX + 0.1, -3.0
    counter(m, x0, x1, -HY, 0.55, 0.85, +1)
    d, y = 0.35, -HY + 0.175
    for vx in (x0, -5.35, -4.05, x1):
        m.box((vx, y, 1.8), (0.03, d, 1.9), tex_mat("wood_light.png", 1, 2))
    for zx0, zx1, levels in ((x0, -5.35, (1.35, 1.9, 2.3, 2.74)), (-4.05, x1, (1.35, 1.9, 2.3, 2.74)),
                             (-5.35, -4.05, (2.3, 2.74))):
        for z in levels:
            m.box(((zx0 + zx1) / 2, y, z), (zx1 - zx0, d, 0.03), tex_mat("wood_light.png", 2))
    m.box((-4.7, -HY + 0.02, 1.55), (1.25, 0.02, 1.35), "whiteboard")
    for px, pz in ((-6.0, 1.05), (-5.65, 1.55), (-6.05, 1.55), (-3.7, 1.05), (-3.35, 1.55), (-3.7, 1.55), (-5.85, 2.0)):
        m.box((px, -HY + 0.07, pz + 0.15), (0.24, 0.01, 0.3), "poster", rpy=(0.12, 0, 0))
    # VR kit and leaning board
    m.box((-4.7, -HY + 0.3, 0.92), (0.35, 0.18, 0.14), "green1")
    for s in (-1, 1):
        m.cyl((-4.7 + s * 0.35, -HY + 0.3, 0.95), 0.05, 0.12, "darkgrey")
    m.box((-4.3, -HY + 0.66, 0.55), (0.9, 0.02, 1.1), "white", rpy=(-0.12, 0, 0), collide=True)


def build_left_counter():
    m = new("left_counter")
    x0, x1 = -4.5, 3.6
    front = counter(m, x0, x1, HY, 0.65, 0.88, -1)
    for px in (-1.2, 1.8):  # pillars behind the counter
        m.box((px, HY - 0.22, ROOM_H / 2), (0.5, 0.44, ROOM_H), "wall")
    for ax in (-2.8, 0.3):
        m.box((ax, front - 0.003, 0.5), (0.4, 0.004, 0.55), tex_mat("lattice.png", 2, 3))
    for k in range(4):  # socket covers
        m.cyl((-3.5 + 2 * k, HY - 0.4, 0.885), 0.04, 0.01, "white")
    for k, x in enumerate((-3.9, -3.2, -2.5, -1.8, 0.6, 2.4)):
        stool("stool_left_%d" % k, x, HY - 1.05)
    # stack of coloured files near the TV corner
    files = new("file_stacks", 4.05, HY - 0.35)
    cols = ["orange", "blue", "red", "green2", (0.9, 0.2, 0.6, 1), (0.95, 0.8, 0.2, 1)]
    for s, dx in enumerate((-0.18, 0.18)):
        for k in range(30 + 6 * s):
            files.box((dx + random.uniform(-0.02, 0.02), 0, 0.02 + k * 0.025), (0.33, 0.25, 0.024),
                      random.choice(cols), rpy=(0, 0, random.uniform(-0.08, 0.08)))
    files.collision_only("<box><size>0.75 0.3 0.9</size></box>", (0, 0, 0.45))


def build_corner_desks():
    # blue student desk near TV corner
    m = new("blue_desk", 5.3, 3.0)
    m.box((0, 0, 0.36), (0.42, 1.2, 0.72), "white", collide=True)
    m.box((0, 0, 0.735), (0.47, 1.25, 0.03), "blue")
    office_chair("blue_desk_chair", 5.85, 3.0, math.pi, style="grey")
    for k, (x, y) in enumerate(((4.55, 2.4), (4.5, 3.05), (4.55, 3.7), (4.0, 2.75))):
        stool("stool_corner_%d" % k, x, y)
    # podium
    p = new("podium", 6.05, -0.9)
    p.box((0, 0, 0.01), (0.5, 0.5, 0.02), "black", collide=True)
    p.box((0, 0, 0.55), (0.22, 0.22, 1.05), "black", collide=True)
    p.box((0, 0, 1.1), (0.45, 0.6, 0.04), "black", rpy=(0, 0.25, 0))
    p.cyl((0.05, 0.15, 1.3), 0.006, 0.4, "darkgrey", rpy=(0, -0.4, 0))
    # fire extinguisher + dustbin by the door
    e = new("fire_extinguisher", 6.25, -4.25)
    e.cyl((0, 0, 0.27), 0.08, 0.5, "red", collide=True)
    e.cyl((0, 0, 0.55), 0.025, 0.08, "black")
    b = new("dustbin", 5.9, -4.3)
    b.cyl((0, 0, 0.2), 0.12, 0.4, "chrome", collide=True)


def build_faculty_desk():
    m = new("faculty_desk", -5.3, 2.65)
    w, L, h = 0.75, 1.8, 1.0
    m.box((0, 0, h / 2), (w, L, h), tex_mat("wood_light.png", 2), collide=True)
    m.box((w / 2 + 0.004, 0, 0.5), (0.004, L - 0.35, 0.5), tex_mat("lattice.png", 6, 2))
    for s in (-1, 1):
        m.box((0, s * (L / 2 + 0.004), 0.5), (w - 0.3, 0.004, 0.55), tex_mat("lattice.png", 2, 2))
    m.box((w / 2 - 0.01, 0, h + 0.16), (0.012, L, 0.3), "glass", transparency=0.4)
    for s in (-1, 1):
        m.box((0, s * (L / 2 - 0.01), h + 0.16), (w, 0.012, 0.3), "glass", transparency=0.4)
    m.box((-0.2, 0.3, h + 0.15), (0.25, 0.2, 0.3), "black")  # backpack
    monitor(m, -0.15, -0.4, h, 0.0)
    office_chair("faculty_chair", -6.05, 2.65, 0.0, style="grey")


def build_orange_mat():
    m = new("orange_mat", -5.45, -1.4)
    m.box((0, 0, 0.0025), (1.8, 5.0, 0.005), "orange", collide=True)


def build_conference_table():
    L, W = 6.2, 1.8
    cx = 0.1
    m = new("conference_table", cx, 0.0)
    straight = L - W
    m.box((0, 0, 0.74), (straight, W, 0.04), "white", collide=True)
    for s in (-1, 1):
        m.cyl((s * straight / 2, 0, 0.74), W / 2, 0.04, "white", collide=True)
    for k in range(1, 5):  # seams between table segments
        m.box((-straight / 2 + k * straight / 5, 0, 0.761), (0.01, W, 0.002), "grey")
    m.box((0, 0, 0.36), (L - 1.2, 0.9, 0.72), tex_mat("wood_light.png", 4), collide=True)
    # planter strip with plants
    m.box((0, 0, 0.9), (L - 2.2, 0.34, 0.28), "planter")
    for k in range(int((L - 2.2) / 0.07)):  # leafy clumps + a few tall fern/spider-plant leaves
        x = -(L - 2.2) / 2 + 0.05 + k * 0.07
        m.sphere((x, random.uniform(-0.12, 0.12), 1.06 + random.uniform(0, 0.1)), random.uniform(0.06, 0.1),
                 random.choice(["green1", "green2", "green3"]))
        if k % 3 == 0:
            m.box((x, random.uniform(-0.1, 0.1), 1.2), (0.02, 0.05, 0.3), random.choice(["green1", "green3"]),
                  rpy=(random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4), random.uniform(0, 3)))
    # monitors and chairs on both sides
    seats = [-2.3, -1.4, -0.5, 0.4, 1.3, 2.2]
    for side in (-1, 1):
        for k, x in enumerate(seats):
            monitor(m, x, side * 0.42, 0.76, side * math.pi / 2)
            office_chair("chair_%s_%d" % ("r" if side < 0 else "l", k), cx + x, side * 1.3, -side * math.pi / 2,
                         style="white" if k % 2 == 0 else "grey")
    office_chair("chair_end_tv", cx + L / 2 + 0.45, 0, math.pi)
    office_chair("chair_end_back", cx - L / 2 - 0.45, 0, 0.0, style="grey")


# ------------------------------------------------------------------ world file
WORLD_HEAD = """<?xml version='1.0'?>
<!-- AUTO-GENERATED by generate_lab_world.py - edit that script, not this file. -->
<sdf version='1.6'>
  <world name='mahadev_lab'>
    <!-- physics identical to svan_gazebo/worlds/simple_world.sdf so the robot behaves the same -->
    <physics type='ode'>
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>
    <gravity>0 0 -9.81</gravity>
    <scene>
      <ambient>0.55 0.55 0.55 1</ambient>
      <background>0.75 0.8 0.85 1</background>
      <shadows>true</shadows>
    </scene>
    <include><uri>model://sun</uri></include>
    <light name='ceiling_1' type='point'><pose>-3 0 3.0 0 0 0</pose><diffuse>0.35 0.35 0.33 1</diffuse>
      <attenuation><range>12</range><constant>0.6</constant><linear>0.05</linear><quadratic>0.005</quadratic></attenuation>
      <cast_shadows>false</cast_shadows></light>
    <light name='ceiling_2' type='point'><pose>3 0 3.0 0 0 0</pose><diffuse>0.35 0.35 0.33 1</diffuse>
      <attenuation><range>12</range><constant>0.6</constant><linear>0.05</linear><quadratic>0.005</quadratic></attenuation>
      <cast_shadows>false</cast_shadows></light>
    <model name='gplane'>
      <static>true</static>
      <link name='plane'>
        <collision name='plane'>
          <geometry><plane><normal>0 0 1</normal></plane></geometry>
          <surface><friction><ode><mu>100</mu><mu2>100</mu2></ode></friction></surface>
        </collision>
      </link>
    </model>
"""

WORLD_TAIL = """    <gui fullscreen='0'>
      <camera name='user_camera'>
        <pose>0 -9 13 0 0.96 1.5708</pose>
      </camera>
    </gui>
  </world>
</sdf>
"""


def main():
    make_textures()
    build_room()
    build_pc_counter()
    build_shelf_unit()
    build_left_counter()
    build_corner_desks()
    build_faculty_desk()
    build_orange_mat()
    build_conference_table()
    write_material_script()
    with open(WORLD_FILE, "w") as f:
        f.write(WORLD_HEAD)
        for m in MODELS:
            f.write("    " + m.sdf() + "\n")
        f.write(WORLD_TAIL)
    print("wrote %s (%d models), media in %s" % (WORLD_FILE, len(MODELS), MEDIA))


if __name__ == "__main__":
    main()
