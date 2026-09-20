import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


   
# UNIT CONVERSION
   

def feet_to_cm(feet):
    """Convert feet to centimeters."""
    return float(feet) * 30.48


   
# LAYOUT HELPERS
   

MIN_CLEARANCE = 45       # cm between major fixtures
WALL_MARGIN = 25         # cm from walls
DOOR_WIDTH = 80          # cm
DOOR_OFFSET = 100        # cm from right wall
ENTRY_CLEARANCE = 80    # cm kept clear inside the entrance


def _rect(x, y, width, depth):
    """Return a fixture rectangle as (x1, y1, x2, y2)."""
    return (
        float(x),
        float(y),
        float(x) + float(width),
        float(y) + float(depth),
    )


def _overlaps(a, b, clearance=MIN_CLEARANCE):
    """Check whether two rectangles overlap after adding clearance."""
    return not (
        a[2] + clearance <= b[0]
        or b[2] + clearance <= a[0]
        or a[3] + clearance <= b[1]
        or b[3] + clearance <= a[1]
    )


def _inside_room(rect, room_width, room_depth, margin=WALL_MARGIN):
    """Check whether a fixture is safely inside the room."""
    return (
        rect[0] >= margin
        and rect[1] >= margin
        and rect[2] <= room_width - margin
        and rect[3] <= room_depth - margin
    )


def _in_entry_zone(rect, room_width):
    """
    Bottom-right entrance zone.

    The door is on the bottom-right wall. Keep the immediate
    walking/entry area clear of major fixtures.
    """
    door_x = room_width - DOOR_OFFSET
    entry_zone = (
        door_x - 35,
        0,
        room_width - WALL_MARGIN,
        ENTRY_CLEARANCE,
    )
    return _overlaps(rect, entry_zone, clearance=0)


def _can_place(rect, placed, room_width, room_depth, protect_entry=True):
    """Validate room bounds, fixture clearance and entry clearance."""
    if not _inside_room(rect, room_width, room_depth):
        return False

    for existing in placed:
        if _overlaps(rect, existing):
            return False

    if protect_entry and _in_entry_zone(rect, room_width):
        return False

    return True


def _fit_options(product, room_width, room_depth):
    """
    Return all catalog orientations that fit inside the room.
    Normal orientation is listed first; the rotated orientation
    is also available so the placement logic can choose the
    arrangement that preserves usable circulation.
    """
    width = float(product["width_cm"])
    depth = float(product["depth_cm"])

    options = []

    if (
        width <= room_width - 2 * WALL_MARGIN
        and depth <= room_depth - 2 * WALL_MARGIN
    ):
        options.append((width, depth, False))

    if (
        depth <= room_width - 2 * WALL_MARGIN
        and width <= room_depth - 2 * WALL_MARGIN
        and (depth, width, True) not in options
    ):
        options.append((depth, width, True))

    return options


def _find_position(
    width,
    depth,
    candidates,
    placed,
    room_width,
    room_depth,
    protect_entry=True,
):
    """
    Choose a sensible position.

    Preferred positions are tried first. If none work, a coarse
    room scan finds the first valid position. This makes the
    layout robust to different catalog product dimensions.
    """
    for x, y in candidates:
        rect = _rect(x, y, width, depth)

        if _can_place(
            rect,
            placed,
            room_width,
            room_depth,
            protect_entry=protect_entry,
        ):
            return x, y, rect

    # Robust fallback: scan from the far end of the room toward
    # the entrance, preserving the same clearance rules.
    step = 10

    max_x = room_width - WALL_MARGIN - width
    max_y = room_depth - WALL_MARGIN - depth

    if max_x < WALL_MARGIN or max_y < WALL_MARGIN:
        return None

    y = max_y
    while y >= WALL_MARGIN:
        x = WALL_MARGIN

        while x <= max_x:
            rect = _rect(x, y, width, depth)

            if _can_place(
                rect,
                placed,
                room_width,
                room_depth,
                protect_entry=protect_entry,
            ):
                return x, y, rect

            x += step

        y -= step

    return None


   
# DOOR
   

def draw_door(ax, bathroom_width, bathroom_depth):
    """Draw the existing bottom-right door without a swing arc."""
    door_x = bathroom_width - DOOR_OFFSET

    # Door opening
    ax.plot(
        [door_x, door_x + DOOR_WIDTH],
        [0, 0],
        linewidth=7,
        color="white",
        solid_capstyle="butt",
        zorder=5,
    )

    # Door panel
    ax.plot(
        [door_x, door_x],
        [0, DOOR_WIDTH],
        linewidth=2,
        color="black",
        zorder=6,
    )

    ax.text(
        door_x + DOOR_WIDTH / 2,
        -18,
        "DOOR / ENTRY",
        ha="center",
        va="top",
        fontsize=9,
        zorder=7,
    )


   
# DRAW PRODUCT
   

