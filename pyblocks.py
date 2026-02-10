import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pyglet
from pyglet.gl import (
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FLOAT,
    GL_LEQUAL,
    GL_LINES,
    GL_QUADS,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glDrawElements,
    glEnable,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTranslatef,
    glVertex2f,
    glVertex3f,
    glViewport,
    gluPerspective,
    glOrtho,
    glDepthFunc,
    GL_MODELVIEW,
    GL_PROJECTION,
)
from pyglet.window import key, mouse

# ===================== CONFIG =====================
TICKS_PER_SEC = 60
CHUNK_SIZE = 16
CHUNK_HEIGHT = 64
SEA_LEVEL = 16
RENDER_DISTANCE = 2  # raio em chunks
WORLD_SEED = 1337

WALK_SPEED = 4.8
RUN_SPEED = 7.2
CROUCH_SPEED = 2.6
GRAVITY = 22.0
JUMP_SPEED = 8.5
PLAYER_WIDTH = 0.35
PLAYER_HEIGHT = 1.8
CROUCH_HEIGHT = 1.4

# IDs de blocos
BLOCKS = {
    0: "Air",
    1: "Grass",
    2: "Dirt",
    3: "Stone",
    4: "Wood",
    5: "Leaves",
    6: "Sand",
    7: "Water",
    8: "Iron Ore",
    9: "Iron",
    10: "Diamond Ore",
    11: "Diamond",
    12: "Planks",
    13: "Crafting Table",
    14: "Furnace",
    15: "Bed",
    16: "Raw Meat",
    17: "Cooked Meat",
    18: "Wool",
    19: "Wooden Sword",
    20: "Stone Sword",
    21: "Iron Sword",
    22: "Wooden Pickaxe",
    23: "Stone Pickaxe",
    24: "Iron Pickaxe",
    25: "Wooden Axe",
    26: "Stone Axe",
    27: "Iron Axe",
    28: "Wooden Shovel",
    29: "Stone Shovel",
    30: "Iron Shovel",
}

AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
SAND = 6
WATER = 7
IRON_ORE = 8
IRON = 9
DIAMOND_ORE = 10
DIAMOND = 11
PLANKS = 12
CRAFTING_TABLE = 13

BLOCK_COLORS = {
    AIR: (0.0, 0.0, 0.0),
    GRASS: (0.34, 0.72, 0.28),
    DIRT: (0.52, 0.36, 0.23),
    STONE: (0.52, 0.52, 0.56),
    WOOD: (0.49, 0.31, 0.16),
    LEAVES: (0.20, 0.55, 0.20),
    SAND: (0.85, 0.80, 0.56),
    WATER: (0.16, 0.35, 0.8),
    IRON_ORE: (0.74, 0.62, 0.50),
    IRON: (0.84, 0.84, 0.84),
    DIAMOND_ORE: (0.0, 0.8, 0.8),
    DIAMOND: (0.35, 1.0, 1.0),
    PLANKS: (0.67, 0.50, 0.29),
    CRAFTING_TABLE: (0.64, 0.45, 0.20),
    14: (0.25, 0.25, 0.25),
    15: (0.72, 0.18, 0.18),
    16: (0.80, 0.23, 0.23),
    17: (0.60, 0.28, 0.12),
    18: (0.94, 0.94, 0.94),
    19: (0.56, 0.44, 0.30),
    20: (0.48, 0.48, 0.48),
    21: (0.74, 0.74, 0.74),
    22: (0.56, 0.44, 0.30),
    23: (0.48, 0.48, 0.48),
    24: (0.74, 0.74, 0.74),
    25: (0.56, 0.44, 0.30),
    26: (0.48, 0.48, 0.48),
    27: (0.74, 0.74, 0.74),
    28: (0.56, 0.44, 0.30),
    29: (0.48, 0.48, 0.48),
    30: (0.74, 0.74, 0.74),
}

FACES = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]

