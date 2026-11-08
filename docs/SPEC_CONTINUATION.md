# Accepted continuation requirements — Parts 1 / 2

This records the user's continuation for the existing project; it does not replace the implementation or acceptance evidence. Company: SAYRAM PLANETA HOLDING. Current working subtitle: LEGACY OF THE STEPPE. Approximately 1465 remains the initial campaign. Total War: Rome II and Crusader Kings III are design references only, never asset/code sources.

## Persistent modular simulation
Required responsibilities: GameCore, GrandCampaign, ProvinceSystem, DynastySystem, CharacterSystem, SuccessionSystem, PoliticsSystem, DiplomacySystem, EconomySystem, NomadSystem, ArmySystem, TacticalBattle, BattleBridge, StrategicAI, TacticalAI, EventSystem, SaveSystem, LocalizationSystem, GraphicsSystem, AssetPipeline, DiagnosticsSystem. Responsibility boundaries matter more than empty files with these names. Existing working architecture must be preserved.

Campaign state needs identity, calendar/season, factions, provinces, settlements, characters, dynasties, armies, diplomatic relations, economy, political events, wars and pending battles. Keep stable IDs and validate all links. Do not duplicate authoritative values without synchronization. Archive dead people rather than deleting their family and political links. Unknown historical facts remain unknown; gameplay scores and succession outcomes must be labelled as simulation rules.

## BattleBridge and saves
Snapshot army composition/health/morale/experience, commanders, province, terrain, weather and battle type; start actual native real-time battle; return winner, losses, prisoners/wounded where implemented, commander outcomes, experience and territorial effects. Apply each result once. Validate before committing. A bad result must leave a recoverable consistent pending battle. Test interruption, retry, conflict and corruption. Native mid-battle save must restore live entities and orders. Versioned manual/auto/quick saves must survive process restart. Tests include turns, moves, battle results, character death, state consistency and old saves.

## Explained AI and politics
Player can inspect reasons/factors for wars, attacks and political support. Runtime must remain offline, deterministic and performant. LLMs are optional future features only after cost/privacy/quality/performance decisions. They are not used by this prototype.

## Presentation
Art Bible: historically reviewed warriors/horses, variation of faces/clothes/age, steppe vegetation/natural materials, navy/graphite/bronze/gold/sand UI with original Kazakh ornament. Verify PBR/materials/shadows/LOD/instancing/blending/particles/weather/postprocessing/AA/scaling/high resolution against actual R28 source and runtime. Source support is not proof of accepted game behavior. Camera goals: strategic/free/low cinematic/follow/commander; replay future. Controls take priority over spectacle.

Audio: original menu/campaign/war/battle music with historically reviewed dombra/kobyz/percussion, cavalry/bows/weapons/voices/steppe/weather/camp sounds. Separate music/effect/voice/UI controls; actual audio acceptance required. No unlicensed tracks.

UI: continue/new/scenarios/custom battle/tutorial/settings/credits/exit. Campaign finances/supply/armies/province/diplomacy/dynasty/council/journal/minimap/end turn. Battle unit cards/minimap/formations/orders/morale/fatigue/pause/speed/commander/victory. RU/KK/EN, Kazakh glyphs, scale/hotkeys/text labels/subtitles/accessibility. Unimplemented menu features must not masquerade as functional.

## Part 1 acceptance retained
Windows-compatible launcher, Kazakh and opposing faction, >=5 provinces and troop types, recruitment/movement/turns, mounted archers, real tactical battlefield, victory/defeat, persistent casualties, campaign return/save/load. Keep open items active until verified, including actual Windows launch. Provide changed files, test/build status, real screenshots where possible, limits and remaining work. Never fabricate an executable, performance result or completion claim.

Maintain `ASTRA_PROJECT_STATE.md` with all 15 user-required fields. Every subsequent part extends this same project.