def draw_product(ax, product, x, y, rotation=False):
    """Draw a simplified product footprint using catalog dimensions."""
    category = str(product["category"])

    width = float(product["width_cm"])
    depth = float(product["depth_cm"])

    if rotation:
        width, depth = depth, width

    rect = Rectangle(
        (x, y),
        width,
        depth,
        alpha=0.6,
        edgecolor="black",
        linewidth=1.5,
    )

    ax.add_patch(rect)

    # Keep the vanity label away from the faucet marker.
    label_y = y + depth / 2

    if category == "Vanity":
        label_y = y + depth * 0.20

    ax.text(
        x + width / 2,
        label_y,
        category,
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        wrap=True,
    )

    return width, depth


   
# CREATE LAYOUT
   

def create_layout(
    bathroom_width_ft,
    bathroom_depth_ft,
    products,
):
    """
    Create an entrance-aware 2D bathroom layout.

    Design rules:
      - Uses actual catalog width/depth values.
      - Keeps major fixtures separated by MIN_CLEARANCE.
      - Protects the bottom-right entrance area.
      - Uses fixed bathroom zones first, then safe candidate positions.
      - Keeps faucet attached to the vanity.
      - Adds room dimensions, product dimensions and a legend.
      - Product shapes are schematic; dimensions are based on the catalog.
    """

    if bathroom_width_ft <= 0 or bathroom_depth_ft <= 0:
        raise ValueError("Bathroom dimensions must be greater than zero.")

    if products is None or products.empty:
        raise ValueError("No recommended products are available for the layout.")

    required_columns = {"category", "width_cm", "depth_cm"}
    missing = required_columns - set(products.columns)

    if missing:
        raise ValueError(
            "Layout data is missing required columns: "
            + ", ".join(sorted(missing))
        )

    bathroom_width = feet_to_cm(bathroom_width_ft)
    bathroom_depth = feet_to_cm(bathroom_depth_ft)

    if bathroom_width <= 2 * WALL_MARGIN or bathroom_depth <= 2 * WALL_MARGIN:
        raise ValueError("Bathroom is too small for the layout margins.")

    # First product for each category, matching the current behavior.
    products_by_category = {}

    for _, product in products.iterrows():
        category = str(product["category"])
        if category not in products_by_category:
            products_by_category[category] = product

    fig, ax = plt.subplots(figsize=(10, 7))

    # -----------------------------------------------------
    # BATHROOM WALLS
    # -----------------------------------------------------

    bathroom = Rectangle(
        (0, 0),
        bathroom_width,
        bathroom_depth,
        fill=False,
        linewidth=3,
        edgecolor="black",
    )
    ax.add_patch(bathroom)

    draw_door(ax, bathroom_width, bathroom_depth)

    placed = []
    placed_info = {}

    # -----------------------------------------------------
    # SHOWER — FAR TOP-LEFT ZONE
    # -----------------------------------------------------

    if "Shower" in products_by_category:
        product = products_by_category["Shower"]

        for width, depth, rotation in _fit_options(
            product, bathroom_width, bathroom_depth
        ):
            candidates = [
                # Preferred: far top-left.
                (
                    WALL_MARGIN,
                    bathroom_depth - WALL_MARGIN - depth,
                ),
                # Alternative upper-middle position.
                (
                    bathroom_width / 2 - width / 2,
                    bathroom_depth - WALL_MARGIN - depth,
                ),
                # Lower-left fallback.
                (
                    WALL_MARGIN,
                    bathroom_depth * 0.68,
                ),
            ]

            found = _find_position(
                width,
                depth,
                candidates,
                placed,
                bathroom_width,
                bathroom_depth,
            )

            if found:
                x, y, rect = found
                draw_product(
                    ax,
                    product,
                    x,
                    y,
                    rotation=rotation,
                )
                placed.append(rect)
                placed_info["Shower"] = (
                    x, y, width, depth, product, rotation
                )
                break

    # -----------------------------------------------------
    # VANITY : TOP-RIGHT ZONE
    # -----------------------------------------------------

    if "Vanity" in products_by_category:
        product = products_by_category["Vanity"]

        for width, depth, rotation in _fit_options(
            product, bathroom_width, bathroom_depth
        ):
            candidates = [
                # Preferred: upper-right. Rotation is automatically
                # considered if the normal orientation is too wide.
                (
                    bathroom_width - WALL_MARGIN - width,
                    bathroom_depth - WALL_MARGIN - depth,
                ),
                (
                    bathroom_width - WALL_MARGIN - width,
                    bathroom_depth * 0.62,
                ),
                (
                    bathroom_width * 0.52,
                    bathroom_depth - WALL_MARGIN - depth,
                ),
                (
                    bathroom_width - WALL_MARGIN - width,
                    bathroom_depth * 0.48,
                ),
            ]

            found = _find_position(
                width,
                depth,
                candidates,
                placed,
                bathroom_width,
                bathroom_depth,
            )

            if found:
                x, y, rect = found
                draw_product(
                    ax,
                    product,
                    x,
                    y,
                    rotation=rotation,
                )
                placed.append(rect)
                placed_info["Vanity"] = (
                    x, y, width, depth, product, rotation
                )
                break

    # -----------------------------------------------------
    # TOILET — AWAY FROM ENTRANCE SIGHTLINE
    # -----------------------------------------------------

    if "Toilet" in products_by_category:
        product = products_by_category["Toilet"]

        for width, depth, rotation in _fit_options(
            product, bathroom_width, bathroom_depth
        ):
            candidates = [
                # Left-middle zone.
                (
                    WALL_MARGIN,
                    bathroom_depth * 0.38 - depth / 2,
                ),
                (
                    WALL_MARGIN,
                    bathroom_depth * 0.50 - depth / 2,
                ),
                # Middle-left / middle zone.
                (
                    bathroom_width * 0.30 - width / 2,
                    bathroom_depth * 0.40 - depth / 2,
                ),
                (
                    bathroom_width * 0.42 - width / 2,
                    bathroom_depth * 0.48 - depth / 2,
                ),
                # Last-resort central position, still protected from entry.
                (
                    bathroom_width * 0.50 - width / 2,
                    bathroom_depth * 0.35,
                ),
            ]

            found = _find_position(
                width,
                depth,
                candidates,
                placed,
                bathroom_width,
                bathroom_depth,
            )

            if found:
                x, y, rect = found
                draw_product(
                    ax,
                    product,
                    x,
                    y,
                    rotation=rotation,
                )
                placed.append(rect)
                placed_info["Toilet"] = (
                    x, y, width, depth, product, rotation
                )
                break

    # -----------------------------------------------------
    # FAUCET — ON VANITY
    # -----------------------------------------------------

    if "Faucet" in products_by_category and "Vanity" in placed_info:
        vanity_x, vanity_y, vanity_width, vanity_depth, _, _ = placed_info["Vanity"]

        faucet_width = min(8, vanity_width * 0.25)
        faucet_depth = min(8, vanity_depth * 0.25)

        faucet_x = (
            vanity_x
            + vanity_width / 2
            - faucet_width / 2
        )
        faucet_y = (
            vanity_y
            + vanity_depth * 0.68
            - faucet_depth / 2
        )

        faucet_rect = Rectangle(
            (faucet_x, faucet_y),
            faucet_width,
            faucet_depth,
            facecolor="white",
            edgecolor="black",
            linewidth=1.5,
            zorder=5,
        )

        ax.add_patch(faucet_rect)

        ax.text(
            faucet_x + faucet_width / 2,
            faucet_y + faucet_depth / 2,
            "F",
            ha="center",
            va="center",
            fontsize=7,
            zorder=6,
        )

    # -----------------------------------------------------
    # ROOM DIMENSIONS
    # -----------------------------------------------------

    ax.text(
        bathroom_width / 2,
        -35,
        f"{bathroom_width_ft:g} ft",
        ha="center",
        va="top",
        fontsize=10,
        fontweight="bold",
    )

    ax.text(
        -25,
        bathroom_depth / 2,
        f"{bathroom_depth_ft:g} ft",
        ha="right",
        va="center",
        rotation=90,
        fontsize=10,
        fontweight="bold",
    )

    # -----------------------------------------------------
    # LEGEND
    # -----------------------------------------------------

    legend_lines = [
        "SCHEMATIC LAYOUT",
        "Product shapes simplified; dimensions from catalog",
        f"Fixture clearance: ≥ {MIN_CLEARANCE} cm",
        f"Entry clearance protected: {ENTRY_CLEARANCE} cm",
    ]

    for category in ["Shower", "Vanity", "Toilet"]:
        if category in placed_info:
            _, _, width, depth, product, rotation = placed_info[category]
            legend_lines.append(
                f"{category}: {width:.0f} × {depth:.0f} cm"
            )

    legend_text = "\n".join(legend_lines)

    ax.text(
        bathroom_width + 35,
        bathroom_depth * 0.48,
        legend_text,
        ha="left",
        va="center",
        fontsize=8,
        linespacing=1.5,
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor="white",
            edgecolor="black",
            alpha=0.9,
        ),
    )

    # -----------------------------------------------------
    # GRAPH SETTINGS
    # -----------------------------------------------------

    ax.set_xlim(-50, bathroom_width + 190)
    ax.set_ylim(-60, bathroom_depth + 40)
    ax.set_aspect("equal")

    ax.set_title(
        f"AI Bathroom Layout — "
        f"{bathroom_width_ft:g} ft × "
        f"{bathroom_depth_ft:g} ft",
        fontsize=14,
        fontweight="bold",
    )

    ax.axis("off")
    plt.tight_layout()

    return fig
