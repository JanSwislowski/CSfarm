"""
Graph Creator — pygame app
Features:
  - Loads graph from graph.txt on startup (if it exists)
  - Vertices can only be placed ON the image (preserves aspect ratio; TL = 0,0)
  - Directed (one-sided) edges with arrowheads
  - Move vertices by dragging them
  - Delete edges by clicking near them in Delete-Edge mode
  - On close, graph is saved to graph.txt (positions in original image coords)

Controls:
  A / button  → Add-Vertex mode  (left-click on map to place)
  C / button  → Connect mode     (click src vertex, then dst vertex)
  D / button  → Delete-Edge mode (click near an edge to remove it)
  M / button  → Move mode        (drag a vertex to reposition)
  Right-click → Delete vertex under cursor (any mode)
  Escape      → Cancel / deselect
"""

import sys, math, json, os
import pygame

IMAGE_PATH = "fragment.png"
SAVE_PATH  = "graph.txt"
WINDOW_W   = 1280
WINDOW_H   = 760
FPS        = 60

VERTEX_RADIUS  = 10
VERTEX_COLOR   = (255, 220, 60)
VERTEX_BORDER  = (60, 40, 10)
HOVER_COLOR    = (255, 255, 160)
SELECTED_COLOR = (100, 220, 255)
DRAG_COLOR     = (120, 255, 160)
EDGE_COLOR     = (255, 80, 80)
EDGE_HOV_COLOR = (255, 180, 60)
EDGE_WIDTH     = 3
ARROW_SIZE     = 14
FONT_SIZE      = 13
LABEL_COLOR    = (20, 20, 20)

PANEL_H    = 56
PANEL_BG   = (28, 36, 54)
BTN_W      = 155
BTN_H      = 36
BTN_MARGIN = 10
C_IDLE     = (55, 70, 110)
C_HOVER_B  = (80, 100, 160)
C_ACTIVE   = (60, 160, 120)
C_TEXT     = (220, 230, 255)
C_INFO     = (180, 200, 255)
C_WARN     = (255, 160, 60)

EDGE_HIT_DIST = 18


def fit_image(img_w, img_h, max_w, max_h):
    scale = min(max_w / img_w, max_h / img_h)
    dw = int(img_w * scale)
    dh = int(img_h * scale)
    return (max_w - dw) // 2, (max_h - dh) // 2, dw, dh, scale


def s2i(sx, sy, ox, oy, scale):
    return (sx - ox) / scale, (sy - oy) / scale


def i2s(ix, iy, ox, oy, scale):
    return ox + ix * scale, oy + iy * scale


def dist2(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def pt_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    lsq = dx*dx + dy*dy
    if lsq == 0:
        return dist2(px, py, ax, ay)
    t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / lsq))
    return dist2(px, py, ax + t*dx, ay + t*dy)


def draw_arrow(surface, color, x1, y1, x2, y2, width=3, asize=14):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    ex = x2 - ux * VERTEX_RADIUS
    ey = y2 - uy * VERTEX_RADIUS
    sx = x1 + ux * VERTEX_RADIUS
    sy = y1 + uy * VERTEX_RADIUS
    pygame.draw.line(surface, color, (int(sx), int(sy)), (int(ex), int(ey)), width)
    angle = math.atan2(dy, dx)
    for sign in (1, -1):
        ta = angle + sign * math.radians(150)
        pygame.draw.line(surface, color, (int(ex), int(ey)),
                         (int(ex + asize*math.cos(ta)), int(ey + asize*math.sin(ta))), width)


