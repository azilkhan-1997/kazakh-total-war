# Recorded evidence

These files come from the actual Pyrogenesis 0.28.0 Linux run. The PNGs are native game-window captures, not concept art. The MP4 is a continuous 20-second live X11 recording at 1280×720, encoded as H.264 with a 30 fps output container. It is not a slideshow, not a rendered trailer and not a measurement of engine FPS. The QA runtime used software rendering and disabled audio.

The early campaign/battle screenshots were captured during functional testing; the later postbattle screenshot reflects the reduced terrain haze. The final module also includes the last camera and text-contrast fixes. No screenshot should be presented as final historical art or as evidence of Windows testing.

`state-before-load.json` and `state-after-load.json` retain the same complete authoritative campaign across the native load dialog. `state-postbattle.json` and `state-after-process-restart.json` retain the same campaign after a full engine restart, including 62 Kazakh and 12 opposing survivors. Entity marker IDs may be reconstructed when changing scenes; campaign IDs and counts are the persistent authority.

`state-midbattle-before.json` and `state-midbattle-after.json` verify a separate native save at 15 simulation seconds and full process restart: pending battle-1 and 170/155 troops remain intact. The controller snapshot and every friendly entity snapshot match, including IDs, health, coordinates and queued orders.
