# Native Pyrogenesis interface — version 0.2

The interface remains native engine XML and JavaScript. Version 0.2 extends the existing v0.1 campaign/battle UI; it does not restart the project or replace the game with HTML. The working subtitle is now **LEGACY OF THE STEPPE**. The module ID `kazakh_total_war` and campaign ID `great_steppe_1465_slice` remain unchanged. No proprietary Total War files are used.

## Changes in 0.2

| Feature | Behavior and implementation boundary |
| --- | --- |
| Continue | Selects the most recent compatible KTW native save by its metadata timestamp. It accepts the original module version `0.1.0` or the currently loaded module version, provided engine serialization version, required base mods and KTW map/mode match. It does not silently load unrelated 0 A.D. games or future module versions. |
| Main-menu settings | Opens the existing Release 28 options page and applies its configuration-change callbacks. The separate Hotkeys button opens the native hotkey editor. These are inherited engine controls, not a newly implemented settings subsystem. |
| Credits | Opens an original, scrollable native child page with project attribution, Wildfire Games attribution, Millennium artwork attribution and applicable license references. |
| Political council | Displays the simulation-provided ruler, proposed successor, group influence, candidate support and score factors. The UI does not determine the winner or mutate political state. The explanatory notice identifies this as an abstract gameplay rule, not a reconstruction of a particular 1465 qurultay. |
| Character archive | Displays persistent character names, statuses, titles, family links, lineage, balance abilities, known death information and explicitly unknown birth dates. Deceased characters remain visible. This is a data view, not a complete interactive family-tree editor. |
| Event journal | Shows campaign and political events, newest turns first. Enemy movement, paid truce, truce expiry, declared war and succession reasons have RU/KK/EN explanations. Numeric facts come from the simulation. |
| Commander display | The campaign roster uses the current commander instead of a fixed Kerei label. In a battle, the commander button focuses the camera on the living bound entity. A dead or unavailable commander cannot be focused. |
| Turn autosaves | A validated campaign turn change triggers one native save into `ktw_autosave_0` or `ktw_autosave_1`, alternating by turn parity. Repeated UI ticks, initial load and battle-mode ticks do not create duplicate turn saves. The existing quicksave and transition checkpoint remain. |
| Recovery screen | If the controller reports `KTW_LOAD_RECOVERY_REQUIRED`, the GUI blocks campaign/battle controls and its Save button before rendering the malformed state. The screen offers a backup-save browser and return to the main menu. It does not overwrite the original save or claim to repair an arbitrary damaged native binary. |
| Visual presentation | The existing original dark interface uses navy, graphite and muted bronze/gold accents. Council/archive/journal panels open over the center of the map and can be closed; they do not permanently replace the 3D view. |

## Existing gameplay controls retained

- On the campaign map, select a province from the left list or select its real 3D settlement. **«Отправить войско»** moves the army to an eligible neighboring province. **«Завершить ход»** advances the shared campaign clock.
- The lower roster retains recruitment of the five implemented troop types. The province panel retains pasture/market construction and the paid three-turn truce. Prices and treasury/supply totals are dynamic.
- **«Политический совет»** opens the council view. Its **«Персонажи и родословная»** tab opens the character archive. **«Журнал событий»** opens recorded decisions and outcomes. **«Закрыть»** restores the unobstructed map center.
- The encounter panel retains **«Сражаться»**, **«Авторасчёт»** and **«Отступить»**, subject to simulation rules.
- In battle, left-click or drag selects units; right-click issues movement or attack orders. Native formation and stance controls remain available. The commander-name button moves the camera to the living commander. Existing camera controls include the mouse wheel for zoom and arrow keys for movement.
- **«Сохранить»** writes `ktw_quicksave`; the two turn-autosave slots retain alternating turn checkpoints. Scene transitions also retain `ktw_transition`. These are native `.0adsave` files, not browser storage.
- **«Продолжить»** launches the newest compatible KTW save. **«Загрузить игру»** opens the native save browser. Saves from v0.1 can be eligible for KTW migration despite a module-version mismatch; the inherited browser's compatibility filter can still hide such entries. The Continue path performs the targeted KTW compatibility check directly.
- **«Настройки»** opens engine options; **«Горячие клавиши»** opens the inherited remapping editor. Newly added KTW buttons are clickable controls; a complete custom remappable shortcut set has not been implemented.

