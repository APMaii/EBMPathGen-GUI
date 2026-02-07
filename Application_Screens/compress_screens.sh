#!/bin/bash
# Reduce image file size in Application_Screens.
#
# Option A - Convert to JPEG (best size reduction, good for screenshots):
#   ./compress_screens.sh jpeg [quality]
#   Example: ./compress_screens.sh jpeg 82
#   Creates .jpg versions; delete .png if you don't need them.
#
# Option B - Scale PNG (resize to % of original; may re-encode):
#   ./compress_screens.sh scale [percent]
#   Example: ./compress_screens.sh scale 60

DIR="$(cd "$(dirname "$0")" && pwd)"
mode="${1:-jpeg}"
arg="${2:-82}"

case "$mode" in
  jpeg)
    quality="${arg}"
    echo "Converting PNGs to JPEG (quality ${quality})..."
    for f in "$DIR"/*.png; do
      [ -f "$f" ] || continue
      out="${f%.png}.jpg"
      before=$(stat -f %z "$f" 2>/dev/null)
      sips -s format jpeg -s formatOptions "$quality" "$f" --out "$out"
      after=$(stat -f %z "$out" 2>/dev/null)
      echo "  $(basename "$f") → $(basename "$out"): $(( before / 1024 ))KB → $(( after / 1024 ))KB"
    done
    echo "Done. JPEGs created. Remove .png if you only want the smaller files."
    ;;
  scale)
    scale="${arg}"
    echo "Scaling PNGs to ${scale}%..."
    for f in "$DIR"/*.png; do
      [ -f "$f" ] || continue
      name=$(basename "$f")
      before=$(stat -f %z "$f" 2>/dev/null)
      w=$(sips -g pixelWidth "$f" | awk '/pixelWidth/{print $2}')
      h=$(sips -g pixelHeight "$f" | awk '/pixelHeight/{print $2}')
      max=$(( w > h ? w : h ))
      new=$(( max * scale / 100 ))
      [ "$new" -lt 1 ] && new=1
      sips -Z "$new" "$f"
      after=$(stat -f %z "$f" 2>/dev/null)
      echo "  $name: $(( before / 1024 ))KB → $(( after / 1024 ))KB"
    done
    echo "Done."
    ;;
  *)
    echo "Usage: $0 jpeg [quality]  OR  $0 scale [percent]"
    echo "  jpeg 82  - convert to JPEG quality 82 (default, good size/quality)"
    echo "  scale 60 - resize PNGs to 60%"
    exit 1
    ;;
esac
