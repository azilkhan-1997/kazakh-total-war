// SPDX-License-Identifier: GPL-2.0-or-later
Engine.LoadLibrary("rmgen");
Engine.LoadLibrary("ktw_terrain");
export function* generateMap(mapSettings)
{
    globalThis.g_Map = KtwGenerateTerrain(mapSettings, true);
    yield 90;
    return g_Map;
}
