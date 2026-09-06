from pathlib import Path
import re


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def sub_once(path, pattern, replacement, label, marker):
    text = read(path)
    if marker in text:
        print(f"Already applied: {label}")
        return
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count == 0:
        raise SystemExit(f"Could not apply {label} in {path}")
    write(path, new_text)
    print(f"Applied: {label}")

# AircraftManager.h
sub_once(
    "src/AircraftManager.h",
    r'^(\s*double rad = 0\.2;\s*)$',
    r'\1\n    int zoomIndex = 0;',
    "zoomIndex",
    "int zoomIndex = 0;"
)

sub_once(
    "src/AircraftManager.h",
    r'^(\s*void EncoderClick\(\);\s*)$',
    r'\1\n    void ZoomIn();\n    void ZoomOut();\n    void ResetZoom();',
    "zoom declarations",
    "void ZoomIn();"
)

# AircraftManager.cpp: protect against missing/zero stored radius.
sub_once(
    "src/AircraftManager.cpp",
    r'^(\s*rad = configServer\.GetStoredString\("radius"\)\.toDouble\(\);\s*)$',
    r'\1\n    if (!isfinite(rad) || rad <= 0.0001)\n    {\n        rad = 0.2;\n        Serial.println("[WARN] Invalid/missing radar radius; using safe default 0.2 deg");\n    }',
    "radius safety",
    'Invalid/missing radar radius'
)

# AircraftManager.cpp: constants
sub_once(
    "src/AircraftManager.cpp",
    r'^(constexpr int SCREEN_SIZE_DIV_2 = \(SCREEN_SIZE / 2\);)\s*$',
    r'\1\n\nstatic constexpr float ZOOM_FACTORS[] = {1.0f, 0.5f, 0.25f, 0.10f};\nstatic constexpr int ZOOM_LEVEL_COUNT =\n    sizeof(ZOOM_FACTORS) / sizeof(ZOOM_FACTORS[0]);',
    "zoom constants",
    "ZOOM_FACTORS[]"
)

# Replace DrawRadarCircles body.
text = read("src/AircraftManager.cpp")
if 'drawString("N"' not in text:
    start = text.find("void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const")
    end = text.find("\nstd::pair<int, int> AircraftManager::ProjectCoordinateToScreen", start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate DrawRadarCircles()")
    new_func = '''void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const
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

    const float displayRadiusDeg = max((float)(rad * ZOOM_FACTORS[zoomIndex]), 0.0001f);
    const float displayRadiusKm = displayRadiusDeg * 111.32f;

    char rangeText[20];
    snprintf(rangeText, sizeof(rangeText), "R %.1f km", displayRadiusKm);

    backbuffer.setTextDatum(textdatum_t::bottom_center);
    backbuffer.drawString(rangeText, CENTRE, SCREEN_SIZE - 4);
    backbuffer.setTextDatum(textdatum_t::top_left);
}
'''
    text = text[:start] + new_func + text[end:]
    write("src/AircraftManager.cpp", text)
    print("Applied: radar labels")
else:
    print("Already applied: radar labels")

# Replace projection function and append zoom methods.
text = read("src/AircraftManager.cpp")
if "const float displayRad = max((float)(rad * ZOOM_FACTORS[zoomIndex]), 0.0001f);" not in text:
    start = text.find("std::pair<int, int> AircraftManager::ProjectCoordinateToScreen")
    end = text.find("\nvoid AircraftManager::DrawAircraftInfo", start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate ProjectCoordinateToScreen()")
    new_block = '''std::pair<int, int> AircraftManager::ProjectCoordinateToScreen(float predLat, float predLon) const
{
    const float dLon = predLon - lon;
    const float dLat = predLat - lat;
    const float displayRad = max((float)(rad * ZOOM_FACTORS[zoomIndex]), 0.0001f);

    const float normLon = (dLon + displayRad) / (2.0f * displayRad);
    const float normLat = (dLat + displayRad) / (2.0f * displayRad);

    const int x = static_cast<int>(normLon * SCREEN_SIZE);
    const int y = static_cast<int>(SCREEN_SIZE - (normLat * SCREEN_SIZE));

    return {x, y};
}

void AircraftManager::ZoomIn()
{
    if (currentScreen != SCREEN_RADAR)
        return;
    if (zoomIndex < ZOOM_LEVEL_COUNT - 1)
        ++zoomIndex;
}

void AircraftManager::ZoomOut()
{
    if (currentScreen != SCREEN_RADAR)
        return;
    if (zoomIndex > 0)
        --zoomIndex;
}

void AircraftManager::ResetZoom()
{
    if (currentScreen != SCREEN_RADAR)
        return;
    zoomIndex = 0;
}
'''
    text = text[:start] + new_block + text[end:]
    write("src/AircraftManager.cpp", text)
    print("Applied: projection")
else:
    print("Already applied: projection")

# main.cpp: replace only the encoder/button section at top of loop.
text = read("src/main.cpp")
if "buttonUsedForZoom" not in text:
    start = text.find("void loop()\n{")
    marker = "  SetLed(0, 255, 255); // Fetching"
    end = text.find(marker, start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate loop encoder/button section")
    new_prefix = '''void loop()
{
  static bool lastButtonState = HIGH;
  static unsigned long buttonDownAt = 0;
  static bool buttonUsedForZoom = false;
  static bool longPressHandled = false;

  bool currentButtonState = digitalRead(ENCODER_SW);

  if (lastButtonState == HIGH && currentButtonState == LOW)
  {
    buttonDownAt = millis();
    buttonUsedForZoom = false;
    longPressHandled = false;
  }

  int64_t pos = encoder.getCount();
  if (pos != lastEncoderPos)
  {
    if (currentButtonState == LOW)
    {
      if (pos > lastEncoderPos)
        aircraftManager.ZoomIn();
      else
        aircraftManager.ZoomOut();

      buttonUsedForZoom = true;
    }
    else
    {
      if (pos > lastEncoderPos)
        aircraftManager.SelectNextAircraft();
      else
        aircraftManager.SelectPreviousAircraft();
    }

    lastEncoderPos = pos;
  }

  if (currentButtonState == LOW &&
      !buttonUsedForZoom &&
      !longPressHandled &&
      millis() - buttonDownAt >= 1500)
  {
    aircraftManager.ResetZoom();
    longPressHandled = true;
  }

  if (lastButtonState == LOW && currentButtonState == HIGH)
  {
    if (!buttonUsedForZoom && !longPressHandled)
      aircraftManager.EncoderClick();
  }

  lastButtonState = currentButtonState;
'''
    text = text[:start] + new_prefix + text[end:]
    write("src/main.cpp", text)
    print("Applied: encoder controls")
else:
    print("Already applied: encoder controls")

print("TARS radar enhancements applied successfully.")
