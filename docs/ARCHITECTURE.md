# Legacy of the Steppe — native Pyrogenesis prototype 0.2

## Scope

This continues the existing Pyrogenesis / 0 A.D. Release 28 module from commit `608e9e4`. It does not replace the previously published Godot DALA 0.3 build. It is not an HTML game and contains no browser runtime. Module ID and campaign ID remain stable through the subtitle change. Trademark clearance for a public commercial title is not established.

## Two modes, one campaign

The pure JavaScript `KtwCampaign` reducer owns political and economic state. `KtwController`, a native Pyrogenesis simulation system component, owns its engine integration and serialized entities. The GUI submits ordinary deterministic network commands; it does not directly fabricate battle casualties.

`ktw_campaign` is a generated 3D terrain with settlements and army markers. Province adjacency governs moves independently of the decorative geographic distances. The political boundaries and distances are deliberately schematic.

`ktw_battle` is a different generated 3D map. The pending battle snapshots the participating regiments. The simulation creates one real Pyrogenesis entity per warrior. Native pathfinding, unit orders, formations, attack/projectile processing, health and skeletal animations execute within the engine.

On a scene transition, the GUI obtains a validated campaign snapshot, ends the old game session and starts the next native map with that snapshot in initialization settings. Battle resolution counts surviving simulation entities by their regiment identities and applies the result exactly once. The campaign then reconstructs its map markers from the updated state. No cross-process Python or C# service is required.

## Save boundaries

Native 0 A.D. saves serialize the simulation component and battle entities, including an unresolved battle. A separate checksummed campaign JSON representation is used by unit tests and tools. The checksum detects accidental corruption; it is not an anti-cheat signature. The campaign prevents replaying a result under a different battle ID or gaining warriors through casualty reports.

## Code organization

| Path | Responsibility |
| --- | --- |
| `mods/kazakh_total_war/simulation/helpers/KtwCampaign.js` | Deterministic economy, turn progression, movement and battle transactions |
| `mods/kazakh_total_war/simulation/components/KtwController.js` | Real entities, mode setup, orders and battle resolution |
| `mods/kazakh_total_war/gui/` | Native XML/JS menu and campaign HUD |
| `mods/kazakh_total_war/maps/random/` | Native terrain generation |
| `mods/kazakh_total_war/art/` | Namespaced, licensed actor subset |
| `research/` | Historical anchors and explicitly marked gameplay assumptions |
| `tests/` | Campaign and integration checks |
| `tools/` | Packaging and source/asset validation |

## Deliberately deferred

Full sieges, all requested eras, clan politics, historical-event scripting, advanced false retreat/circular horse archery, final 15th-century costumes, fully animated nomadic life, photorealism and measured 1,000–5,000-warrior performance are not implied by this technical prototype. No engine C++ replacement is necessary for the first proof. C# is not inserted merely to satisfy a language list. Future engine changes must be justified by profiling and isolated behind reproducible build patches.

## 0.2 transaction and persistence changes

`KtwBattleBridge` validates battle context, roster and commander outcomes, and constructs a canonical receipt. A result with only explicit `alive` outcomes has the same signature as the corresponding legacy result; deaths are sorted into the signature. This preserves schema-1 receipt replay. The controller ties a commander to one existing warrior, keeping 325 starting soldiers rather than adding invisible bonus units. Health determines the reported outcome. Old mid-battle saves have no such identity and remain untracked until a new battle.

`KtwCampaign.resolveBattle` validates the input, clones the whole campaign, applies losses/retreat/ownership and `KtwPolitics` consequences to the candidate, validates all cross-links, then commits. An exception during any candidate update leaves the source untouched. Duplicate matching receipts return without mutation; conflicts are rejected. This is an in-memory atomic state change, not a database transaction or a claim of crash-proof disk writes.

`KtwSaveSystem` checks the original JSON envelope checksum before decoding/migrating. `KtwCampaign.upgrade` returns a validated independent schema-2 state from schema 1 or 2; unknown versions fail. `restoreWithRecovery(primary, backup)` returns a validated previous JSON checkpoint with the original failure reason, or fails when both are bad. Native `.0adsave` serialization remains engine-owned. **No custom Serialize/Deserialize methods were added:** R28's binary deserializer reads according to the current prototype, so adding them would break old payloads. `KtwController.OnDeserialized` upgrades only after native fields/entities are loaded. Invalid state/mappings lock campaign commands and KTW-controlled saving (the base engine simulation is not automatically paused); the UI directs the player to a prior save. Two rotating turn-autosave slots and the transition checkpoint provide separate native recovery choices; torn or arbitrarily corrupted native files cannot be repaired by the JSON codec.

`KtwPolitics` maintains characters, reciprocal family links, lineage archives, factions, council weights, stable political event IDs and explained candidate scores. Confirmed deaths are archived before succession; a missing eligible successor leaves an explicit vacancy. Present groups/weights/abilities are clearly marked gameplay assumptions. Verified father-child links are documented in `research/CHARACTER_MODEL_NOTES.md`; absent dates/spouses remain unknown. Autoresolve does not yet report commander death.

## Responsibility mapping (no empty placeholder modules)

| Requested responsibility | Current implementation | Extent |
|---|---|---|
| GameCore / GrandCampaign / ProvinceSystem / ArmySystem | KtwCampaign + KtwController + native maps | Eight provinces, two armies, turns, recruitment, real marker scene |
| CharacterSystem / DynastySystem | KtwPolitics | Five permanent people, two documented lineage archives, family/relationship validation |
| SuccessionSystem / PoliticsSystem | KtwPolitics | Deterministic council on confirmed ruler death, reasons and vacancy; broader politics pending |
| EconomySystem / NomadSystem / DiplomacySystem | KtwCampaign | Supplies/upkeep/pasture/buildings/three-turn truce; migration, marriages, vassals pending |
| StrategicAI / EventSystem | KtwCampaign | Pursuit/attack/truce events with factors and stable IDs; not autonomous grand diplomacy |
| TacticalBattle / TacticalAI | Native R28 + KtwController | Actual unit commands and combat, simple morale/fatigue/routing/skirmishing |
| BattleBridge | KtwBattleBridge + staged campaign resolver + controller | Actual losses/commanders, exactly-once receipt, validated return |
| SaveSystem | KtwSaveSystem + native serialization + GUI checkpoints | Schema migration/JSON recovery, native manual/turn/transition saves |
| LocalizationSystem / UI | gui/common/ktw.js, data.json, session/menu pages | RU/KK/EN custom panels; stock engine KK incomplete |
| GraphicsSystem / AssetPipeline | Unmodified R28, namespaced licensed actors, validation tools | Actual native rendering; additional PBR/LOD/AAA goals unproven |
| DiagnosticsSystem | Node tests, Python validator, native fixtures/evidence | Distinguishes pure logic, mocked APIs, real Linux runs and untested Windows |

## CampaignState field ownership

`campaignId` is identity; `turn/year/season` form the single authoritative calendar. `provinces[].owner/settlement/buildings` describe territories; `armies[].regiments` are campaign troops. `factions`, `characters`, `dynasties`, `politicalEvents` own political state. `treasury` owns resources; `relation/ceasefireUntil` represent the present two-faction diplomatic model. `pendingBattle` is the single active transfer and `resolvedBattles` is its receipt ledger. `events` has stable IDs; `lastBattle` is a display summary, not authority for reapplying a result. Full multiple-war/settlement/nomad data models remain future work rather than duplicated aliases of these fields.
