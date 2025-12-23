#PYBLOCKS Source Code 0.6.1 - TestForPreAlpha Edition

import sys
import math
import random
import time
from collections import deque

import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *
from OpenGL.GL import *
from OpenGL.GLU import *


# ================= CONFIGURAÇÕES =================
TICKS_PER_SEC = 60
SECTOR_SIZE = 16  # Tamanho do Chunk (16x16)
WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
PLAYER_HEIGHT = 2

# IDs dos Blocos
AIR = 0
GRASS = 1
DIRT = 2
STONE = 3
WOOD = 4
LEAVES = 5
DIAMOND_ORE = 6
CRAFTING_TABLE = 7
FURNACE = 8
PLANKS = 9

# Mapeamento de texturas
BLOCK_COLORS = {
    GRASS: (0.5, 0.8, 0.5), # Verde
    DIRT: (0.55, 0.27, 0.07), # Marrom
    STONE: (0.5, 0.5, 0.5), # Cinza
    WOOD: (0.4, 0.2, 0.0), # Madeira escura
    LEAVES: (0.0, 0.6, 0.0), # Verde escuro
    DIAMOND_ORE: (0.0, 0.8, 0.8), # Ciano
    CRAFTING_TABLE: (0.8, 0.6, 0.4),
    FURNACE: (0.2, 0.2, 0.2),
    PLANKS: (0.7, 0.5, 0.3)
}

FACES = [
    ( 0, 1, 0), ( 0,-1, 0), ( -1, 0, 0), ( 1, 0, 0), ( 0, 0, 1), ( 0, 0, -1),
]

def cube_vertices(x, y, z, n):
    """ Retorna vértices do cubo com escala n """
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

def normalize(position):
    """ Arredonda posição para coordenadas de bloco """
    x, y, z = position
    x, y, z = int(round(x)), int(round(y)), int(round(z))
    return (x, y, z)

def sectorize(position):
    """ Retorna a tupla do chunk (x, z) baseado na posição """
    x, y, z = normalize(position)
    x, z = x // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class Model:
    def __init__(self, seed_val=None):
        self.batch = pyglet.graphics.Batch()
        self.group = pyglet.graphics.Group()
        self.world = {}  # Mapa: (x,y,z) -> block_type
        self.shown = {}  # Mapa: (x,y,z) -> vertex_list
        self._shown = {} # Mapa: (x,y,z) -> vertex_list (chunks)
        self.sectors = {} # Mapa: (sx, sz) -> lista de coords (x,y,z)
        self.queue = deque()
        
        # Configuração do Mundo
        self.seed = seed_val if seed_val else random.randint(0, 10000)
        random.seed(self.seed)
        
        self.initialize()

    def initialize(self):
        # Geração inicial (plataforma + noise simples)
        n = 80 # Tamanho inicial
        s = 1  # Step
        y = 0 
        
        # Noise generation simplificado
        for x in range(-n, n + 1, s):
            for z in range(-n, n + 1, s):
                # Simplex noise "fake" usando sin/cos para performance sem lib externa
                h = int(5 * (math.sin(x/10) + math.cos(z/10))) 
                
                # Base
                self.add_block((x, h - 2, z), STONE, immediate=False)
                self.add_block((x, h - 1, z), DIRT, immediate=False)
                self.add_block((x, h, z), GRASS, immediate=False)
                
                # Paredes para evitar cair no void no inicio
                if x in (-n, n) or z in (-n, n):
                    for dy in range(1, 3):
                        self.add_block((x, h+dy, z), STONE, immediate=False)
                
                # Minérios Raros
                if random.random() < 0.01:
                    self.add_block((x, h-3, z), DIAMOND_ORE, immediate=False)


    def exposed(self, position):
        """ Retorna True se a face do bloco está visível """
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False

    def add_block(self, position, block_type, immediate=True):
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)

    def remove_block(self, position, immediate=True):
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)

    def check_neighbors(self, position):
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)

    def show_block(self, position):
        block_type = self.world[position]
        color = BLOCK_COLORS.get(block_type, (1,1,1))
        
        # Cores para cada face (simulando luz simples)
        top = color
        bottom = [max(0, c - 0.2) for c in color]
        side = [max(0, c - 0.1) for c in color]
        
        vertex_data = cube_vertices(*position, 0.5)
        
        # Simples array de cores (R,G,B) * 4 vértices * 6 faces
        color_data = []
        color_data.extend(top * 4) # Top
        color_data.extend(bottom * 4) # Bottom
        color_data.extend(side * 4 * 4) # Lados

        # Adiciona ao Batch do Pyglet
        self.shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('c3f/static', color_data))

    def hide_block(self, position):
        self.shown.pop(position).delete()

    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

