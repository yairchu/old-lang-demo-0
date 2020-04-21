# TODO:
# - splice by dragging inputs into arrows
# - fix graph bug (lines run over nodes)

import model.cls, model.clsnodes
from model.CallField import CallField
from lib import graphs

import pygame
import math

def split_to_rows(graph):
    order = graphs.topological_sort(graph)
    rows = []
    for node in order:
        last = None
        for row in reversed(rows):
            if row & graph[node]:
                break
            last = row
        if last is None:
            last = set()
            rows.append(last)
        last.add(node)
    return rows

def graph_positions(surface, graph):
    resolution = surface.get_size()
    rows = split_to_rows(graph)
    if not rows:
        return
    row_size = resolution[1]/len(rows)
    cur_y = row_size/2
    max_row_len = max(map(len, rows))
    dist_in_row = resolution[0]/max_row_len
    for row in rows:
        cur_x = resolution[0]/2-dist_in_row*(len(row)-1)/2
        for node in row:
            yield node, (cur_x, cur_y)
            cur_x += dist_in_row
        cur_y += row_size

def distance_2d(xxx_todo_changeme1, xxx_todo_changeme2):
    (ax, ay) = xxx_todo_changeme1
    (bx, by) = xxx_todo_changeme2
    return ((ax-bx)**2+(ay-by)**2)**.5

def draw_centered_text(surface, xxx_todo_changeme3, text, color, max_size):
    (x, y) = xxx_todo_changeme3
    lines = [line.strip() for line in [_f for _f in text.splitlines() if _f]]
    from lib.font import find_font
    font = find_font(lines, max_size)
    pixels = [font.render(line, True, color) for line in lines]
    total_y = sum(p.get_size()[1] for p in pixels)
    cur_y = y-total_y/2
    for p in pixels:
        sx, sy = p.get_size()
        surface.blit(p, (x-sx/2, cur_y))
        cur_y += sy

def cls_to_graph(cls):
    res = {}
    for node in cls.nodes:
        res[node] = set()
    if not isinstance(cls, model.cls.Class):
        return res
    for src, dst in cls.links.items():
        if isinstance(src, CallField):
            src = src.call
        if isinstance(dst, CallField):
            dst = dst.call
        res[src].add(dst)
    return res

def call_positions(node, xxx_todo_changeme4):
    ((x, y), radius) = xxx_todo_changeme4
    inputs = list(node.cls.inputs())
    outputs = list(node.cls.outputs())
    for negate, items in [(-1, inputs), (1, outputs)]:
        for i, field in enumerate(items):
            angle = (i+1)*math.pi/(len(items)+1)
            yield CallField(node, field), (
                (x+math.cos(angle)*radius, y+negate*math.sin(angle)*radius), radius/3)

class QuitEvent(Exception):
    pass

class Stack(object):
    def __init__(self):
        self.items = []
    def draw(self):
        return self.items[-1].draw()
    def handle_event(self, event):
        if not self.items:
            return False
        if self.items[-1].handle_event(event):
            return True
        if pygame.KEYDOWN == event.type and pygame.K_ESCAPE == event.key:
            self.items.pop()
            if not self.items:
                raise QuitEvent()
            return True
        return False

class Env(object):
    def __init__(self, menu):
        self.stack = Stack()
        self.clipboard = None
        self.menu = menu
    def handle_event(self, event):
        self.stack.handle_event(event)
    def draw(self):
        self.stack.draw()

