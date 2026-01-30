"""Generate an icon file for the system tray."""

from PIL import Image, ImageDraw


def create_icon():
    """Create a simple clipboard/image icon."""
    size = 256  # Create at higher resolution for quality
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # Scale factor
    s = size / 64

    # Background rounded rectangle (clipboard)
    draw.rounded_rectangle(
        [int(8*s), int(4*s), int(56*s), int(60*s)],
        radius=int(6*s),
        fill=(70, 130, 180),  # Steel blue
        outline=(50, 100, 150),
        width=int(2*s)
    )

    # Clipboard clip at top
    draw.rounded_rectangle(
        [int(22*s), int(0*s), int(42*s), int(12*s)],
        radius=int(3*s),
        fill=(100, 160, 210),
        outline=(50, 100, 150),
        width=int(2*s)
    )

    # Image icon in center (white background)
    draw.rectangle(
        [int(16*s), int(20*s), int(48*s), int(48*s)],
        fill=(255, 255, 255),
        outline=(200, 200, 200),
        width=int(1*s)
    )

    # Sun
    draw.ellipse(
        [int(36*s), int(24*s), int(44*s), int(32*s)],
        fill=(255, 200, 50)
    )

    # Mountains
    draw.polygon(
        [(int(18*s), int(46*s)), (int(28*s), int(32*s)), (int(38*s), int(46*s))],
        fill=(100, 180, 100)
    )
    draw.polygon(
        [(int(30*s), int(46*s)), (int(40*s), int(36*s)), (int(46*s), int(46*s))],
        fill=(80, 150, 80)
    )

    # Save as ICO with multiple sizes
    icon.save('icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print("Icon created: icon.ico")


if __name__ == "__main__":
    create_icon()
