from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if new in text:
        print(f"Already updated {path}; skipping this block")
        return
    if old not in text:
        raise SystemExit(f"Expected source block not found in {path}; upstream source may have changed.")
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one matching block in {path}, found {text.count(old)}.")
    p.write_text(text.replace(old, new, 1))
    print(f"Updated {path}")

replace_once(
    "src/AircraftManager.h",
'''private:
    double lat = 0.0;
    double lon = 0.0;
    double rad = 0.2;
    std::map<String, TrackedAircraft> trackedAircraft;
''',
'''private:
    double lat = 0.0;
    double lon = 0.0;
    double rad = 0.2;
    int zoomIndex = 0;
    std::map<String, TrackedAircraft> trackedAircraft;
''')

replace_once(
    "src/AircraftManager.h",
'''    void DrawDetails(LGFX_Sprite &backbuffer);
    void EncoderClick();
    void ZoomIn();
    void ZoomOut();
    void ResetZoom();
};
''',
'''    void DrawDetails(LGFX_Sprite &backbuffer);
    void EncoderClick();
    void ZoomIn();
    void ZoomOut();
    void ResetZoom();
};
''')

replace_once(
    "src/AircraftManager.cpp",
'''constexpr int SCREEN_SIZE = 240;
constexpr int SCREEN_SIZE_DIV_2 = (SCREEN_SIZE / 2);
#include <ArduinoJson.h>
''',
'''constexpr int SCREEN_SIZE = 240;
constexpr int SCREEN_SIZE_DIV_2 = (SCREEN_SIZE / 2);

static constexpr float ZOOM_FACTORS[] = {1.0f, 0.5f, 0.25f, 0.10f};
static constexpr int ZOOM_LEVEL_COUNT =
    sizeof(ZOOM_FACTORS) / sizeof(ZOOM_FACTORS[0]);

#include <ArduinoJson.h>
''')

replace_once(
    "src/AircraftManager.cpp",
'''void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const
{
    constexpr int CENTRE = SCREEN_SIZE_DIV_2 - 1;
    constexpr int OUTER = SCREEN_SIZE_DIV_2 - 5;
    backbuffer.drawCircle(CENTRE, CENTRE, OUTER, lgfx::color888(0, 200, 0));
    backbuffer.drawCircle(CENTRE, CENTRE, (OUTER / 3) * 2, lgfx::color888(0, 64, 0));
    backbuffer.drawCircle(CENTRE, CENTRE, OUTER / 3, lgfx::color888(0, 32, 0));
}
''',
'''void AircraftManager::DrawRadarCircles(LGFX_Sprite &backbuffer) const
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

    const float displayRadiusDeg = rad * ZOOM_FACTORS[zoomIndex];
    const float displayRadiusKm = displayRadiusDeg * 111.32f;

    char rangeText[20];
    snprintf(rangeText, sizeof(rangeText), "R %.1f km", displayRadiusKm);

    backbuffer.setTextDatum(textdatum_t::bottom_center);
    backbuffer.drawString(rangeText, CENTRE, SCREEN_SIZE - 4);
    backbuffer.setTextDatum(textdatum_t::top_left);
}
''')

replace_once(
    "src/AircraftManager.cpp",
'''std::pair<int, int> AircraftManager::ProjectCoordinateToScreen(float predLat, float predLon) const
{
    const float dLon = predLon - lon;
    const float dLat = predLat - lat;
    const float normLon = (dLon + rad) / (2.0f * rad);
    const float normLat = (dLat + rad) / (2.0f * rad);

    const int x = static_cast<int>(normLon * SCREEN_SIZE);
    const int y = static_cast<int>(SCREEN_SIZE - (normLat * SCREEN_SIZE));

    return {x, y};
}
''',
'''std::pair<int, int> AircraftManager::ProjectCoordinateToScreen(float predLat, float predLon) const
{
    const float dLon = predLon - lon;
    const float dLat = predLat - lat;
    const float displayRad = rad * ZOOM_FACTORS[zoomIndex];

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
''')

replace_once(
    "src/main.cpp",
'''void loop()
{
  int64_t pos = encoder.getCount();
  if (pos != lastEncoderPos)
  {
    if (pos > lastEncoderPos)
    {
      aircraftManager.SelectNextAircraft();
    }
    else
    {
      aircraftManager.SelectPreviousAircraft();
    }

    lastEncoderPos = pos;
  }

  static bool lastButtonState = HIGH;

  bool currentButtonState = digitalRead(ENCODER_SW);

  if (lastButtonState == HIGH &&
      currentButtonState == LOW)
  {
    aircraftManager.EncoderClick();
  }

  lastButtonState = currentButtonState;
''',
'''void loop()
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
''')

print("TARS radar enhancements applied successfully.")
