"""Procedural Central-Texas plants for Cycles: live oak (space colonization),
agave, sotol, dwarf palmetto, muhly / feather grass, buffalo-grass tufts and
rounded shrubs. All units here are METERS."""
import math
import random

import bpy
import bmesh
from mathutils import Vector, Matrix, kdtree


# ---------------------------------------------------------------- utilities
def _link(obj, coll):
    coll.objects.link(obj)
    return obj


def mesh_obj(name, verts, faces, coll, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    if mat:
        ob.data.materials.append(mat)
    return _link(ob, coll)


def points_obj(name, pts, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    ob = bpy.data.objects.new(name, me)
    return _link(ob, coll)


def instancer_group(name, collection, rot_xy=math.pi, scale=(0.75, 1.3), align_z=False):
    """GN: instance a collection (random pick) on every vertex, random rot/scale.
    Vertex attribute 'scale' (float) multiplies the random scale if present."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, l = ng.nodes, ng.links
    gin = n.new("NodeGroupInput")
    gout = n.new("NodeGroupOutput")
    ci = n.new("GeometryNodeCollectionInfo")
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    ci.transform_space = "ORIGINAL"
    ci.inputs["Collection"].default_value = collection
    iop = n.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    rnd_i = n.new("FunctionNodeRandomValue"); rnd_i.data_type = "INT"
    rnd_i.inputs["Min"].default_value = 0
    rnd_i.inputs["Max"].default_value = 99
    rnd_i.inputs["Seed"].default_value = 3
    rnd_r = n.new("FunctionNodeRandomValue"); rnd_r.data_type = "FLOAT_VECTOR"
    if align_z:
        rnd_r.inputs["Min"].default_value = (-math.pi, -math.pi, -math.pi)
        rnd_r.inputs["Max"].default_value = (math.pi, math.pi, math.pi)
    else:
        rnd_r.inputs["Min"].default_value = (-rot_xy * 0.15, -rot_xy * 0.15, 0.0)
        rnd_r.inputs["Max"].default_value = (rot_xy * 0.15, rot_xy * 0.15, 2 * math.pi)
    rnd_r.inputs["Seed"].default_value = 5
    rnd_s = n.new("FunctionNodeRandomValue"); rnd_s.data_type = "FLOAT"
    rnd_s.inputs["Min"].default_value = scale[0]
    rnd_s.inputs["Max"].default_value = scale[1]
    rnd_s.inputs["Seed"].default_value = 11
    attr = n.new("GeometryNodeInputNamedAttribute"); attr.data_type = "FLOAT"
    attr.inputs["Name"].default_value = "pscale"
    # factor = exists ? pscale : 1   ->  pscale*exists + (1-exists)
    m1 = n.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    m2 = n.new("ShaderNodeMath"); m2.operation = "SUBTRACT"; m2.inputs[0].default_value = 1.0
    m3 = n.new("ShaderNodeMath"); m3.operation = "ADD"
    m4 = n.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
    l.new(attr.outputs["Attribute"], m1.inputs[0]); l.new(attr.outputs["Exists"], m1.inputs[1])
    l.new(attr.outputs["Exists"], m2.inputs[1])
    l.new(m1.outputs[0], m3.inputs[0]); l.new(m2.outputs[0], m3.inputs[1])
    l.new(m3.outputs[0], m4.inputs[0]); l.new(rnd_s.outputs[0], m4.inputs[1])
    l.new(gin.outputs["Geometry"], iop.inputs["Points"])
    l.new(ci.outputs[0], iop.inputs["Instance"])
    l.new(rnd_i.outputs[0], iop.inputs["Instance Index"])
    l.new(rnd_r.outputs[0], iop.inputs["Rotation"])
    l.new(m4.outputs[0], iop.inputs["Scale"])
    l.new(iop.outputs[0], gout.inputs[0])
    return ng


def scatter(name, pts, collection, coll, rot_xy=math.pi, scale=(0.75, 1.3), pscale=None, align_z=False):
    ob = points_obj(name, pts, coll)
    if pscale is not None:
        a = ob.data.attributes.new("pscale", "FLOAT", "POINT")
        a.data.foreach_set("value", pscale)
    ng = instancer_group(name + "_GN", collection, rot_xy, scale, align_z)
    mod = ob.modifiers.new("scatter", "NODES")
    mod.node_group = ng
    return ob


def hidden_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


# ---------------------------------------------------------------- leaves
def leaf_mesh(name, coll, mat, length=0.06, width=0.028, bend=0.25):
    """small elliptic leaf, slightly cupped & bent (live oak)."""
    verts, faces = [], []
    n = 5
    for i in range(n + 1):
        t = i / n
        y = t * length
        w = width * math.sin(math.pi * min(1.0, t * 1.05)) * 0.5 + 1e-4
        z = bend * (t ** 2) * length
        verts += [(-w, y, z + w * 0.25), (0, y, z), (w, y, z + w * 0.25)]
    for i in range(n):
        a = i * 3
        faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    return mesh_obj(name, verts, faces, coll, mat)


# ---------------------------------------------------------------- live oak
def live_oak(name, loc, height, spread, seed, coll, bark_mat, leaf_coll,
             leaf_density=1.0, crown_base=0.2):
    """Space-colonization tree shaped like a Texas live oak: short trunk that
    forks low into long, sinuous, near-horizontal limbs under a broad dome."""
    rng = random.Random(seed)
    R = spread / 2.0
    H = height
    cz0 = H * crown_base
    lobes = []
    for i in range(11):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.2, 0.68) * R
        c = Vector((math.cos(a) * r, math.sin(a) * r, rng.uniform(0.46, 0.62) * H))
        lobes.append((c, rng.uniform(0.38, 0.52) * R, rng.uniform(0.2, 0.27) * H))
    lobes.append((Vector((0, 0, 0.64 * H)), 0.55 * R, 0.3 * H))

    def inside(p):
        for c, rr, rz in lobes:
            if ((p.x - c.x) / rr) ** 2 + ((p.y - c.y) / rr) ** 2 + ((p.z - c.z) / rz) ** 2 < 1.0:
                return True
        return False

    attract = []
    n_att = int(3500 + 70 * R * R)
    tries = 0
    while len(attract) < n_att and tries < n_att * 60:
        tries += 1
        p = Vector((rng.uniform(-R, R), rng.uniform(-R, R), rng.uniform(cz0, H)))
        if inside(p):
            attract.append(p)

    D = max(0.22, H * 0.02)
    di = R * 0.42
    dk = D * 1.6

    nodes = [Vector((0, 0, 0))]
    parent = [-1]
    lean = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1)).normalized()
    p = Vector((0, 0, 0))
    while p.z < cz0 * 0.6:
        p = p + lean * D
        nodes.append(p.copy())
        parent.append(len(nodes) - 2)
    child_dirs = {}

    alive = list(range(len(attract)))
    for it in range(400):
        if not alive:
            break
        kd = kdtree.KDTree(len(nodes))
        for i, q in enumerate(nodes):
            kd.insert(q, i)
        kd.balance()
        pull = {}
        cnt = {}
        survivors = []
        for ai in alive:
            a = attract[ai]
            co, idx, dist = kd.find(a)
            if dist < dk:
                continue
            survivors.append(ai)
            if dist < di:
                pull[idx] = pull.get(idx, Vector((0, 0, 0))) + (a - nodes[idx]).normalized()
                cnt[idx] = cnt.get(idx, 0) + 1
        alive = survivors
        added = 0
        for idx, v in pull.items():
            if v.length < 1e-6:
                continue
            d = v.normalized()
            # live-oak tropism: reach outward, slight gravity on long limbs
            d = (d + Vector((0, 0, -0.12))).normalized()
            dup = False
            for cd in child_dirs.get(idx, ()):
                if cd.dot(d) > 0.94:
                    dup = True
                    break
            if dup:
                continue
            child_dirs.setdefault(idx, []).append(d)
            nodes.append(nodes[idx] + d * D)
            parent.append(idx)
            added += 1
        if added == 0:
            if not pull:
                tip = len(nodes) - 1
                if nodes[tip].z < H:
                    nodes.append(nodes[tip] + lean * D)
                    parent.append(tip)
                    continue
            break

    N = len(nodes)
    children = [[] for _ in range(N)]
    for i in range(1, N):
        children[parent[i]].append(i)
    depth = [0] * N
    for i in range(1, N):
        depth[i] = depth[parent[i]] + 1
    radius = [0.0] * N
    r_tip = 0.010
    for i in sorted(range(N), key=lambda i: -depth[i]):
        if not children[i]:
            radius[i] = r_tip
        else:
            radius[i] = sum(radius[c] ** 2.3 for c in children[i]) ** (1 / 2.3)
    for i in range(N):
        if radius[i] > 0.04:
            radius[i] *= 1.0 + 0.9 * min(1.0, (radius[i] - 0.04) / 0.15)
    for i in range(N):
        if nodes[i].z < 0.9:
            radius[i] *= 1.0 + (0.9 - nodes[i].z) * 0.3
    for i in range(1, N):
        j = min(radius[i] * 0.3, 0.03) + 0.01
        nodes[i] = nodes[i] + Vector((rng.uniform(-j, j), rng.uniform(-j, j), rng.uniform(-j, j)))

    cu = bpy.data.curves.new(name + "_wood", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    starts = [0]
    min_r = 0.007
    while starts:
        s = starts.pop()
        chain = [parent[s]] if parent[s] >= 0 else []
        i = s
        while True:
            chain.append(i)
            ch = sorted(children[i], key=lambda c: -radius[c])
            if not ch:
                break
            for c in ch[1:]:
                if radius[c] > min_r:
                    starts.append(c)
            i = ch[0]
            if radius[i] < min_r:
                break
        if len(chain) < 2:
            continue
        sp = cu.splines.new("POLY")
        sp.points.add(len(chain) - 1)
        for k, ni in enumerate(chain):
            q = nodes[ni]
            sp.points[k].co = (q.x, q.y, q.z, 1)
            sp.points[k].radius = radius[ni]
    wood = bpy.data.objects.new(name + "_wood", cu)
    wood.data.materials.append(bark_mat)
    wood.location = loc
    coll.objects.link(wood)

    pts = []
    for i in range(1, N):
        if radius[i] < 0.034 and nodes[i].z > cz0 * 0.9:
            k = int(rng.uniform(34, 56) * leaf_density)
            a, b = nodes[parent[i]], nodes[i]
            for _ in range(k):
                t = rng.random()
                c = a.lerp(b, t)
                off = Vector((rng.gauss(0, 0.2), rng.gauss(0, 0.2), rng.gauss(0, 0.13)))
                pts.append(c + off)
    leaves = scatter(name + "_leaves", pts, leaf_coll, coll, rot_xy=math.pi, scale=(0.8, 1.4), align_z=True)
    leaves.location = loc
    return wood, leaves, len(pts)


def _depth(i, parent, _cache={}):
    d = 0
    while parent[i] >= 0:
        i = parent[i]
        d += 1
    return d


# ---------------------------------------------------------------- agave
def agave(name, coll, mat, seed=1, n_leaves=26, length=0.75, width=0.13):
    rng = random.Random(seed)
    verts, faces = [], []
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(n_leaves):
        t = k / n_leaves
        az = k * golden + rng.uniform(-0.05, 0.05)
        elev = math.radians(78 - 62 * t + rng.uniform(-4, 4))   # inner leaves upright
        L = length * (0.55 + 0.45 * t) * rng.uniform(0.9, 1.08)
        W = width * (0.7 + 0.3 * t)
        segs = 7
        base = len(verts)
        for s in range(segs + 1):
            u = s / segs
            # leaf curve: rises then droops slightly
            e = elev - 0.35 * u * u * (1 - elev / 1.6)
            r = L * u
            x = r * math.cos(e)
            z = r * math.sin(e) + 0.05
            w = W * (1 - u ** 1.6) * (0.6 + 0.4 * math.sin(math.pi * min(1, u * 2.2))) + 0.004
            th = w * 0.35  # V-shaped cupped cross-section
            ca, sa = math.cos(az), math.sin(az)
            for (lat, up) in ((-w, th), (0, 0), (w, th)):
                px, py, pz = x, lat, z + up
                verts.append((px * ca - py * sa, px * sa + py * ca, pz))
        for s in range(segs):
            a = base + s * 3
            faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
    return mesh_obj(name, verts, faces, coll, mat)


# ---------------------------------------------------------------- grasses
def grass_clump(name, coll, mat, seed=1, blades=70, height=0.8, spread=0.45,
                width=0.006, droop=0.6, segs=6):
    rng = random.Random(seed)
    verts, faces = [], []
    for b in range(blades):
        az = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0, 0.06)
        lean = rng.uniform(0.15, 1.0) * spread
        h = height * rng.uniform(0.6, 1.1)
        w = width * rng.uniform(0.7, 1.3)
        ca, sa = math.cos(az), math.sin(az)
        base = len(verts)
        for s in range(segs + 1):
            u = s / segs
            out = r0 + lean * (u ** 1.5)
            z = h * (u - droop * 0.35 * u ** 3 * (lean / spread))
            ww = w * (1 - u * 0.9)
            px, pz = out, z
            # blade plane perpendicular to direction
            verts.append((px * ca + ww * -sa, px * sa + ww * ca, pz))
            verts.append((px * ca - ww * -sa, px * sa - ww * ca, pz))
        for s in range(segs):
            a = base + s * 2
            faces.append((a, a + 2, a + 3, a + 1))
    return mesh_obj(name, verts, faces, coll, mat)


def sotol(name, coll, mat, seed=1):
    """Dasylirion: a fountain-sphere of stiff thin leaves."""
    return grass_clump(name, coll, mat, seed=seed, blades=140, height=0.95, spread=0.9,
                       width=0.011, droop=0.25, segs=6)


# ---------------------------------------------------------------- palmetto
def palmetto(name, coll, mat, seed=1, n_leaves=9):
    rng = random.Random(seed)
    verts, faces = [], []
    for k in range(n_leaves):
        az = rng.uniform(0, 2 * math.pi)
        elev = math.radians(rng.uniform(35, 72))
        L = rng.uniform(0.55, 0.95)
        ca, sa = math.cos(az), math.sin(az)
        tip = Vector((math.cos(elev) * L, 0, math.sin(elev) * L + 0.05))
        # petiole as thin strip
        base = len(verts)
        for s in range(5):
            u = s / 4
            p = tip * u
            for side in (-0.006, 0.006):
                verts.append((p.x * ca - side * sa, p.x * sa + side * ca, p.z))
        for s in range(4):
            a = base + s * 2
            faces.append((a, a + 2, a + 3, a + 1))
        # fan blade: segments radiating from tip, pleated
        segs = 22
        fan = math.radians(rng.uniform(150, 200))
        Rf = rng.uniform(0.35, 0.55)
        tilt = elev * 0.6
        base = len(verts)
        verts.append((tip.x * ca, tip.x * sa, tip.z))
        rings = 4
        for s in range(segs + 1):
            phi = -fan / 2 + fan * s / segs
            for rr in range(1, rings + 1):
                rad = Rf * rr / rings * (0.85 + 0.15 * math.cos(phi))
                pleat = 0.025 * (1 if s % 2 else -1) * (rr / rings)
                lx = math.cos(phi) * rad
                ly = math.sin(phi) * rad
                # fan plane tilted: local x outward along leaf, z up
                px = tip.x + lx * math.cos(tilt)
                pz = tip.z + lx * math.sin(tilt) * 0.5 + pleat - 0.12 * (rad / Rf) ** 2
                py = ly
                verts.append((px * ca - py * sa, px * sa + py * ca, pz))
        for s in range(segs):
            a0 = base + 1 + s * rings
            b0 = base + 1 + (s + 1) * rings
            faces.append((base, a0, b0))
            for rr in range(rings - 1):
                if rr == rings - 2 and s % 2 == 0:
                    continue  # split leaf tips
                faces.append((a0 + rr, a0 + rr + 1, b0 + rr + 1, b0 + rr))
    return mesh_obj(name, verts, faces, coll, mat)


# ---------------------------------------------------------------- shrub
def shrub_points(center, rx, ry, rz, n, rng):
    pts = []
    while len(pts) < n:
        p = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.1, 1)))
        d = p.x * p.x + p.y * p.y + p.z * p.z
        if 0.55 < d < 1.0:
            pts.append(Vector((center[0] + p.x * rx, center[1] + p.y * ry, center[2] + p.z * rz)))
    return pts