class Window(pyglet.window.Window):
    def init_gl(self):
        glClearColor(0.5, 0.69, 1.0, 1)
        glEnable(GL_CULL_FACE)
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.exclusive = False
        self.flying = False
        self.strafe = [0, 0]
        self.position = (0, 10, 0)
        self.rotation = (0, 0)
        self.sector = None
        self.reticle = None
        self.dy = 0
        self.inventory = {WOOD: 0, STONE: 0, DIRT: 0, DIAMOND_ORE: 0, PLANKS: 0}
        self.block_cursor = STONE
        self.mode = 'creative' # creative, exploration
        self.health = 20
        self.credits_shown = False
        
        # Mobs simples (apenas posições)
        self.mobs = [{'pos': [5, 5, 5], 'type': 'cow'}]
        
        self.model = Model()
        
        # Label setup
        self.label = pyglet.text.Label('', font_name='Arial', font_size=10, 
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top', color=(0,0,0,255))
        
        self.credits_label = pyglet.text.Label('', font_name='Arial', font_size=16,
            x=self.width//2, y=self.height//2, anchor_x='center', anchor_y='center', 
            multiline=True, width=400, color=(255, 255, 255, 255))

        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        pyglet.clock.schedule_interval(self.update_mobs, 1.0) # Mobs lentos

    def set_exclusive_mouse(self, exclusive):
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive

    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
            return (dx, dy, dz)
        return (0.0, 0.0, 0.0)

    def update(self, dt):
        if self.credits_shown: return

        self.model.queue = deque() # Limpa queue antiga
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.batch = pyglet.graphics.Batch() # Refresh batch no chunk change (simples)
            self.model.initialize() # Re-renderiza área próxima
            self.sector = sector

        m = 8
        dt = min(dt, 0.2)
        for _ in range(m):
            self._update(dt / m)

    def _update(self, dt):
        # Walk logic
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        
        # Gravity
        if not self.flying:
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -50) # Terminal velocity
            dy += self.dy * dt

        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)

        # Fall damage logic (Simplificado: se dy parou abruptamente e estava rápido)
        if not self.flying and self.mode == 'exploration':
            if y < -100: # Void
                self.respawn()

    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in FACES:  # check all surrounding blocks
            for i in range(3):  # check each dimension independently
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in range(height):  # check each height
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face[1]:
                        self.dy = 0
                    break
        return tuple(p)

    def update_mobs(self, dt):
        # AI BÁSICA: Mobs andam aleatoriamente
        for mob in self.mobs:
            dx = random.choice([-1, 0, 1])
            dz = random.choice([-1, 0, 1])
            bx, by, bz = mob['pos']
            if (bx+dx, by, bz+dz) not in self.model.world: # Só anda se não tiver parede
                mob['pos'][0] += dx * 0.2
                mob['pos'][2] += dz * 0.2

    def on_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            if (button == mouse.RIGHT) or \
                ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                if previous:
                    self.model.add_block(previous, self.block_cursor)
                    # Gasta item se exploração
            elif button == mouse.LEFT and block:
                texture = self.model.world[block]
                if texture != AIR:
                    self.model.remove_block(block)
                    # Drop Logic
                    if self.mode == 'exploration':
                        if texture == DIAMOND_ORE:
                            self.trigger_win()
                        else:
                            self.inventory[texture] = self.inventory.get(texture, 0) + 1
        else:
            self.set_exclusive_mouse(True)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.W: self.strafe[0] -= 1
        elif symbol == key.S: self.strafe[0] += 1
        elif symbol == key.A: self.strafe[1] -= 1
        elif symbol == key.D: self.strafe[1] += 1
        elif symbol == key.SPACE:
            if self.dy == 0: self.dy = JUMP_SPEED
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol == key._1: self.block_cursor = STONE
        elif symbol == key._2: self.block_cursor = DIRT
        elif symbol == key._3: self.block_cursor = GRASS
        elif symbol == key._4: self.block_cursor = WOOD
        elif symbol == key._5: self.block_cursor = PLANKS
        elif symbol == key._6: self.block_cursor = CRAFTING_TABLE
        elif symbol == key._7: self.block_cursor = FURNACE
        
        # Comandos Simples (Teclas de atalho para demonstração)
        elif symbol == key.C: # Crafting simples (Madeira -> Planks)
            if self.inventory.get(WOOD, 0) >= 1:
                self.inventory[WOOD] -= 1
                self.inventory[PLANKS] = self.inventory.get(PLANKS, 0) + 4
                print("Craftado: 4 Planks")
        
        elif symbol == key.G: # Toggle Game Mode
            self.mode = 'creative' if self.mode == 'exploration' else 'exploration'
            self.flying = True if self.mode == 'creative' else False
            print(f"Gamemode: {self.mode}")

    def on_key_release(self, symbol, modifiers):
        if symbol == key.W: self.strafe[0] += 1
        elif symbol == key.S: self.strafe[0] -= 1
        elif symbol == key.A: self.strafe[1] += 1
        elif symbol == key.D: self.strafe[1] -= 1

    def on_resize(self, width, height):
        self.label.y = height - 10
        
        x, y = width // 2, height // 2
        n = 10
        # CORREÇÃO v0.3: Removido o argumento 'width' do construtor
        self.reticle = [
            pyglet.shapes.Line(x - n, y, x + n, y, color=(0, 0, 0, 255)),
            pyglet.shapes.Line(x, y - n, x, y + n, color=(0, 0, 0, 255))
        ]
        # Ajusta a largura manualmente após criar (funciona na maioria das versões)
        self.reticle[0].width = 2
        self.reticle[1].width = 2
        
    def set_2d(self):
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_3d(self):
        # Garantir que a altura não seja zero pra evitar divisão por zero
        width, height = self.get_size()
        if height == 0:
            height = 1

        # --- CORREÇÃO CRÍTICA v0.4: Desativa shaders do Pyglet para permitir OpenGL Legacy ---
        try:
            glUseProgram(0)
        except:
            pass
        # --------------------------------------------------------------------------------

        # Ativa profundidade
        glEnable(GL_DEPTH_TEST)
        glViewport(0, 0, width, height)

        # Configuração da projeção
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65.0, width / float(height), 0.1, 60.0)

        # Configuração da modelview
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Rotação da câmera
        x_rot, y_rot = self.rotation
        glRotatef(x_rot, 0, 1, 0)
        glRotatef(-y_rot, math.cos(math.radians(x_rot)), 0, math.sin(math.radians(x_rot)))

        # Translação da câmera
        x_pos, y_pos, z_pos = self.position
        glTranslatef(-x_pos, -y_pos, -z_pos)

    def on_draw(self):
        if not hasattr(self, '_gl_initialized'):
            self.init_gl()
            self._gl_initialized = True

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # limpa cor + profundidade

        # --- Desenho 3D ---
        self.set_3d()
        glColor3f(1, 1, 1)
        self.model.batch.draw()
    
        for mob in self.mobs:
            glPushMatrix()
            glTranslatef(mob['pos'][0], mob['pos'][1], mob['pos'][2])
            glBegin(GL_QUADS)
            glColor3f(1, 0.8, 0.6)
            
            # --- CORREÇÃO v0.6: Iterar a lista plana de vértices de 3 em 3 ---
            verts = cube_vertices(0, 0, 0, 0.4)
            for i in range(0, len(verts), 3):
                glVertex3f(verts[i], verts[i+1], verts[i+2])
            # -----------------------------------------------------------
            
            glEnd()
            glPopMatrix()

        # --- Interface 2D ---
        self.set_2d()
        if self.reticle:
            for line in self.reticle:
                line.draw()
        info = f"FPS: {pyglet.clock.get_frequency():.1f} | Pos: {tuple(map(int, self.position))} | Mode: {self.mode}"
        self.label.text = info
        self.label.draw()
    
        inv_text = f"Bloco: {self.block_cursor} | Madeira: {self.inventory.get(WOOD,0)} | Pedras: {self.inventory.get(STONE,0)}"
        pyglet.text.Label(inv_text, x=10, y=20, color=(255,255,255,255)).draw()

        if self.credits_shown:
            self.credits_label.draw()


            
    def respawn(self):
        self.position = (0, 10, 0)
        self.dy = 0

    def trigger_win(self):
        self.credits_shown = True
        self.credits_label.text = ("PARABÉNS! VOCÊ ENCONTROU UM DIAMANTE!\n\n"
                                   "Criador: Matttz\nAno: 2026\n"
                                   "Tecnologias: Python, Pyglet, OpenGL Legacy Wrapper\n\n"
                                   "Pressione ESC para sair.")


if __name__ == '__main__':
    # Correção de Compatibilidade v0.5: Configura o OpenGL para a versão 2.1 (Legacy) para permitir glMatrixMode/glBegin
    config = pyglet.gl.Config(major_version=2, minor_version=1, double_buffer=True, depth_size=24)
    window = Window(width=800, height=600, caption='PyBlocks', resizable=True, config=config)
    pyglet.app.run()