## Files changed

| Path | Responsibility |
| --- | --- |
| `mods/kazakh_total_war/gui/common/ktw.js` | RU/KK/EN text, targeted save compatibility, Continue/load, options/hotkey/credits entry points |
| `mods/kazakh_total_war/gui/ktw/mainmenu.js` | Menu labels, Continue availability and tooltip |
| `mods/kazakh_total_war/gui/ktw/mainmenu.xml` | Expanded native main-menu layout and new working subtitle |
| `mods/kazakh_total_war/gui/page_ktw_information.xml` | Credits child-page includes |
| `mods/kazakh_total_war/gui/ktw/information.js` | Credits initialization and Release 28 child-page close callback |
| `mods/kazakh_total_war/gui/ktw/information.xml` | Scrollable credits dialog |
| `mods/kazakh_total_war/gui/session/ktw.js` | Council/archive/journal presentation, turn autosaves, commander focus and load-recovery guard |
| `mods/kazakh_total_war/gui/session/session_objects/ktw.xml` | Campaign toolbar, dismissible dossier, commander button and recovery panel |
| `tests/gui.test.cjs` | Focused compatibility, autosave, explanation, archive and recovery tests |

The authoritative campaign, characters, council calculations and commander bindings are supplied by the simulation. GUI actions use the existing network-command path. The GUI does not fabricate casualties, deaths, elections or AI decisions.

## Verified static scope

The following checks were completed for the 0.2 GUI implementation:

- `node --test tests/gui.test.cjs`: **6 tests passed**. They cover selecting a v0.1/current-version save, rejecting incompatible or unrelated saves, two-slot autosave behavior, translated decision reasons with numeric facts, simulation-derived council/archive text and recovery-state save blocking.
- All **five GUI XML files** validate against the actual Release 28 `gui.rng` / `gui_page.rng` schemas. The included session `object` is wrapped only for schema validation, preserving its required production root.
- Changed GUI JavaScript passes `node --check`; `git diff --check` reports no whitespace errors in these files.

The Node tests use a mocked GUI API. They verify presentation and control-flow rules; they do **not** establish that a native dialog rendered correctly, a native save survived a process restart, or Windows execution succeeded. Native runtime results, screenshots and platform limitations belong in `docs/native-qa-v0.2.md` and its evidence files. Earlier v0.1 native evidence remains separate.

## Release 28 integration details

- Use `Engine.OpenChildPage`, not the removed older `Engine.PushGuiPage` API. A new child page closes when its `init` promise resolves; no unverified `Engine.ClosePage` call is used.
- Native options return changed configuration keys for `fireConfigChangeHandlers`.
- `Engine.StartGame` receives the two human player records; `LoadPlayerSettings` inserts Gaia. `PopulationCapType` remains specified alongside `PopulationCap`.
- XML included through `session_objects/` uses one `object` root. Dynamic decorative square brackets are avoided because the GUI interprets them as markup.
- GUI data JSON remains ASCII-escaped to preserve Cyrillic and Kazakh text through the existing engine data-reading path.
- Continue checks save metadata before starting the session. Binary integrity and simulation migration are handled by native loading and the controller; metadata filtering alone does not certify an intact save.

## Remaining work and limits

Custom menus, campaign overlays, political views and credits have RU/KK/EN text. The engine locale is synchronized to Russian for RU and KK, and English for EN. The upstream Release 28 package lacks a Kazakh dictionary: inherited save dialogs, options, tactical tooltips and error messages therefore remain Russian when KK is selected. The main menu states this limitation.

Council groups, influence, abilities and election weights are gameplay abstractions. The council is currently a read-only explanation view; interactive clan management, player-driven candidate negotiation, marriage diplomacy and a full dynasty interface remain unimplemented. There are no new character portraits or unique commander models in this GUI increment.

Historical scenarios, custom battle configuration and a playable tutorial have not been added as inactive menu promises. Complete accessibility validation, subtitle/voice systems, custom UI-scale behavior across resolutions and a complete KTW-specific hotkey set remain outstanding. Opening inherited engine settings is not proof that all requested accessibility, audio or graphics features exist in this module.

No performance or Windows compatibility claim is inferred from UI code or mocked tests.