SHADE = [1.00, 0.58, 0.78, 0.78, 0.9, 0.9]


def floor_pos(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    return int(math.floor(position[0])), int(math.floor(position[1])), int(math.floor(position[2]))


def world_to_chunk(x: int, z: int) -> Tuple[int, int]:
    return math.floor(x / CHUNK_SIZE), math.floor(z / CHUNK_SIZE)


def local_coord(value: int) -> int:
    return value % CHUNK_SIZE


def hash2(x: int, z: int, seed: int) -> float:
    n = (x * 1836311903) ^ (z * 2971215073) ^ (seed * 4807526976)
    n = (n << 13) ^ n
    h = (n * (n * n * 15731 + 789221) + 1376312589) & 0x7FFFFFFF
    return 1.0 - h / 1073741824.0


def smooth_noise(x: float, z: float, seed: int) -> float:
    xi = math.floor(x)
    zi = math.floor(z)
    xf = x - xi
    zf = z - zi

    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    n00 = hash2(xi, zi, seed)
    n10 = hash2(xi + 1, zi, seed)
    n01 = hash2(xi, zi + 1, seed)
    n11 = hash2(xi + 1, zi + 1, seed)
    u = xf * xf * (3 - 2 * xf)
    v = zf * zf * (3 - 2 * zf)
    return lerp(lerp(n00, n10, u), lerp(n01, n11, u), v)


def fbm(x: float, z: float, seed: int, octaves: int = 4) -> float:
    freq = 0.02
    amp = 1.0
    value = 0.0
    norm = 0.0
    for i in range(octaves):
        value += smooth_noise(x * freq, z * freq, seed + 101 * i) * amp
        norm += amp
        freq *= 2.0
        amp *= 0.5
    return value / max(norm, 1e-6)


@dataclass
class Recipe:
    result: Tuple[int, int]
    requires: Dict[int, int]


RECIPES_2x2 = [
    Recipe((PLANKS, 4), {WOOD: 1}),
    Recipe((CRAFTING_TABLE, 1), {PLANKS: 4}),
]

RECIPES_3x3 = [
    Recipe((IRON, 1), {IRON_ORE: 1}),
    Recipe((DIAMOND, 1), {DIAMOND_ORE: 1}),
    Recipe((22, 1), {PLANKS: 2, STONE: 1}),
]


class Chunk:
    def __init__(self, cx: int, cz: int):
        self.cx = cx
        self.cz = cz
        self.blocks: Dict[Tuple[int, int, int], int] = {}
        self.vertex_list = None


class World:
    def __init__(self, seed: int, batch: pyglet.graphics.Batch):
        self.seed = seed
        self.batch = batch
        self.chunks: Dict[Tuple[int, int], Chunk] = {}

    def get_block(self, pos: Tuple[int, int, int]) -> int:
        x, y, z = pos
        if y < 0 or y >= CHUNK_HEIGHT:
            return AIR
        ckey = world_to_chunk(x, z)
        chunk = self.chunks.get(ckey)
        if not chunk:
            return AIR
        return chunk.blocks.get((local_coord(x), y, local_coord(z)), AIR)

    def set_block(self, pos: Tuple[int, int, int], block_id: int):
        x, y, z = pos
        if y < 0 or y >= CHUNK_HEIGHT:
            return
        ckey = world_to_chunk(x, z)
        chunk = self.chunks.get(ckey)
        if not chunk:
            return
        lpos = (local_coord(x), y, local_coord(z))
        if block_id == AIR:
            chunk.blocks.pop(lpos, None)
        else:
            chunk.blocks[lpos] = block_id
        self.rebuild_chunk_and_neighbors(ckey, x, z)

    def rebuild_chunk_and_neighbors(self, ckey: Tuple[int, int], x: int, z: int):
        self.rebuild_chunk(ckey)
        lx = local_coord(x)
        lz = local_coord(z)
        if lx == 0:
            self.rebuild_chunk((ckey[0] - 1, ckey[1]))
        if lx == CHUNK_SIZE - 1:
            self.rebuild_chunk((ckey[0] + 1, ckey[1]))
        if lz == 0:
            self.rebuild_chunk((ckey[0], ckey[1] - 1))
        if lz == CHUNK_SIZE - 1:
            self.rebuild_chunk((ckey[0], ckey[1] + 1))

    def generate_chunk(self, cx: int, cz: int) -> Chunk:
        chunk = Chunk(cx, cz)
        wx0 = cx * CHUNK_SIZE
        wz0 = cz * CHUNK_SIZE
        for lx in range(CHUNK_SIZE):
            for lz in range(CHUNK_SIZE):
                wx = wx0 + lx
                wz = wz0 + lz
                n = fbm(wx, wz, self.seed)
                m = fbm(wx + 1200, wz - 700, self.seed + 17)
                height = int(SEA_LEVEL + n * 8 + m * 4)
                height = max(4, min(CHUNK_HEIGHT - 2, height))

                for y in range(height + 1):
                    block = STONE
                    if y == height:
                        if height <= SEA_LEVEL:
                            block = SAND
                        else:
                            block = GRASS
                    elif y >= height - 2:
                        block = DIRT
                    if y < height - 5 and hash2(wx + y, wz - y, self.seed) > 0.82:
                        block = IRON_ORE
                    if y < height - 12 and hash2(wx - y, wz + y, self.seed + 9) > 0.90:
                        block = DIAMOND_ORE
                    chunk.blocks[(lx, y, lz)] = block

                if height <= SEA_LEVEL:
                    for y in range(height + 1, SEA_LEVEL + 1):
                        chunk.blocks[(lx, y, lz)] = WATER
                else:
                    tree_noise = hash2(wx, wz, self.seed + 999)
                    if tree_noise > 0.90:
                        self._add_tree(chunk, lx, height + 1, lz)
        return chunk

    def _add_tree(self, chunk: Chunk, lx: int, y: int, lz: int):
        if y + 5 >= CHUNK_HEIGHT:
            return
        for ty in range(y, y + 4):
            chunk.blocks[(lx, ty, lz)] = WOOD
        for ox in range(-2, 3):
            for oz in range(-2, 3):
                for oy in range(3, 6):
                    tx = lx + ox
                    tz = lz + oz
                    ty = y + oy
                    if 0 <= tx < CHUNK_SIZE and 0 <= tz < CHUNK_SIZE and ty < CHUNK_HEIGHT:
                        if abs(ox) + abs(oz) <= 3:
                            chunk.blocks[(tx, ty, tz)] = LEAVES

    def load_chunk(self, cx: int, cz: int):
        key = (cx, cz)
        if key in self.chunks:
            return
        chunk = self.generate_chunk(cx, cz)
        self.chunks[key] = chunk
        self.rebuild_chunk(key)

    def unload_chunk(self, key: Tuple[int, int]):
        chunk = self.chunks.pop(key, None)
        if chunk and chunk.vertex_list is not None:
            chunk.vertex_list.delete()

    def rebuild_chunk(self, key: Tuple[int, int]):
        chunk = self.chunks.get(key)
        if not chunk:
            return
        if chunk.vertex_list is not None:
            chunk.vertex_list.delete()
            chunk.vertex_list = None

        vertices: List[float] = []
        colors: List[float] = []
        indices: List[int] = []
        offset = 0

        for (lx, y, lz), block in chunk.blocks.items():
            if block == AIR:
                continue
            wx = chunk.cx * CHUNK_SIZE + lx
            wz = chunk.cz * CHUNK_SIZE + lz
            base_color = BLOCK_COLORS.get(block, (1.0, 1.0, 1.0))

            for face_idx, (dx, dy, dz) in enumerate(FACES):
                if self.get_block((wx + dx, y + dy, wz + dz)) != AIR and not (
                    block == WATER and self.get_block((wx + dx, y + dy, wz + dz)) == WATER
                ):
                    continue
                face = cube_face_vertices(wx, y, wz, face_idx)
                shade = SHADE[face_idx]
                vertices.extend(face)
                colors.extend([base_color[0] * shade, base_color[1] * shade, base_color[2] * shade] * 4)
                indices.extend([offset, offset + 1, offset + 2, offset, offset + 2, offset + 3])
                offset += 4

        if not indices:
            return
        chunk.vertex_list = self.batch.add_indexed(
            offset,
            GL_TRIANGLES,
            None,
            indices,
            ("v3f/static", vertices),
            ("c3f/static", colors),
        )


def cube_face_vertices(x: int, y: int, z: int, face_idx: int) -> List[float]:
    x0, x1 = x, x + 1
    y0, y1 = y, y + 1
    z0, z1 = z, z + 1
    if face_idx == 0:  # top
        return [x0, y1, z0, x0, y1, z1, x1, y1, z1, x1, y1, z0]
    if face_idx == 1:  # bottom
        return [x0, y0, z0, x1, y0, z0, x1, y0, z1, x0, y0, z1]
    if face_idx == 2:  # left
        return [x0, y0, z0, x0, y0, z1, x0, y1, z1, x0, y1, z0]
    if face_idx == 3:  # right
        return [x1, y0, z1, x1, y0, z0, x1, y1, z0, x1, y1, z1]
    if face_idx == 4:  # front
        return [x0, y0, z1, x1, y0, z1, x1, y1, z1, x0, y1, z1]
    return [x1, y0, z0, x0, y0, z0, x0, y1, z0, x1, y1, z0]


class GameWindow(pyglet.window.Window):
    def __init__(self):
        config = pyglet.gl.Config(major_version=2, minor_version=1, depth_size=24, double_buffer=True)
        super().__init__(1280, 720, "PyBlocks - Voxel", resizable=True, config=config)
        self.set_minimum_size(960, 540)

        self.batch = pyglet.graphics.Batch()
        self.world = World(WORLD_SEED, self.batch)

        self.pos = [0.0, 26.0, 0.0]
        self.rot = [0.0, 0.0]
        self.vel_y = 0.0
        self.grounded = False
        self.exclusive = False
        self.render_distance = RENDER_DISTANCE

        self.move = {"w": False, "a": False, "s": False, "d": False, "run": False, "crouch": False}
        self.crouching = False
        self.hotbar = [GRASS, DIRT, STONE, WOOD, PLANKS, CRAFTING_TABLE, 14, SAND, LEAVES]
        self.selected = 0
        self.inventory: Dict[int, int] = {bid: 0 for bid in BLOCKS.keys() if bid != AIR}
        self.inventory[GRASS] = 32
        self.inventory[DIRT] = 32
        self.inventory[STONE] = 32
        self.inventory[WOOD] = 16
        self.inventory[CRAFTING_TABLE] = 1

        self.ui_mode: Optional[str] = None  # None|inv|table
        self.grid2: List[int] = [AIR] * 4
        self.grid3: List[int] = [AIR] * 9
        self.grid_cursor = 0
        self.grid_pick = WOOD

        self.debug = pyglet.text.Label("", x=12, y=self.height - 12, anchor_x="left", anchor_y="top", color=(255, 255, 255, 255))
        self.ui_label = pyglet.text.Label("", x=12, y=140, anchor_x="left", anchor_y="bottom", color=(255, 255, 255, 255), multiline=True, width=640)

        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        self.last_chunk = None
        self.update_visible_chunks(force=True)

        glClearColor(0.53, 0.74, 0.95, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glDepthFunc(GL_LEQUAL)

    def get_sight_vector(self) -> Tuple[float, float, float]:
        rx, ry = self.rot
        m = math.cos(math.radians(ry))
        return (
            math.cos(math.radians(rx - 90.0)) * m,
            math.sin(math.radians(ry)),
            math.sin(math.radians(rx - 90.0)) * m,
        )

    def get_motion_vector(self) -> Tuple[float, float, float]:
        fw = float(self.move["w"]) - float(self.move["s"])
        sd = float(self.move["d"]) - float(self.move["a"])
        if fw == 0 and sd == 0:
            return 0.0, 0.0, 0.0

        yaw = math.radians(self.rot[0])
        fx, fz = math.cos(yaw), math.sin(yaw)
        rx, rz = math.cos(yaw + math.pi / 2), math.sin(yaw + math.pi / 2)
        dx = fx * fw + rx * sd
        dz = fz * fw + rz * sd
        l = math.sqrt(dx * dx + dz * dz)
        return dx / l, 0.0, dz / l

    def update_visible_chunks(self, force: bool = False):
        pchunk = world_to_chunk(int(math.floor(self.pos[0])), int(math.floor(self.pos[2])))
        if not force and pchunk == self.last_chunk:
            return
        self.last_chunk = pchunk
        needed = set()
        for dx in range(-self.render_distance, self.render_distance + 1):
            for dz in range(-self.render_distance, self.render_distance + 1):
                if dx * dx + dz * dz <= self.render_distance * self.render_distance:
                    needed.add((pchunk[0] + dx, pchunk[1] + dz))

        loaded = set(self.world.chunks.keys())
        for c in sorted(needed - loaded):
            self.world.load_chunk(*c)
        for c in loaded - needed:
            self.world.unload_chunk(c)

    def hit_test(self, max_distance=8.0):
        ox, oy, oz = self.pos
        dx, dy, dz = self.get_sight_vector()
        px = py = pz = None
        step = 0.1
        t = 0.0
        while t <= max_distance:
            x = int(math.floor(ox + dx * t))
            y = int(math.floor(oy + dy * t))
            z = int(math.floor(oz + dz * t))
            if (x, y, z) != (px, py, pz):
                block = self.world.get_block((x, y, z))
                if block != AIR and block != WATER:
                    return (x, y, z), (px, py, pz)
                px, py, pz = x, y, z
            t += step
        return None, None

    def on_mouse_press(self, x, y, button, modifiers):
        if self.ui_mode:
            return
        if not self.exclusive:
            self.set_exclusive_mouse(True)
            self.exclusive = True
            return
        target, neighbor = self.hit_test()
        if button == mouse.LEFT and target:
            bid = self.world.get_block(target)
            self.world.set_block(target, AIR)
            if bid != AIR:
                self.inventory[bid] = self.inventory.get(bid, 0) + 1
        if button == mouse.RIGHT and neighbor:
            block = self.hotbar[self.selected]
            if self.inventory.get(block, 0) > 0:
                self.world.set_block(neighbor, block)
                self.inventory[block] -= 1

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.exclusive or self.ui_mode:
            return
        sensitivity = 0.15
        self.rot[0] = (self.rot[0] + dx * sensitivity) % 360
        self.rot[1] = max(-89.9, min(89.9, self.rot[1] + dy * sensitivity))

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
            self.exclusive = False
            self.ui_mode = None
        elif symbol == key.W:
            self.move["w"] = True
        elif symbol == key.A:
            self.move["a"] = True
        elif symbol == key.S:
            self.move["s"] = True
        elif symbol == key.D:
            self.move["d"] = True
        elif symbol == key.LSHIFT:
            self.move["run"] = True
        elif symbol == key.LCTRL:
            self.move["crouch"] = True
        elif symbol == key.SPACE and self.grounded and not self.ui_mode:
            self.vel_y = JUMP_SPEED
            self.grounded = False
        elif symbol == key.I:
            self.ui_mode = None if self.ui_mode == "inv" else "inv"
            self.set_exclusive_mouse(False)
            self.exclusive = False
        elif symbol == key.E:
            self.ui_mode = None if self.ui_mode == "table" else "table"
            self.set_exclusive_mouse(False)
            self.exclusive = False
        elif symbol == key.LEFT:
            self.grid_cursor = (self.grid_cursor - 1) % (4 if self.ui_mode == "inv" else 9)
        elif symbol == key.RIGHT:
            self.grid_cursor = (self.grid_cursor + 1) % (4 if self.ui_mode == "inv" else 9)
        elif symbol == key.UP:
            self.grid_pick = max(1, self.grid_pick - 1)
        elif symbol == key.DOWN:
            self.grid_pick = min(30, self.grid_pick + 1)
        elif symbol == key.ENTER and self.ui_mode:
            self.apply_craft()
        elif symbol == key.BACKSPACE and self.ui_mode:
            if self.ui_mode == "inv":
                self.grid2[self.grid_cursor] = AIR
            else:
                self.grid3[self.grid_cursor] = AIR
        elif symbol == key.P and self.ui_mode:
            if self.inventory.get(self.grid_pick, 0) > 0:
                if self.ui_mode == "inv":
                    self.grid2[self.grid_cursor] = self.grid_pick
                else:
                    self.grid3[self.grid_cursor] = self.grid_pick
        elif key._1 <= symbol <= key._9:
            self.selected = symbol - key._1

    def on_key_release(self, symbol, modifiers):
        if symbol == key.W:
            self.move["w"] = False
        elif symbol == key.A:
            self.move["a"] = False
        elif symbol == key.S:
            self.move["s"] = False
        elif symbol == key.D:
            self.move["d"] = False
        elif symbol == key.LSHIFT:
            self.move["run"] = False
        elif symbol == key.LCTRL:
            self.move["crouch"] = False

    def apply_craft(self):
        grid = self.grid2 if self.ui_mode == "inv" else self.grid3
        recipes = RECIPES_2x2 if self.ui_mode == "inv" else RECIPES_3x3
        contents: Dict[int, int] = {}
        for b in grid:
            if b != AIR:
                contents[b] = contents.get(b, 0) + 1
        for recipe in recipes:
            ok = True
            for bid, qty in recipe.requires.items():
                if contents.get(bid, 0) < qty:
                    ok = False
                    break
                if self.inventory.get(bid, 0) < qty:
                    ok = False
                    break
            if not ok:
                continue
            for bid, qty in recipe.requires.items():
                self.inventory[bid] -= qty
            out, qty = recipe.result
            self.inventory[out] = self.inventory.get(out, 0) + qty
            for i in range(len(grid)):
                grid[i] = AIR
            return

    def collide(self, next_pos: List[float], h: float) -> List[float]:
        px, py, pz = next_pos

        def solid(x: int, y: int, z: int) -> bool:
            b = self.world.get_block((x, y, z))
            return b != AIR and b != WATER

        for axis in range(3):
            p = [px, py, pz]
            minx, maxx = p[0] - PLAYER_WIDTH, p[0] + PLAYER_WIDTH
            minz, maxz = p[2] - PLAYER_WIDTH, p[2] + PLAYER_WIDTH
            miny, maxy = p[1], p[1] + h

            xs = range(math.floor(minx), math.floor(maxx) + 1)
            ys = range(math.floor(miny), math.floor(maxy) + 1)
            zs = range(math.floor(minz), math.floor(maxz) + 1)
            collided = False
            for bx in xs:
                for by in ys:
                    for bz in zs:
                        if solid(bx, by, bz):
                            collided = True
                            break
                    if collided:
                        break
                if collided:
                    break

            if not collided:
                continue

            if axis == 1:
                if self.vel_y < 0:
                    py = math.floor(py) + 0.001
                    self.grounded = True
                else:
                    py = math.ceil(py) - h - 0.001
                self.vel_y = 0.0
            elif axis == 0:
                px = self.pos[0]
            else:
                pz = self.pos[2]

        return [px, py, pz]

    def update(self, dt: float):
        dt = min(0.04, dt)
        self.crouching = self.move["crouch"]
        speed = RUN_SPEED if self.move["run"] else WALK_SPEED
        if self.crouching:
            speed = CROUCH_SPEED

        mx, _, mz = self.get_motion_vector()
        nx = self.pos[0] + mx * speed * dt
        nz = self.pos[2] + mz * speed * dt

        self.vel_y -= GRAVITY * dt
        ny = self.pos[1] + self.vel_y * dt

        self.grounded = False
        next_pos = [nx, ny, nz]
        new_h = CROUCH_HEIGHT if self.crouching else PLAYER_HEIGHT
        self.pos = self.collide(next_pos, new_h)

        if self.pos[1] < -20:
            self.pos = [0.0, 30.0, 0.0]
            self.vel_y = 0.0

        self.update_visible_chunks()

    def draw_crosshair(self):
        w, h = self.get_size()
        cx, cy = w // 2, h // 2
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(cx - 8, cy)
        glVertex2f(cx + 8, cy)
        glVertex2f(cx, cy - 8)
        glVertex2f(cx, cy + 8)
        glEnd()

    def set_3d(self):
        w, h = self.get_size()
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, w, max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70.0, w / max(1.0, float(h)), 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(self.rot[1], math.cos(math.radians(self.rot[0])), 0, math.sin(math.radians(self.rot[0])))
        glRotatef(self.rot[0], 0, -1, 0)
        glTranslatef(-self.pos[0], -(self.pos[1] + (CROUCH_HEIGHT - 0.2 if self.crouching else PLAYER_HEIGHT - 0.2)), -self.pos[2])

    def set_2d(self):
        w, h = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def on_draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_3d()
        self.batch.draw()

        self.set_2d()
        self.draw_crosshair()

        chunk = world_to_chunk(int(math.floor(self.pos[0])), int(math.floor(self.pos[2])))
        self.debug.y = self.height - 12
        self.debug.text = (
            f"FPS: {pyglet.clock.get_fps():.1f} | Pos: ({self.pos[0]:.1f}, {self.pos[1]:.1f}, {self.pos[2]:.1f}) "
            f"| Chunk: {chunk} | Loaded chunks: {len(self.world.chunks)} | Render distance: {self.render_distance}"
        )
        self.debug.draw()

        sel = self.hotbar[self.selected]
        inv_count = self.inventory.get(sel, 0)
        info = pyglet.text.Label(
            f"Selecionado [{self.selected + 1}]: {BLOCKS[sel]} x{inv_count} | I: Craft 2x2 | E: Craft 3x3 | ENTER: craft",
            x=12,
            y=12,
            anchor_x="left",
            anchor_y="bottom",
            color=(255, 255, 255, 255),
        )
        info.draw()

        if self.ui_mode:
            grid = self.grid2 if self.ui_mode == "inv" else self.grid3
            side = 2 if self.ui_mode == "inv" else 3
            lines = [f"{self.ui_mode.upper()} CRAFTING ({side}x{side})"]
            for r in range(side):
                row = []
                for c in range(side):
                    idx = r * side + c
                    bid = grid[idx]
                    marker = "*" if idx == self.grid_cursor else " "
                    row.append(f"{marker}[{idx + 1}:{BLOCKS.get(bid, 'Air')}]")
                lines.append(" ".join(row))
            lines.append(f"Pick atual: {self.grid_pick} {BLOCKS[self.grid_pick]} (UP/DOWN)")
            lines.append("P: colocar item no slot | BACKSPACE: limpar slot | ENTER: craft")
            self.ui_label.text = "\n".join(lines)
            self.ui_label.draw()


def main():
    window = GameWindow()
    pyglet.app.run()


if __name__ == "__main__":
    main()
