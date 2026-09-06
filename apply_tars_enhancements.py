from pathlib import Path
import re

def read(path):
    return Path(path).read_text()

def write(path, text):
    Path(path).write_text(text)

path = "src/AircraftManager.cpp"
text = read(path)

if "Invalid/missing radar radius; using safe default 0.2 deg" not in text:
    pattern = r'(^\s*rad\s*=\s*configServer\.GetStoredString\("radius"\)\.toDouble\(\);\s*$)'
    repl = r'''\1
    if (!isfinite(rad) || rad <= 0.0001)
    {
        rad = 0.2;
        Serial.println("[WARN] Invalid/missing radar radius; using safe default 0.2 deg");
    }'''
    text, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit("Could not locate radius configuration assignment in AircraftManager.cpp")
    print("Applied: safe radius fallback")
else:
    print("Already applied: safe radius fallback")

start = text.find("void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const")
end = text.find("\nstd::pair<int, int> AircraftManager::ProjectCoordinateToScreen", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate DrawRadarCircles() in AircraftManager.cpp")

new_draw = r'''void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const
{
    constexpr int CENTRE = SCREEN_SIZE_DIV_2 - 1;
    constexpr int OUTER = SCREEN_SIZE_DIV_2 - 5;

    backbuffer.drawCircle(CENTRE, CENTRE, OUTER, lgfx::color888(0, 200, 0));
    backbuffer.drawCircle(CENTRE, CENTRE, (OUTER / 3) * 2, lgfx::color888(0, 64, 0));
    backbuffer.drawCircle(CENTRE, CENTRE, OUTER / 3, lgfx::color888(0, 32, 0));

    backbuffer.setTextSize(1);
    backbuffer.setTextColor(lgfx::color888(0, 220, 0));

    backbuffer.setTextDatum(textdatum_t::top_center);
    backbuffer.drawString("N", CENTRE, 4);

    backbuffer.setTextDatum(textdatum_t::middle_right);
    backbuffer.drawString("E", SCREEN_SIZE - 4, CENTRE);

    const float safeRad = max((float)rad, 0.0001f);
    const float rangeKm = safeRad * 111.32f;

    char rangeText[20];
    snprintf(rangeText, sizeof(rangeText), "R %.1f km", rangeKm);

    backbuffer.setTextDatum(textdatum_t::bottom_center);
    backbuffer.drawString(rangeText, CENTRE, SCREEN_SIZE - 4);

    backbuffer.setTextDatum(textdatum_t::top_left);
}
'''
text = text[:start] + new_draw + text[end:]
print("Applied: N/E/range display")

start = text.find("std::pair<int, int> AircraftManager::ProjectCoordinateToScreen")
end = text.find("\nvoid AircraftManager::DrawAircraftInfo", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate ProjectCoordinateToScreen() in AircraftManager.cpp")

new_proj = r'''std::pair<int, int> AircraftManager::ProjectCoordinateToScreen(float predLat, float predLon) const
{
    const float dLon = predLon - lon;
    const float dLat = predLat - lat;
    const float safeRad = max((float)rad, 0.0001f);

    const float normLon = (dLon + safeRad) / (2.0f * safeRad);
    const float normLat = (dLat + safeRad) / (2.0f * safeRad);

    const int x = static_cast<int>(normLon * SCREEN_SIZE);
    const int y = static_cast<int>(SCREEN_SIZE - (normLat * SCREEN_SIZE));

    return {x, y};
}
'''
text = text[:start] + new_proj + text[end:]
print("Applied: stock projection with safety clamp")

for func in ["ZoomIn", "ZoomOut", "ResetZoom"]:
    pattern = rf'\nvoid AircraftManager::{func}\(\)\s*\{{.*?\n\}}\n'
    text, _ = re.subn(pattern, "\n", text, count=1, flags=re.DOTALL)

write(path, text)

hpath = "src/AircraftManager.h"
h = read(hpath)
h = re.sub(r'^\s*int zoomIndex\s*=\s*0;\s*\n', '', h, flags=re.MULTILINE)
for decl in ["void ZoomIn();", "void ZoomOut();", "void ResetZoom();"]:
    h = re.sub(r'^\s*' + re.escape(decl) + r'\s*\n', '', h, flags=re.MULTILINE)
write(hpath, h)

print("Removed: all zoom state/method declarations")
print("TARS Recovery v1 source changes applied successfully.")