def button_rect(index):
    return pygame.Rect(BTN_MARGIN + index*(BTN_W+BTN_MARGIN),
                       (PANEL_H - BTN_H) // 2, BTN_W, BTN_H)


def main():
    pygame.init()
    screen   = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Graph Creator")
    clock    = pygame.time.Clock()
    font     = pygame.font.SysFont("monospace", FONT_SIZE, bold=True)
    font_btn = pygame.font.SysFont("sans-serif", 15, bold=True)

    if not os.path.exists(IMAGE_PATH):
        print(f"ERROR: '{IMAGE_PATH}' not found.")
        pygame.quit(); sys.exit(1)

    orig_img       = pygame.image.load(IMAGE_PATH).convert()
    orig_w, orig_h = orig_img.get_size()
    canvas_h       = WINDOW_H - PANEL_H
    canvas_y       = PANEL_H
    ox, oy_rel, disp_w, disp_h, scale = fit_image(orig_w, orig_h, WINDOW_W, canvas_h)
    oy       = canvas_y + oy_rel
    disp_img = pygame.transform.smoothscale(orig_img, (disp_w, disp_h))
    img_rect = pygame.Rect(ox, oy, disp_w, disp_h)

    vertices   = []   # [img_x, img_y, label]
    edges      = []   # [src_idx, dst_idx]
    next_label = 1

    # ── Load ──────────────────────────────────────────────────────────────────
    loaded = False
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH) as f:
                data = json.load(f)
            for v in data.get("vertices", []):
                vertices.append([float(v["x"]), float(v["y"]), str(v["label"])])
            for e in data.get("edges", []):
                edges.append([int(e["from"]), int(e["to"])])
            nums = []
            for v in vertices:
                try: nums.append(int(v[2]))
                except ValueError: pass
            if nums:
                next_label = max(nums) + 1
            loaded = True
            print(f"Loaded V:{len(vertices)} E:{len(edges)} from {SAVE_PATH}")
        except Exception as ex:
            print(f"Warning: could not load {SAVE_PATH}: {ex}")

    # ── Interaction ───────────────────────────────────────────────────────────
    mode         = "none"
    selected     = None
    dragging     = None
    drag_offset  = (0, 0)
    hover_vertex = None
    hover_edge   = None
    status_msg   = f"Graph loaded ({len(vertices)}V, {len(edges)}E)." if loaded else "New graph."
    status_timer = 0

    def set_status(msg, duration=3000):
        nonlocal status_msg, status_timer
        status_msg   = msg
        status_timer = pygame.time.get_ticks() + duration

    def nearest_vertex(sx, sy, max_d=VERTEX_RADIUS+6):
        best, bd = None, max_d
        for i, v in enumerate(vertices):
            d = dist2(sx, sy, *i2s(v[0], v[1], ox, oy, scale))
            if d < bd: best, bd = i, d
        return best

    def nearest_edge_idx(sx, sy, max_d=EDGE_HIT_DIST):
        best, bd = None, max_d
        for i, (a, b) in enumerate(edges):
            ax2, ay2 = i2s(vertices[a][0], vertices[a][1], ox, oy, scale)
            bx2, by2 = i2s(vertices[b][0], vertices[b][1], ox, oy, scale)
            d = pt_seg_dist(sx, sy, ax2, ay2, bx2, by2)
            if d < bd: best, bd = i, d
        return best

    def delete_vertex(idx):
        nonlocal selected, dragging
        vertices.pop(idx)
        new_edges = []
        for a, b in edges:
            if a == idx or b == idx: continue
            new_edges.append([a-(1 if a>idx else 0), b-(1 if b>idx else 0)])
        edges[:] = new_edges
        if selected == idx: selected = None
        elif selected is not None and selected > idx: selected -= 1
        if dragging == idx: dragging = None
        elif dragging is not None and dragging > idx: dragging -= 1

    def save_graph():
        data = {
            "image": IMAGE_PATH,
            "original_size": [orig_w, orig_h],
            "vertices": [{"id":i,"label":v[2],"x":round(v[0],4),"y":round(v[1],4)}
                         for i,v in enumerate(vertices)],
            "edges":    [{"from":a,"to":b,
                          "from_label":vertices[a][2],"to_label":vertices[b][2]}
                         for a,b in edges],
        }
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved → {SAVE_PATH}  (V:{len(vertices)} E:{len(edges)})")

    buttons = [
        {"label": "Add Vertex  [A]",  "mode": "add_vertex"},
        {"label": "Connect     [C]",  "mode": "connect"},
        {"label": "Del Edge    [D]",  "mode": "delete_edge"},
        {"label": "Move        [M]",  "mode": "move"},
    ]
    mode_status = {
        "add_vertex":  "Add Vertex — click on the map.",
        "connect":     "Connect — click source, then destination.",
        "delete_edge": "Delete Edge — click near an edge to remove it.",
        "move":        "Move — drag a vertex to reposition.",
    }

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        hover_vertex = nearest_vertex(mx, my)
        hover_edge   = nearest_edge_idx(mx, my) if mode == "delete_edge" else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if   k == pygame.K_ESCAPE: mode="none"; selected=None; dragging=None; set_status("Mode cleared.")
                elif k == pygame.K_a:      mode="add_vertex";  selected=None; dragging=None; set_status(mode_status["add_vertex"])
                elif k == pygame.K_c:      mode="connect";     selected=None; dragging=None; set_status(mode_status["connect"])
                elif k == pygame.K_d:      mode="delete_edge"; selected=None; dragging=None; set_status(mode_status["delete_edge"])
                elif k == pygame.K_m:      mode="move";        selected=None; dragging=None; set_status(mode_status["move"])

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # toolbar
                if my < PANEL_H:
                    for i, btn in enumerate(buttons):
                        if button_rect(i).collidepoint(mx, my):
                            mode = btn["mode"]; selected=None; dragging=None
                            set_status(mode_status.get(mode, ""))
                    continue

                # right-click → delete vertex
                if event.button == 3:
                    if hover_vertex is not None:
                        lbl = vertices[hover_vertex][2]
                        delete_vertex(hover_vertex)
                        set_status(f"Deleted vertex '{lbl}'.")
                    continue

                if event.button != 1:
                    continue

                if mode == "add_vertex":
                    if img_rect.collidepoint(mx, my):
                        ix, iy = s2i(mx, my, ox, oy, scale)
                        lbl = str(next_label); next_label += 1
                        vertices.append([ix, iy, lbl])
                        set_status(f"Added vertex '{lbl}'.")
                    else:
                        set_status("⚠ Click inside the image.", 2000)

                elif mode == "connect":
                    if hover_vertex is not None:
                        if selected is None:
                            selected = hover_vertex
                            set_status(f"'{vertices[selected][2]}' — now click target.")
                        else:
                            src, dst = selected, hover_vertex; selected = None
                            if src == dst:
                                set_status("Cannot connect vertex to itself.", 2000)
                            elif [src, dst] in edges:
                                set_status("Edge already exists.", 2000)
                            else:
                                edges.append([src, dst])
                                set_status(f"Edge '{vertices[src][2]}' → '{vertices[dst][2]}'.")
                    else:
                        selected = None
                        set_status("No vertex there — click a vertex.")

                elif mode == "delete_edge":
                    if hover_edge is not None:
                        a, b = edges[hover_edge]
                        edges.pop(hover_edge)
                        set_status(f"Deleted edge '{vertices[a][2]}' → '{vertices[b][2]}'.")
                    else:
                        set_status("No edge nearby — click closer to an edge.", 2000)

                elif mode == "move":
                    if hover_vertex is not None:
                        dragging = hover_vertex
                        vsx, vsy = i2s(vertices[hover_vertex][0], vertices[hover_vertex][1], ox, oy, scale)
                        drag_offset = (vsx - mx, vsy - my)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and dragging is not None:
                    tx = max(ox, min(ox+disp_w, mx+drag_offset[0]))
                    ty = max(oy, min(oy+disp_h, my+drag_offset[1]))
                    ix, iy = s2i(tx, ty, ox, oy, scale)
                    vertices[dragging][0] = ix
                    vertices[dragging][1] = iy
                    set_status(f"Moved '{vertices[dragging][2]}' → ({ix:.1f}, {iy:.1f}).")
                    dragging = None

            elif event.type == pygame.MOUSEMOTION:
                if dragging is not None:
                    tx = max(ox, min(ox+disp_w, mx+drag_offset[0]))
                    ty = max(oy, min(oy+disp_h, my+drag_offset[1]))
                    ix, iy = s2i(tx, ty, ox, oy, scale)
                    vertices[dragging][0] = ix
                    vertices[dragging][1] = iy

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill((15, 20, 35))
        screen.blit(disp_img, (ox, oy))
        pygame.draw.rect(screen, (80, 100, 150), img_rect, 2)

        for i, (a, b) in enumerate(edges):
            ax2, ay2 = i2s(vertices[a][0], vertices[a][1], ox, oy, scale)
            bx2, by2 = i2s(vertices[b][0], vertices[b][1], ox, oy, scale)
            highlighted = (mode == "delete_edge" and i == hover_edge)
            col = EDGE_HOV_COLOR if highlighted else EDGE_COLOR
            w   = EDGE_WIDTH + 2 if highlighted else EDGE_WIDTH
            draw_arrow(screen, col, ax2, ay2, bx2, by2, w, ARROW_SIZE)
            if highlighted:
                mid_x, mid_y = int((ax2+bx2)/2), int((ay2+by2)/2)
                r = 8
                pygame.draw.line(screen,(255,60,60),(mid_x-r,mid_y-r),(mid_x+r,mid_y+r),3)
                pygame.draw.line(screen,(255,60,60),(mid_x+r,mid_y-r),(mid_x-r,mid_y+r),3)

        if mode == "connect" and selected is not None:
            ax2, ay2 = i2s(vertices[selected][0], vertices[selected][1], ox, oy, scale)
            pygame.draw.line(screen, SELECTED_COLOR, (int(ax2), int(ay2)), (mx, my), 2)

        for i, v in enumerate(vertices):
            sx2, sy2 = i2s(v[0], v[1], ox, oy, scale)
            isx, isy = int(sx2), int(sy2)
            if   i == dragging:      col = DRAG_COLOR
            elif i == selected:      col = SELECTED_COLOR
            elif i == hover_vertex:  col = HOVER_COLOR
            else:                    col = VERTEX_COLOR
            pygame.draw.circle(screen, col, (isx,isy), VERTEX_RADIUS)
            pygame.draw.circle(screen, VERTEX_BORDER, (isx,isy), VERTEX_RADIUS, 2)
            lbl = font.render(v[2], True, LABEL_COLOR)
            screen.blit(lbl, (isx - lbl.get_width()//2, isy - lbl.get_height()//2))

        # toolbar
        pygame.draw.rect(screen, PANEL_BG, (0, 0, WINDOW_W, PANEL_H))
        pygame.draw.line(screen, (60,80,130), (0, PANEL_H-1), (WINDOW_W, PANEL_H-1), 1)
        for i, btn in enumerate(buttons):
            r   = button_rect(i)
            act = (mode == btn["mode"])
            hov = r.collidepoint(mx, my) and my < PANEL_H
            col = C_ACTIVE if act else (C_HOVER_B if hov else C_IDLE)
            pygame.draw.rect(screen, col, r, border_radius=6)
            pygame.draw.rect(screen, (80,100,160), r, 1, border_radius=6)
            txt = font_btn.render(btn["label"], True, C_TEXT)
            screen.blit(txt, (r.x+(BTN_W-txt.get_width())//2, r.y+(BTN_H-txt.get_height())//2))

        info_x = BTN_MARGIN + len(buttons)*(BTN_W+BTN_MARGIN)
        now = pygame.time.get_ticks()
        if now < status_timer or status_timer == 0:
            scol = C_WARN if "⚠" in status_msg else C_INFO
            surf = font_btn.render(status_msg, True, scol)
            screen.blit(surf, (info_x, (PANEL_H-surf.get_height())//2))

        ct = font_btn.render(f"V:{len(vertices)}  E:{len(edges)}", True, (130,150,200))
        screen.blit(ct, (WINDOW_W-ct.get_width()-12, (PANEL_H-ct.get_height())//2))

        pygame.display.flip()
        clock.tick(FPS)

    save_graph()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()