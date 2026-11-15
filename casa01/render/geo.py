"""Mesh-building helpers. Inputs in FEET (design units), output in meters."""
import random

import bpy
import numpy as np

M = 0.3048


class MB:
    """Accumulates boxes / prisms into one mesh with per-face material index
    and a per-face 'rand' attribute (used for per-stone / per-board variation)."""

    def __init__(self, name, mats):
        self.name = name
        self.mats = list(mats)
        self.v = []
        self.f = []
        self.fm = []
        self.fr = []

    def _add(self, verts, faces, mats, r):
        base = len(self.v)
        self.v += [(x * M, y * M, z * M) for x, y, z in verts]
        for f, m in zip(faces, mats):
            self.f.append(tuple(i + base for i in f))
            self.fm.append(m)
            self.fr.append(r)

    def box(self, x0, y0, z0, x1, y1, z1, mat=0, r=None, mats6=None):
        """mats6 = [bottom, top, y-min, y-max, x-min, x-max]"""
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        if x1 - x0 < 1e-5 or y1 - y0 < 1e-5 or z1 - z0 < 1e-5:
            return
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)]
        mats = mats6 if mats6 else [mat] * 6
        self._add(v, f, mats, random.random() if r is None else r)

    def prism(self, poly, z0, z1, top=0, side=0, bottom=0, r=None):
        """Extrude a CCW polygon (x,y list) between z0 and z1."""
        n = len(poly)
        v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        mats = [bottom, top]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
            mats.append(side)
        self._add(v, faces, mats, random.random() if r is None else r)

    def quad(self, pts, mat=0, r=None):
        self._add(pts, [(0, 1, 2, 3)], [mat], random.random() if r is None else r)

    def build(self, coll, bevel=0.0, smooth=False):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.fm)
        a = me.attributes.new("rand", "FLOAT", "FACE")
        a.data.foreach_set("value", self.fr)
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        if bevel > 0:
            b = ob.modifiers.new("bevel", "BEVEL")
            b.width = bevel
            b.segments = 2
            b.limit_method = "ANGLE"
            b.harden_normals = False
        return ob


def merge_copies(src_mesh, offsets, name, coll, rands=None, mats=None):
    """Realize many translated copies of a mesh into one object (fast, numpy).
    offsets in meters. Each copy gets its own 'rand' value."""
    nv = len(src_mesh.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    src_mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    loops = np.empty(len(src_mesh.loops), dtype=np.int32)
    src_mesh.loops.foreach_get("vertex_index", loops)
    starts = np.empty(len(src_mesh.polygons), dtype=np.int32)
    tot = np.empty(len(src_mesh.polygons), dtype=np.int32)
    src_mesh.polygons.foreach_get("loop_start", starts)
    src_mesh.polygons.foreach_get("loop_total", tot)
    mi = np.empty(len(src_mesh.polygons), dtype=np.int32)
    src_mesh.polygons.foreach_get("material_index", mi)
    k = len(offsets)
    offs = np.asarray(offsets, dtype=np.float32)
    all_co = (co[None, :, :] + offs[:, None, :]).reshape(-1, 3)
    all_loops = (loops[None, :] + (np.arange(k) * nv)[:, None]).reshape(-1)
    nl = len(loops)
    all_starts = (starts[None, :] + (np.arange(k) * nl)[:, None]).reshape(-1)
    all_tot = np.tile(tot, k)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(all_co))
    me.vertices.foreach_set("co", all_co.reshape(-1))
    me.loops.add(len(all_loops))
    me.loops.foreach_set("vertex_index", all_loops)
    me.polygons.add(len(all_starts))
    me.polygons.foreach_set("loop_start", all_starts)
    me.polygons.foreach_set("loop_total", all_tot)
    me.polygons.foreach_set("material_index", np.tile(mi, k))
    me.update(calc_edges=True)
    me.validate()
    for m in (mats or src_mesh.materials):
        me.materials.append(m)
    if rands is None:
        rands = [random.random() for _ in range(k)]
    a = me.attributes.new("rand", "FLOAT", "FACE")
    a.data.foreach_set("value", np.repeat(np.asarray(rands, dtype=np.float32), len(src_mesh.polygons)))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def subtract_rect(r, hole):
    """r, hole = (x0, x1, z0, z1). Returns list of rects of r minus hole."""
    x0, x1, z0, z1 = r
    hx0, hx1, hz0, hz1 = hole
    if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1:
        return [r]
    out = []
    if hx0 > x0:
        out.append((x0, hx0, z0, z1))
    if hx1 < x1:
        out.append((hx1, x1, z0, z1))
    cx0, cx1 = max(x0, hx0), min(x1, hx1)
    if hz0 > z0:
        out.append((cx0, cx1, z0, hz0))
    if hz1 < z1:
        out.append((cx0, cx1, hz1, z1))
    return out


def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c