class ObjEdit(object):
    field_color = 255, 255, 255
    call_color = 200, 200, 200
    arrow_color = 0, 0, 255
    drag_arrow_color = 255, 0, 255
    drag_node_color = 255, 0, 255
    label_color = 255, 0, 0
    constant_color = 111, 111, 255
    bg_color = 0, 0, 0
    def __init__(self, obj, surface, env):
        self.obj = obj
        self.surface = surface
        self.is_dragging = False
        self.env = env

        self.obj.updated.register(self.updated)
        self.positions = {}
        self.animation_index = None
        self.force_update = True
        self.check_updated()

    def updated(self):
        self.force_update = True

    def check_updated(self):
        if not self.force_update:
            return
        self.force_update = False
        self.update_positions()
        self.animation_index = 0
        # Put default items in self.positions so we can iterate it and
        # see "all" changes (both additions and deletions.)
        for key, (pos, radius) in self.new_positions.items():
            self.positions.setdefault(key, (pos, 0))

    def update_positions(self):
        graph = cls_to_graph(self.obj.cls)
        positions = dict(graph_positions(self.surface, graph))
        if len(positions) >= 2:
            min_distance = min(distance_2d(a, b)
                               for a in positions.values()
                               for b in positions.values() if a != b)
        else:
            min_distance = min(self.surface.get_size())
        node_radius = min_distance/3

        self.new_positions = dict((k, (pos, node_radius)) for k, pos in positions.items())

    def animation_progress(self):
        if self.animation_index is None:
            return
        self.animation_index += 1
        if self.animation_index == 20:
            self.positions, self.new_positions = self.new_positions, None
            self.animation_index = None
            return
        for key, ((x, y), radius) in self.positions.items():
            (new_x, new_y), new_radius = self.new_positions.get(key, ((x, y), 0))
            self.positions[key] = ((self.animation_pos_state(x, new_x),
                                    self.animation_pos_state(y, new_y)),
                                   self.animation_pos_state(radius, new_radius))

    def animation_pos_state(self, pos, new_pos, slowness=5.):
        pos = int(pos)
        new_pos = int(new_pos)
        if new_pos == pos:
            return pos
        if new_pos > pos:
            return min(pos + max(3, int((new_pos-pos) / slowness)), new_pos)
        else:
            return max(pos + min(-3, int((new_pos-pos) / slowness)), new_pos)

    def draw(self):
        self.animation_progress()
        self.surface.fill(self.bg_color)
        nodes_order = list(self.positions.keys())
        for node in list(self.positions.keys()):
            if isinstance(node, model.clsnodes.ClassCall):
                new_positions = dict(call_positions(node, self.positions[node]))
                nodes_order.extend(new_positions.keys())
                self.positions.update(new_positions)
        for node in nodes_order:
            (x, y), radius = self.positions[node]
            if self.is_dragging and node in [self.drag_src, self.drag_dst]:
                color = self.drag_node_color
            elif isinstance(node, model.clsnodes.ClassCall):
                color = self.call_color
            elif isinstance(node, model.clsnodes.Constant):
                color = self.constant_color
            else:
                color = self.field_color
            pygame.draw.circle(self.surface, color, (int(x), int(y)), int(radius))
        if isinstance(self.obj.cls, model.cls.Class):
            for dst, src in self.obj.cls.links.items():
                pygame.draw.line(self.surface, self.arrow_color, self.positions[src][0], self.positions[dst][0], 2)
        if self.is_dragging and self.drag_dst is not None:
                  pygame.draw.line(self.surface, self.drag_arrow_color, self.positions[self.drag_src][0], self.positions[self.drag_dst][0], 2)
        for node, ((x, y), radius) in self.positions.items():
            if node in self.obj:
                text = str(self.obj[node])
            else:
                text = str(node)
            if isinstance(node, (model.clsnodes.Field, model.clsnodes.Constant, CallField)) and node in self.obj:
                text = '%s\n%s' % (str(node), self.obj[node])
            draw_centered_text(self.surface, (x, y), text, self.label_color,
                               (radius*2, radius*2))

    def drag_src_filter(self, node):
        return not isinstance(node, model.clsnodes.ClassCall)

    def drag_dst_filter(self, node):
        order = self.link_order(self.drag_src, node)
        if order is None:
            return False
        src, dst = order

        # check that it doesn't make cycles in graph
        graph = cls_to_graph(self.obj.cls)

        def field_node(field):
            if isinstance(field, CallField):
                return field.call
            return field
        src, dst = list(map(field_node, (src, dst)))

        # See if adding this to the graph creates cycles
        graph[dst].add(src)
        if graphs.has_cycles(graph):
            return False

        return True
    def obj_at_pos(self, xxx_todo_changeme, filter):
        (x, y) = xxx_todo_changeme
        for obj, ((ox, oy), radius) in self.positions.items():
            if abs(x-ox) > radius or abs(y-oy) > radius:
                continue
            if (x-ox)**2+(y-oy)**2 <= radius**2 and filter(obj):
                return obj
        return None
    def edit_filter(self, node):
        return (node in self.obj.cls.inputs() or
                isinstance(node, model.clsnodes.Constant))
    def delete_filter(self, node):
        return self.copy_filter(node)
    def label_edit_filter(self, node):
        return True
    def call_filter(self, node):
        return (isinstance(node, model.clsnodes.ClassCall) and
                isinstance(self.obj[node], model.cls.Instance))
    def copy_filter(self, node):
        return not isinstance(node, CallField)
    def handle_event(self, event):
        result = self._handle_event(event)
        self.check_updated()
        return result
    def _handle_event(self, event):
        if self.is_dragging:
            if event.type == pygame.MOUSEMOTION:
                self.drag_dst = self.obj_at_pos(event.pos, self.drag_dst_filter)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.drag_complete()
            else:
                return False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            node = self.obj_at_pos(event.pos, self.drag_src_filter)
            if node is not None:
                self.is_dragging = True
                self.drag_src = node
                self.drag_dst = None
        elif event.type == pygame.KEYDOWN:
            def getnode(filter = self.edit_filter):
                return self.obj_at_pos(pygame.mouse.get_pos(), filter)
            def getval():
                if isinstance(node, model.clsnodes.Constant):
                    return node.value
                if node not in self.obj.state:
                    return 0
                return self.obj[node]
            def setval(val):
                if isinstance(node, model.clsnodes.Constant):
                    node.set_value(val, self.obj.cls)
                else:
                    self.obj[node] = val
            is_ctrl = event.mod in [pygame.KMOD_LCTRL, pygame.KMOD_RCTRL]
            if event.mod & pygame.KMOD_SHIFT:
                node = getnode(self.label_edit_filter)
                if node is None:
                    return False
                if isinstance(node, model.clsnodes.ClassCall):
                    item = node.cls
                elif isinstance(node, CallField):
                    item = node.field
                else:
                    item = node
                if event.key == pygame.K_BACKSPACE:
                    item.label = item.label[:-1]
                else:
                    try:
                        item.label += chr(event.key)
                    except ValueError:
                        pass
            elif event.key == pygame.K_RETURN:
                node = getnode(self.call_filter)
                if node is not None:
                    self.env.stack.items.append(ObjEdit(self.obj[node], self.surface, self.env))
            elif event.key == pygame.K_BACKSPACE:
                node = getnode()
                if node is not None:
                    setval(int(getval()/10.))
            elif '0' <= event.unicode <= '9':
                node = getnode()
                digit = int(event.unicode)
                if node is not None:
                    val = getval()*10
                    if val >= 0:
                        val += digit
                    else:
                        val -= digit
                    setval(val)
            elif event.key == pygame.K_MINUS:
                node = getnode()
                if node is not None:
                    setval(-getval())
            elif event.key == pygame.K_DELETE:
                node = self.obj_at_pos(pygame.mouse.get_pos(), self.delete_filter)
                if node is not None:
                    self.obj.cls.delete_node(node)
            elif event.key == pygame.K_c and is_ctrl:
                self.env.clipboard = getnode(self.copy_filter)
            elif event.key == pygame.K_v and is_ctrl:
                if self.env.clipboard is not None:
                    self.obj.cls.add_node(self.env.clipboard.copy())
            elif event.key == pygame.K_n and is_ctrl:
                cls = model.cls.Class('class', [])
                call = model.clsnodes.ClassCall(cls)
                self.obj.cls.add_node(call)
            else:
                return False
        else:
            return False
        return True
    def link_order(self, a, b):
        """Return (src, dst) order.

        Return the only valid (src, dst) order of given (a, b) or None
        if there is no such valid ordering"""
        aa, ba = [(x.can_be_src(), x.can_be_dst())
                  for x in (a, b)]
        options = [
            (x, y)
            for x, y, xa, ya in [(a, b, aa, ba),
                                 (b, a, ba, aa)]
            if xa[0] and ya[1]
        ]
        if len(options) != 1:
            return None
        option, = options
        return option
        
    def drag_complete(self):
        self.is_dragging = False
        if self.drag_dst is None:
            self.obj.cls.unlink(self.drag_src)
            return
        src, dst = self.link_order(self.drag_src, self.drag_dst)
        self.obj.cls.link(src, dst)
