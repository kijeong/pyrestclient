import sys
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication
import PySide6.QtSvg  # Ensure SVG support

def convert_icon():
    app = QApplication(sys.argv)
    
    base_dir = Path(__file__).resolve().parent.parent
    svg_path = base_dir / "resources" / "icons" / "app_icon.svg"
    png_path = base_dir / "resources" / "icons" / "app_icon.png"
    ico_path = base_dir / "resources" / "icons" / "app_icon.ico"
    
    if not svg_path.exists():
        print(f"Error: {svg_path} not found")
        sys.exit(1)
        
    print(f"Converting {svg_path}...")
    
    # Create icon from SVG
    icon = QIcon(str(svg_path))
    
    # Save as PNG (64x64)
    pixmap = icon.pixmap(64, 64)
    if pixmap.save(str(png_path), "PNG"):
        print(f"Saved {png_path}")
    else:
        print(f"Failed to save {png_path}")

    # Save as ICO (requires specific handling or just save pixmap as ico if supported)
    # Qt supports writing ICO if the plugin is available, but usually it is.
    # For ICO, we might want multiple sizes, but let's just try basic first.
    if pixmap.save(str(ico_path), "ICO"):
        print(f"Saved {ico_path}")
    else:
        print(f"Failed to save {ico_path}")

if __name__ == "__main__":
    convert_icon()
