"""PBR materials for Casa 01 (Cycles). World coords are meters.

Scanned CC0 maps (Poly Haven / ambientCG, see fetch_assets.py) are used where
available, box-projected in object space, with per-element variation (each
stone / board / slat gets its own texture offset and tint via the 'rand'
face attribute). Procedural versions remain as fallbacks."""
import os
import bpy

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "textures")


def have(name):
    return os.path.exists(os.path.join(TEX, name, "sq_color.jpg"))


def hex2lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


class NB:
    """Tiny node-builder for shader trees."""

    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.nt = self.m.node_tree
        self.n = self.nt.nodes
        self.l = self.nt.links
        self.bsdf = self.n.get("Principled BSDF")
        self.out = self.n.get("Material Output")

    def node(self, t, **kw):
        nd = self.n.new(t)
        for k, v in kw.items():
            if k.startswith("in_"):
                key = k[3:].replace("_", " ")
                nd.inputs[key].default_value = v
            else:
                setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.l.new(a, b)

    def coords(self, kind="Object", scale=(1, 1, 1)):
        tc = self.node("ShaderNodeTexCoord")
        mp = self.node("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale
        self.link(tc.outputs[kind], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def noise(self, vec, scale=5.0, detail=6.0, rough=0.6, dist=0.0):
        nz = self.node("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = detail
        nz.inputs["Roughness"].default_value = rough
        nz.inputs["Distortion"].default_value = dist
        if vec is not None:
            self.link(vec, nz.inputs["Vector"])
        return nz

    def ramp(self, fac, stops):
        r = self.node("ShaderNodeValToRGB")
        cr = r.color_ramp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for el, (pos, col) in zip(cr.elements, stops):
            el.position = pos
            el.color = hex2lin(col) if isinstance(col, str) else col
        self.link(fac, r.inputs[0])
        return r

    def math(self, op, a, b=None, clamp=False):
        m = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                self.link(v, m.inputs[i])
        return m.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        mx = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        if isinstance(fac, (int, float)):
            mx.inputs["Factor"].default_value = fac
        else:
            self.link(fac, mx.inputs["Factor"])
        for sock, v in ((mx.inputs[6], a), (mx.inputs[7], b)):
            if isinstance(v, str):
                sock.default_value = hex2lin(v)
            elif isinstance(v, tuple):
                sock.default_value = v
            else:
                self.link(v, sock)
        return mx.outputs[2]

    def bump(self, height, strength=0.2, distance=0.01, normal=None):
        b = self.node("ShaderNodeBump")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height, b.inputs["Height"])
        if normal is not None:
            self.link(normal, b.inputs["Normal"])
        return b.outputs["Normal"]

    def attr(self, name="rand"):
        a = self.node("ShaderNodeAttribute", attribute_name=name, attribute_type="GEOMETRY")
        return a.outputs["Factor"]

    def obj_random(self):
        oi = self.node("ShaderNodeObjectInfo")
        return oi.outputs["Random"]

    def set(self, **kw):
        for k, v in kw.items():
            key = k.replace("_", " ")
            sock = self.bsdf.inputs[key]
            if isinstance(v, str):
                sock.default_value = hex2lin(v)
            elif isinstance(v, (int, float, tuple)):
                sock.default_value = v
            else:
                self.link(v, sock)
        return self.m


# ------------------------------------------------------------------ library
def stucco():
    b = NB("Stucco warm white")
    v = b.coords()
    big = b.noise(v, 0.8, 4, 0.5)
    col = b.ramp(big.outputs["Factor"], [(0.35, "#E7E0D3"), (0.65, "#EFEAE0")])
    fine = b.noise(v, 140, 10, 0.7)
    mid = b.noise(v, 9, 6, 0.6)
    h = b.math("ADD", fine.outputs["Factor"], b.math("MULTIPLY", mid.outputs["Factor"], 0.4))
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.86,
                 Normal=b.bump(h, 0.06, 0.004))


def paint_white():
    b = NB("Interior paint")
    return b.set(Base_Color="#EFECE6", Roughness=0.9)


def limestone(name="Lueders limestone"):
    b = NB(name)
    v = b.coords()
    r = b.attr("rand")
    base = b.ramp(r, [(0.0, "#CDBE9F"), (0.25, "#DCCFB4"), (0.5, "#E4D9C2"),
                      (0.75, "#D6C6A6"), (1.0, "#C8B591")])
    mott = b.noise(v, 3.5, 6, 0.6)
    mottc = b.mix(b.math("MULTIPLY", mott.outputs["Factor"], 0.35), base.outputs["Color"], "#BFAE8C", "MULTIPLY")
    speck = b.noise(v, 160, 4, 0.5)
    spk = b.math("GREATER_THAN", speck.outputs["Factor"], 0.66)
    col = b.mix(b.math("MULTIPLY", spk, 0.25), mottc, "#8E7E62")
    vor = b.node("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 70
    b.link(v, vor.inputs["Vector"])
    pits = b.math("LESS_THAN", vor.outputs["Distance"], 0.12)
    rough = b.noise(v, 22, 10, 0.75)
    h = b.math("SUBTRACT", rough.outputs["Factor"], b.math("MULTIPLY", pits, 0.35))
    return b.set(Base_Color=col, Roughness=0.84, Normal=b.bump(h, 0.35, 0.006))


def mortar():
    b = NB("Mortar")
    v = b.coords()
    nz = b.noise(v, 80, 6, 0.6)
    return b.set(Base_Color="#C3B59B", Roughness=0.95, Normal=b.bump(nz.outputs["Factor"], 0.3, 0.003))


def cobogo():
    b = NB("Cobogo white concrete")
    v = b.coords()
    r = b.attr("rand")
    big = b.noise(v, 2.5, 5, 0.6)
    c1 = b.ramp(big.outputs["Factor"], [(0.3, "#E2DDD2"), (0.7, "#ECE8DF")])
    col = b.mix(b.math("MULTIPLY", r, 0.18), c1.outputs["Color"], "#D6D0C3")
    fine = b.noise(v, 220, 8, 0.7)
    vor = b.node("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 150
    b.link(v, vor.inputs["Vector"])
    pores = b.math("LESS_THAN", vor.outputs["Distance"], 0.1)
    h = b.math("SUBTRACT", fine.outputs["Factor"], b.math("MULTIPLY", pores, 0.5))
    return b.set(Base_Color=col, Roughness=0.9, Normal=b.bump(h, 0.22, 0.003))


def cedar(name="Cedar", axis="Z", tone=1.0, weathered=0.0):
    """Clear western red cedar. axis = grain direction (X, Y or Z)."""
    b = NB(name)
    sc = {"X": (2.0, 70.0, 70.0), "Y": (70.0, 2.0, 70.0), "Z": (70.0, 70.0, 2.0)}[axis]
    v = b.coords(scale=sc)
    r = b.attr("rand")
    # offset coords per board so each board has its own grain
    off = b.node("ShaderNodeCombineXYZ")
    b.link(b.math("MULTIPLY", r, 37.0), off.inputs[0])
    b.link(b.math("MULTIPLY", r, 91.0), off.inputs[1])
    b.link(b.math("MULTIPLY", r, 53.0), off.inputs[2])
    va = b.node("ShaderNodeVectorMath", operation="ADD")
    b.link(v, va.inputs[0]); b.link(off.outputs[0], va.inputs[1])
    grain = b.noise(va.outputs[0], 1.2, 8, 0.62, dist=0.6)
    wave = b.node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
    wave.inputs["Scale"].default_value = 0.08
    wave.inputs["Distortion"].default_value = 9.0
    wave.inputs["Detail"].default_value = 3.0
    b.link(va.outputs[0], wave.inputs["Vector"])
    g = b.math("ADD", b.math("MULTIPLY", grain.outputs["Factor"], 0.7), b.math("MULTIPLY", wave.outputs["Factor"], 0.3))
    if weathered > 0:
        stops = [(0.2, "#7D6A58"), (0.55, "#9A8670"), (0.85, "#B3A08A")]
    else:
        stops = [(0.2, "#8A4B2A"), (0.5, "#B06D41"), (0.85, "#C98E5C")]
    col = b.ramp(g, stops)
    hsv = b.node("ShaderNodeHueSaturation")
    b.link(col.outputs["Color"], hsv.inputs["Color"])
    b.link(b.math("ADD", b.math("MULTIPLY", r, 0.035), 0.485), hsv.inputs["Hue"])
    b.link(b.math("MULTIPLY", b.math("ADD", b.math("MULTIPLY", r, 0.45), 0.78), tone), hsv.inputs["Value"])
    return b.set(Base_Color=hsv.outputs["Color"], Roughness=0.62,
                 Normal=b.bump(grain.outputs["Factor"], 0.12, 0.002))


def white_oak(name="Rift white oak", axis="X"):
    b = NB(name)
    sc = {"X": (1.5, 60.0, 60.0), "Y": (60.0, 1.5, 60.0), "Z": (60.0, 60.0, 1.5)}[axis]
    v = b.coords(scale=sc)
    g = b.noise(v, 1.5, 8, 0.6, dist=0.4)
    col = b.ramp(g.outputs["Factor"], [(0.25, "#B78E62"), (0.6, "#CDAA7E"), (0.9, "#D9BC94")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.48,
                 Normal=b.bump(g.outputs["Factor"], 0.08, 0.002))


def dark_wood():
    b = NB("Freijo dark wood")
    v = b.coords(scale=(1.5, 50, 50))
    g = b.noise(v, 1.4, 8, 0.6, dist=0.5)
    col = b.ramp(g.outputs["Factor"], [(0.25, "#4A2F1C"), (0.6, "#6A4429"), (0.9, "#7E5536")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.42)


def polished_concrete():
    b = NB("Polished concrete")
    v = b.coords()
    big = b.noise(v, 0.6, 6, 0.65)
    col = b.ramp(big.outputs["Factor"], [(0.3, "#A69E93"), (0.5, "#B4ACA1"), (0.72, "#C3BCB2")])
    agg = b.node("ShaderNodeTexVoronoi"); agg.inputs["Scale"].default_value = 90
    b.link(v, agg.inputs["Vector"])
    a = b.math("LESS_THAN", agg.outputs["Distance"], 0.08)
    c2 = b.mix(b.math("MULTIPLY", a, 0.35), col.outputs["Color"], "#8C8479")
    rn = b.noise(v, 1.8, 4, 0.5)
    rough = b.math("ADD", b.math("MULTIPLY", rn.outputs["Factor"], 0.18), 0.12)
    m = b.set(Base_Color=c2, Roughness=rough, Coat_Weight=0.25, Coat_Roughness=0.08)
    return m


def board_concrete():
    b = NB("Exterior concrete")
    v = b.coords()
    big = b.noise(v, 1.2, 6, 0.6)
    col = b.ramp(big.outputs["Factor"], [(0.3, "#B9B2A6"), (0.7, "#C9C3B8")])
    fine = b.noise(v, 120, 8, 0.7)
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.78, Normal=b.bump(fine.outputs["Factor"], 0.15, 0.003))


def pavers(name="Limestone pavers"):
    b = NB(name)
    tc = b.node("ShaderNodeTexCoord")
    br = b.node("ShaderNodeTexBrick", offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.005
    br.inputs["Mortar Smooth"].default_value = 0.2
    br.inputs["Brick Width"].default_value = 0.9144
    br.inputs["Row Height"].default_value = 0.6096
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = hex2lin("#DCD0B8")
    br.inputs["Color2"].default_value = hex2lin("#CFC0A2")
    br.inputs["Mortar"].default_value = hex2lin("#A99A80")
    b.link(tc.outputs["Object"], br.inputs["Vector"])
    v = tc.outputs["Object"]
    mott = b.noise(v, 4, 6, 0.6)
    col = b.mix(b.math("MULTIPLY", mott.outputs["Factor"], 0.3), br.outputs["Color"], "#B8A78A", "MULTIPLY")
    fine = b.noise(v, 60, 10, 0.7)
    h = b.math("SUBTRACT", fine.outputs["Factor"], b.math("MULTIPLY", br.outputs["Factor"], 1.5))
    return b.set(Base_Color=col, Roughness=0.8, Normal=b.bump(h, 0.25, 0.005))


def decomposed_granite():
    b = NB("Decomposed granite")
    v = b.coords()
    big = b.noise(v, 0.9, 5, 0.6)
    col = b.ramp(big.outputs["Factor"], [(0.3, "#A88B6A"), (0.7, "#BFA27E")])
    vor = b.node("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 260
    b.link(v, vor.inputs["Vector"])
    stones = vor.outputs["Color"]
    sc = b.ramp(b.math("MULTIPLY", stones, 1.0) if False else vor.outputs["Distance"],
                [(0.0, "#D8C7AE"), (0.5, "#9C8264"), (1.0, "#6E5A45")])
    c2 = b.mix(0.35, col.outputs["Color"], sc.outputs["Color"])
    fine = b.noise(v, 300, 6, 0.7)
    h = b.math("ADD", fine.outputs["Factor"], b.math("MULTIPLY", vor.outputs["Distance"], -0.8))
    return b.set(Base_Color=c2, Roughness=0.95, Normal=b.bump(h, 0.6, 0.004))


def mulch():
    b = NB("Mulch")
    v = b.coords()
    vor = b.node("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 90
    b.link(v, vor.inputs["Vector"])
    col = b.ramp(vor.outputs["Distance"], [(0.0, "#5A4330"), (0.6, "#3B2B1F"), (1.0, "#2A1F17")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.95,
                 Normal=b.bump(vor.outputs["Distance"], 0.8, 0.01))


def lawn_soil():
    b = NB("Lawn soil")
    v = b.coords()
    nz = b.noise(v, 2, 5, 0.6)
    col = b.ramp(nz.outputs["Factor"], [(0.3, "#4B5A2C"), (0.7, "#6B6B3A")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.95)


def asphalt():
    b = NB("Asphalt")
    v = b.coords()
    nz = b.noise(v, 200, 6, 0.7)
    big = b.noise(v, 0.4, 4, 0.6)
    col = b.ramp(big.outputs["Factor"], [(0.3, "#3C3B39"), (0.7, "#4A4845")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.9, Normal=b.bump(nz.outputs["Factor"], 0.4, 0.004))


def sidewalk():
    b = NB("Sidewalk")
    tc = b.node("ShaderNodeTexCoord")
    br = b.node("ShaderNodeTexBrick", offset=0.0, offset_frequency=1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Brick Width"].default_value = 1.524
    br.inputs["Row Height"].default_value = 1.524
    br.inputs["Color1"].default_value = hex2lin("#BDB6AA")
    br.inputs["Color2"].default_value = hex2lin("#C6C0B5")
    br.inputs["Mortar"].default_value = hex2lin("#8E887E")
    b.link(tc.outputs["Object"], br.inputs["Vector"])
    fine = b.noise(tc.outputs["Object"], 90, 8, 0.7)
    return b.set(Base_Color=br.outputs["Color"], Roughness=0.85, Normal=b.bump(fine.outputs["Factor"], 0.15, 0.003))


def metal(name="Dark bronze", color="#2C2723", rough=0.42, metallic=0.75):
    b = NB(name)
    v = b.coords()
    nz = b.noise(v, 30, 4, 0.5)
    rr = b.math("ADD", b.math("MULTIPLY", nz.outputs["Factor"], 0.12), rough - 0.06)
    return b.set(Base_Color=color, Metallic=metallic, Roughness=rr)


def roof_membrane():
    b = NB("Roof membrane")
    v = b.coords()
    nz = b.noise(v, 0.5, 4, 0.6)
    col = b.ramp(nz.outputs["Factor"], [(0.3, "#B8B5AE"), (0.7, "#C8C5BE")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.75)


def glass():
    b = NB("Glass")
    bs = b.bsdf
    bs.inputs["Base Color"].default_value = (0.92, 0.96, 0.95, 1)
    bs.inputs["Roughness"].default_value = 0.0
    bs.inputs["IOR"].default_value = 1.5
    bs.inputs["Transmission Weight"].default_value = 1.0
    # archviz glass: refractive/reflective to the camera, clear for all
    # indirect & shadow rays so sky, sun and bounce light reach interiors
    lp = b.node("ShaderNodeLightPath")
    tr = b.node("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.96, 0.95, 1)
    mx = b.node("ShaderNodeMixShader")
    b.link(b.math("SUBTRACT", 1.0, lp.outputs["Is Camera Ray"]), mx.inputs[0])
    b.link(bs.outputs["BSDF"], mx.inputs[1])
    b.link(tr.outputs["BSDF"], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m


def granite_black():
    b = NB("Honed black granite")
    v = b.coords()
    sp = b.noise(v, 260, 4, 0.5)
    col = b.ramp(sp.outputs["Factor"], [(0.45, "#181817"), (0.62, "#2C2B29"), (0.7, "#55524C")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.28)


def zellige_green():
    b = NB("Green glazed tile")
    tc = b.node("ShaderNodeTexCoord")
    br = b.node("ShaderNodeTexBrick", offset=0.0)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.003
    br.inputs["Brick Width"].default_value = 0.1016
    br.inputs["Row Height"].default_value = 0.1016
    br.inputs["Color1"].default_value = hex2lin("#2F5A48")
    br.inputs["Color2"].default_value = hex2lin("#3F6F59")
    br.inputs["Mortar"].default_value = hex2lin("#D8D2C4")
    b.link(tc.outputs["Object"], br.inputs["Vector"])
    nz = b.noise(tc.outputs["Object"], 40, 4, 0.5)
    h = b.math("SUBTRACT", b.math("MULTIPLY", nz.outputs["Factor"], 0.2), br.outputs["Factor"])
    return b.set(Base_Color=br.outputs["Color"], Roughness=0.12, Normal=b.bump(h, 0.3, 0.002))


def fabric(name, color, rough=1.0, sheen=0.4):
    b = NB(name)
    v = b.coords()
    nz = b.noise(v, 400, 4, 0.5)
    return b.set(Base_Color=color, Roughness=rough, Sheen_Weight=sheen,
                 Normal=b.bump(nz.outputs["Factor"], 0.15, 0.001))


def leather():
    b = NB("Cognac leather")
    v = b.coords()
    nz = b.noise(v, 60, 8, 0.6)
    col = b.ramp(nz.outputs["Factor"], [(0.3, "#6E3A1E"), (0.7, "#8C4F2A")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.45, Normal=b.bump(nz.outputs["Factor"], 0.1, 0.002))


def rug():
    b = NB("Wool rug")
    v = b.coords()
    nz = b.noise(v, 300, 4, 0.5)
    big = b.noise(v, 2, 3, 0.5)
    col = b.ramp(big.outputs["Factor"], [(0.3, "#CFC4B0"), (0.7, "#D9CFBC")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=1.0, Sheen_Weight=0.6,
                 Normal=b.bump(nz.outputs["Factor"], 0.5, 0.004))


def emission(name, color="#FFD9A8", strength=8.0):
    b = NB(name)
    em = b.node("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex2lin(color)
    em.inputs["Strength"].default_value = strength
    b.link(em.outputs[0], b.out.inputs["Surface"])
    return b.m


def ceramic_white():
    b = NB("Ceramic white")
    return b.set(Base_Color="#F2F0EC", Roughness=0.08)


def terracotta_pot():
    b = NB("Terracotta")
    v = b.coords()
    nz = b.noise(v, 20, 6, 0.6)
    col = b.ramp(nz.outputs["Factor"], [(0.3, "#9A5534"), (0.7, "#B5694A")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.85)


# ------------------------------------------------------------------ plants
def leaf(name="Live oak leaf", c1="#26331A", c2="#4A5C2A", trans="#8FA046"):
    b = NB(name)
    r = b.obj_random()
    col = b.ramp(r, [(0.0, c1), (0.6, c2), (1.0, "#5E6B33")])
    bs = b.bsdf
    b.link(col.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.5
    bs.inputs["Specular IOR Level"].default_value = 0.45
    tl = b.node("ShaderNodeBsdfTranslucent")
    tl.inputs["Color"].default_value = hex2lin(trans)
    mx = b.node("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.22
    b.link(bs.outputs["BSDF"], mx.inputs[1])
    b.link(tl.outputs["BSDF"], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m


def bark():
    b = NB("Live oak bark")
    v = b.coords(scale=(14, 14, 3))
    nz = b.noise(v, 3, 8, 0.65, dist=0.4)
    vor = b.node("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 6
    b.link(v, vor.inputs["Vector"])
    h = b.math("ADD", nz.outputs["Factor"], b.math("MULTIPLY", vor.outputs["Distance"], 0.6))
    col = b.ramp(h, [(0.2, "#211C18"), (0.55, "#3F3730"), (0.9, "#6A6157")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.9, Normal=b.bump(h, 0.8, 0.02))


def agave_mat():
    b = NB("Agave")
    r = b.obj_random()
    v = b.coords()
    nz = b.noise(v, 6, 4, 0.5)
    col = b.ramp(b.math("ADD", b.math("MULTIPLY", r, 0.5), b.math("MULTIPLY", nz.outputs["Factor"], 0.5)),
                 [(0.2, "#6E8D86"), (0.6, "#8CA59C"), (0.95, "#A6B49A")])
    return b.set(Base_Color=col.outputs["Color"], Roughness=0.42, Subsurface_Weight=0.05)


def grass_mat(name="Muhly grass", c1="#7C8A4A", c2="#B9AA74", c3="#9AA05C"):
    b = NB(name)
    r = b.obj_random()
    v = b.coords()
    nz = b.noise(v, 3, 3, 0.5)
    col = b.ramp(b.math("ADD", b.math("MULTIPLY", r, 0.6), b.math("MULTIPLY", nz.outputs["Factor"], 0.4)),
                 [(0.15, c1), (0.5, c3), (0.9, c2)])
    bs = b.bsdf
    b.link(col.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.6
    tl = b.node("ShaderNodeBsdfTranslucent")
    b.link(col.outputs["Color"], tl.inputs["Color"])
    mx = b.node("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.3
    b.link(bs.outputs["BSDF"], mx.inputs[1]); b.link(tl.outputs["BSDF"], mx.inputs[2])
    b.link(mx.outputs[0], b.out.inputs["Surface"])
    return b.m



# ------------------------------------------------------------------ scanned
def _img(b, folder, fname, noncolor, vec):
    path = os.path.join(TEX, folder, fname)
    n = b.node("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path, check_existing=True)
    n.image.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    n.projection = "BOX"
    n.projection_blend = 0.25
    n.interpolation = "Cubic" if noncolor else "Linear"
    b.link(vec, n.inputs["Vector"])
    return n


def scan(name, folder, tile=1.0, rotated=False, rand=False, tint=None, tint_mix=1.0,
         value=1.0, sat=1.0, hue_jitter=0.0, val_jitter=0.0, rough_scale=1.0, rough_add=0.0,
         bump=0.3, bump_dist=0.01, metallic=0.0, coat=0.0, zscale=1.0, extra=None,
         tint_mode="COLOR"):
    """Generic scanned material. tile = meters covered by one texture repeat."""
    b = NB(name)
    tc = b.node("ShaderNodeTexCoord")
    vec = tc.outputs["Object"]
    r = None
    if rand:
        r = b.attr("rand")
        off = b.node("ShaderNodeCombineXYZ")
        b.link(b.math("MULTIPLY", r, 13.7), off.inputs[0])
        b.link(b.math("MULTIPLY", r, 29.3), off.inputs[1])
        b.link(b.math("MULTIPLY", r, 7.1), off.inputs[2])
        va = b.node("ShaderNodeVectorMath", operation="ADD")
        b.link(vec, va.inputs[0]); b.link(off.outputs[0], va.inputs[1])
        vec = va.outputs[0]
    mp = b.node("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile, 1.0 / tile, 1.0 / (tile * zscale))
    b.link(vec, mp.inputs["Vector"])
    v = mp.outputs["Vector"]
    pre = "rot_" if rotated else "sq_"
    col = _img(b, folder, pre + "color.jpg", False, v).outputs["Color"]
    rough = _img(b, folder, pre + "rough.jpg", True, v).outputs["Color"]
    disp = _img(b, folder, pre + "disp.jpg", True, v).outputs["Color"]
    if tint and tint_mode == "SOFT_LIGHT":
        col = b.mix(tint_mix, tint, col, "SOFT_LIGHT")
    elif tint:
        col = b.mix(tint_mix, col, tint, "MULTIPLY") if tint_mix < 0 else b.mix(abs(tint_mix), col, tint, "COLOR")
    hsv = b.node("ShaderNodeHueSaturation")
    b.link(col, hsv.inputs["Color"])
    hsv.inputs["Saturation"].default_value = sat
    if r is not None and (hue_jitter or val_jitter):
        b.link(b.math("ADD", b.math("MULTIPLY", r, hue_jitter), 0.5 - hue_jitter / 2), hsv.inputs["Hue"])
        b.link(b.math("ADD", b.math("MULTIPLY", r, val_jitter), value - val_jitter / 2), hsv.inputs["Value"])
    else:
        hsv.inputs["Value"].default_value = value
    col = hsv.outputs["Color"]
    if extra:
        col = extra(b, col, v)
    rr = b.math("ADD", b.math("MULTIPLY", rough, rough_scale), rough_add, clamp=True)
    return b.set(Base_Color=col, Roughness=rr, Metallic=metallic, Coat_Weight=coat,
                 Coat_Roughness=0.1, Normal=b.bump(disp, bump, bump_dist))


def scanned_library():
    S = {}
    if have("stucco"):
        S["stucco"] = scan("Stucco warm white (scan)", "stucco", tile=1.6, tint="#F3ECDF", tint_mix=0.55,
                           value=1.02, bump=0.25, bump_dist=0.004, rough_add=0.15)
    if have("limestone"):
        S["limestone"] = scan("Lueders limestone (scan)", "limestone", tile=1.4, rand=True, tint="#DCCFB4",
                              tint_mix=0.85, tint_mode="SOFT_LIGHT", value=1.0, sat=0.95, hue_jitter=0.025,
                              val_jitter=0.16, bump=0.45, bump_dist=0.006, rough_add=0.15)
        S["pavers"] = _pavers_scan()
    if have("cedar"):
        S["cedar_z"] = scan("Cedar slats (scan)", "cedar", tile=0.9, rotated=True, rand=True, tint="#B0703F",
                            tint_mix=0.45, value=0.86, sat=0.82, hue_jitter=0.025, val_jitter=0.3, bump=0.12,
                            bump_dist=0.002, rough_add=0.25)
        S["cedar_y"] = scan("Cedar soffit (scan)", "cedar", tile=0.9, rotated=True, rand=True, tint="#B0703F",
                            tint_mix=0.45, value=0.84, sat=0.8, hue_jitter=0.025, val_jitter=0.3, bump=0.12,
                            bump_dist=0.002, rough_add=0.25)
        S["cedar_x"] = scan("Cedar boards X (scan)", "cedar", tile=0.9, rotated=False, rand=True, tint="#B0703F",
                            tint_mix=0.45, value=0.84, sat=0.8, hue_jitter=0.025, val_jitter=0.3, bump=0.12,
                            bump_dist=0.002, rough_add=0.25)
        S["fence"] = scan("Cedar fence (scan)", "cedar", tile=0.9, rand=True, tint="#9C6E4C", tint_mix=0.6,
                          value=0.78, sat=0.6, val_jitter=0.3, bump=0.2, bump_dist=0.003, rough_add=0.35)
    if have("oak"):
        S["oak"] = scan("Rift white oak (scan)", "oak", tile=0.8, rotated=True, rand=True, tint="#D2B48C",
                        tint_mix=0.5, value=1.25, sat=0.7, val_jitter=0.08, bump=0.05, bump_dist=0.001)
        S["oak_y"] = S["oak"]
    if have("walnut"):
        S["dark_wood"] = scan("Freijo / walnut (scan)", "walnut", tile=0.9, value=0.95, bump=0.04,
                              bump_dist=0.001, rough_scale=0.6)
    if have("concrete"):
        S["floor"] = scan("Polished concrete (scan)", "concrete", tile=2.5, tint="#B8AEA2", tint_mix=0.55,
                          value=0.82, bump=0.03, bump_dist=0.002, rough_scale=0.35, rough_add=0.05, coat=0.35)
        S["cobogo"] = scan("Cobogo white concrete (scan)", "concrete", tile=0.6, rand=True, tint="#EEE9DF",
                           tint_mix=0.6, value=1.08, val_jitter=0.06, bump=0.35, bump_dist=0.003, rough_add=0.35)
        S["concrete"] = scan("Exterior concrete (scan)", "concrete", tile=1.8, tint="#C8C0B3", tint_mix=0.5,
                             value=0.92, bump=0.25, bump_dist=0.004, rough_add=0.3)
    if have("dg"):
        S["dg"] = scan("Decomposed granite (scan)", "dg", tile=1.2, tint="#C9A983", tint_mix=0.35, value=1.0,
                       bump=0.6, bump_dist=0.006)
    if have("mulch"):
        S["mulch"] = scan("Mulch (scan)", "mulch", tile=1.2, value=0.85, bump=0.6, bump_dist=0.008)
    if have("bark"):
        S["bark"] = scan("Live oak bark (scan)", "bark", tile=0.8, zscale=2.0, value=0.75, sat=0.7,
                         bump=0.9, bump_dist=0.02)
    if have("leather"):
        S["leather"] = scan("Cognac leather (scan)", "leather", tile=0.7, value=0.85, bump=0.15, bump_dist=0.002)
    if have("linen"):
        S["linen"] = scan("Linen (scan)", "linen", tile=0.35, tint="#DCD3C4", tint_mix=1.0, value=1.0, sat=0.0,
                          bump=0.2, bump_dist=0.001, rough_add=0.3)
        S["olive_fabric"] = scan("Olive linen (scan)", "linen", tile=0.35, tint="#5E6142", tint_mix=1.0, value=0.9,
                                 bump=0.2, bump_dist=0.001, rough_add=0.3)
        S["terracotta_fabric"] = scan("Terracotta linen (scan)", "linen", tile=0.35, tint="#A8613F", tint_mix=1.0,
                                      value=0.9, bump=0.2, bump_dist=0.001, rough_add=0.3)
    if have("asphalt"):
        S["asphalt"] = scan("Asphalt (scan)", "asphalt", tile=3.0, value=0.8, bump=0.3, bump_dist=0.004)
    if have("grass_ground"):
        S["lawn_soil"] = scan("Lawn ground (scan)", "grass_ground", tile=2.0, tint="#5E7A33", tint_mix=0.6,
                              value=1.0, sat=1.1, bump=0.3)
    return S


def _pavers_scan():
    """Limestone pavers 36x24 with scanned stone surface and per-paver tint."""
    b = NB("Limestone pavers (scan)")
    tc = b.node("ShaderNodeTexCoord")
    v = tc.outputs["Object"]
    br = b.node("ShaderNodeTexBrick", offset=0.5, offset_frequency=2)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.005
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Brick Width"].default_value = 0.9144
    br.inputs["Row Height"].default_value = 0.6096
    br.inputs["Color1"].default_value = hex2lin("#E8DDC8")
    br.inputs["Color2"].default_value = hex2lin("#D3C4A6")
    br.inputs["Mortar"].default_value = hex2lin("#9C8E76")
    b.link(v, br.inputs["Vector"])
    mp = b.node("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 1.4, 1 / 1.4, 1 / 1.4)
    b.link(v, mp.inputs["Vector"])
    col = _img(b, "limestone", "sq_color.jpg", False, mp.outputs["Vector"]).outputs["Color"]
    disp = _img(b, "limestone", "sq_disp.jpg", True, mp.outputs["Vector"]).outputs["Color"]
    hsv = b.node("ShaderNodeHueSaturation")
    b.link(col, hsv.inputs["Color"])
    hsv.inputs["Saturation"].default_value = 0.4
    hsv.inputs["Value"].default_value = 1.6
    c2 = b.mix(0.75, hsv.outputs["Color"], br.outputs["Color"], "MULTIPLY")
    c3 = b.mix(b.math("SUBTRACT", 1.0, b.math("GREATER_THAN", br.outputs["Factor"], 0.5)), "#8F8169", c2)
    h = b.math("SUBTRACT", disp, b.math("MULTIPLY", br.outputs["Factor"], 2.0))
    return b.set(Base_Color=c3, Roughness=0.82, Normal=b.bump(h, 0.35, 0.006))


def build_library():
    L = dict(
        stucco=stucco(), paint=paint_white(), limestone=limestone(), mortar=mortar(),
        cobogo=cobogo(), cedar_z=cedar("Cedar slats", "Z"), cedar_y=cedar("Cedar soffit", "Y", tone=0.95),
        cedar_x=cedar("Cedar soffit X", "X", tone=0.95),
        fence=cedar("Cedar fence", "X", weathered=1.0),
        oak=white_oak(), oak_y=white_oak("Rift white oak Y", "Y"), dark_wood=dark_wood(),
        floor=polished_concrete(), concrete=board_concrete(), pavers=pavers(),
        dg=decomposed_granite(), mulch=mulch(), lawn_soil=lawn_soil(), asphalt=asphalt(),
        sidewalk=sidewalk(), bronze=metal("Dark bronze", "#1E1B18", 0.5, 0.35), black=metal("Black steel", "#151514", 0.5, 0.6),
        brass=metal("Brass", "#B08A4A", 0.3, 1.0), roof=roof_membrane(), glass=glass(),
        granite=granite_black(), tile=zellige_green(),
        linen=fabric("Linen", "#D9D1C2"), olive_fabric=fabric("Olive fabric", "#5E6142"),
        terracotta_fabric=fabric("Terracotta fabric", "#A8613F"),
        leather=leather(), rug=rug(), lamp=emission("Lamp glow"),
        ceramic=ceramic_white(), pot=terracotta_pot(),
        leaf=leaf(), leaf_shrub=leaf("Shrub leaf", "#2E3E22", "#56693A", "#93A85A"),
        bark=bark(), agave=agave_mat(),
        grass=grass_mat(), feather=grass_mat("Feather grass", "#A8A46A", "#D8C99A", "#C2B884"),
        turf=grass_mat("Buffalo grass", "#5B6B2E", "#8C8A4E", "#728038"),
        palm=grass_mat("Palmetto", "#2F4A26", "#4D6A36", "#3E5A2E"),
        house_beige=fabric("Neighbor siding", "#CFC6B6", 0.8, 0.0),
        house_roof=fabric("Neighbor roof", "#5B5953", 0.8, 0.0),
    )
    L.update(scanned_library())
    return L
