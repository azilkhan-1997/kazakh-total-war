# Source audit: Millennium A.D. and Medieval A.D.

Audit date: 8 November 2026 (Asia/Almaty). These findings are from the downloaded Git working trees, not repository descriptions. This report covers source inspection and a deliberately small asset import; it is not a certificate that either complete mod works in Release 28.

## Pinned sources

| Project | Revision inspected | Actual mod.json | Source scope |
|---|---|---|---|
| Millennium A.D. | `91636b405ee8d0088ec3a34fba6074dbd5c9d0f3` (2026-04-02) | version `0.28.5`, dependency `0ad=0.28.0` | 3,335 tracked files; 403 simulation XML templates; 809 actor XML files; 12 JavaScript files |
| Medieval A.D. | `84e5b2d8caad8c8830cb6a3ac5c6d427c0d0462c` (2022-07-05) | version `1.0.0`, dependency `0ad=0.0.26` | 550 tracked files; 90 simulation XML templates; 143 actor XML files; zero JavaScript files |

Source URLs:
- https://github.com/0ADMods/millenniumad/tree/91636b405ee8d0088ec3a34fba6074dbd5c9d0f3
- https://github.com/0ADMods/medievalad/tree/84e5b2d8caad8c8830cb6a3ac5c6d427c0d0462c

All 1,284 tracked Millennium XML files and all 237 tracked Medieval XML files parsed successfully with Python ElementTree. This establishes XML well-formedness only, not schema validity, inheritance validity, renderability or simulation compatibility. Detailed machine-readable inventory: `mod-source-inventory.json`.

## Integration matrix

| Component | Actual finding | Decision for kazakh_total_war | Required check |
|---|---|---|---|
| Millennium simulation | R28 dependency; templates use `Identity/Requirements`, `Trainer`, `Researcher`, `Resistance` | Do not import whole faction templates; write original KTW templates against R28 | Actual template load, command and combat tests |
| Millennium mounted archer | `units/rus/cavalry_archer_b.xml` calls itself “Qasaq cavalry archer”; its actor uses a nomad body and Xiongnu-labelled bow/head/cloth props | Admit an isolated licensed visual subset as a prototype; do not claim the asset label proves 1465 authenticity | Skeleton, animation, prop closure, material, rendering and shooting tests |
| Millennium infantry/cavalry art | Europe/late-antiquity factions have equipment unsuitable for automatic relabelling as Kazakh | Create five consistent composite proxy actors from the nomad body and shared engine animation sets | Historical redesign remains open; first release must identify provisional art |
| Millennium siege art | Contains mechanical trebuchet animations and operator animations | Defer; not needed for first battle loop | Crew attachment, projectile timing, minimum range, path obstruction and damage tests |
| Millennium music | README thanks Antti Martikainen for permission; no scoped redistributable commercial license found for individual audio files | Exclude all audio from import | Obtain explicit transferable terms before any reuse |
| Millennium GUI | 12 JS files, loading code and global music override; project-information file still labels Alpha XXIV | Do not import GUI or global prototype modifications | Original GUI must use R28 APIs; dependency version alone is not proof |
| Medieval simulation | Five files still contain `Identity/RequiredTechnology`; exact dependency is Alpha 26 | Quarantine all templates; no dependency-only version bump | Rewrite requirements against R28 schema and test actual behavior |
| Medieval combat/AI | No custom JavaScript simulation systems or tactical AI; relies on base-engine templates | Use as reference, not a second independent battle engine | Cannot credit it with mechanics it does not implement |
| Medieval animations | Only four tracked animation files, all teutonic wall-door states | No combat-animation import | Gate actor state transitions would require actual R28 testing |
| Medieval actors/models | European Teutonic/Polish equipment and generic props | Exclude until exact license scope is resolved; do not put these factions into 1465 Kazakhstan | Per-file attribution/license and historical review |
| Both mods together | Same relative VFS paths include waypoint flag and player_defaults.json | Never enable both full mods as implicit dependencies | Namespaced selective imports avoid last-loaded-file conflicts |

The KTW module's dependency is the base game only. Neither `millenniumad` nor `medievalad` is required at runtime. No global simulation/GUI file from either mod has been copied.

## Specific Medieval migration blockers

The following real files use legacy `Identity/RequiredTechnology`:

1. `simulation/templates/template_structure_special_mines.xml`
2. `simulation/templates/template_unit_support_bannerman.xml`
3. `simulation/templates/units/teutonic/cavalry_spearman_b.xml`
4. `simulation/templates/units/teutonic/cavalry_swordsman_b.xml`
5. `simulation/templates/units/teutonic/support_female_citizen_house.xml`

A migration must translate the requirement semantics to the R28 `Requirements` model, resolve inherited templates, validate technology IDs and run training/building availability checks. An XML parse and a changed mod.json version do not perform that migration. Medieval's `cavalry_spearman_b.xml` references `units/teutonics/cavalry_spearman_b_m.xml`; the spelling difference (`teutonic` faction, `teutonics` art) is intentional in this tree and must not be blindly normalized. Actors depend on base-engine horse meshes, rider variants and materials; copying the XML alone will not make a self-contained asset.

The complete Medieval mod has **not** been migrated or certified. Its content is excluded from the shipping KTW subset. This is an explicit outstanding part of the larger specification, not a completed feature.

## Licensing findings and import policy

### Millennium

Root `License.txt` is GPL version 2. More specific **`art/license.txt`** states the artwork directory is CC BY-SA 3.0 unless otherwise noted, with the attribution “The Council of Modders, Fallen Empire Studio, Scion Development” and links to Wildfire Games and the license. It also describes the special permission applying to the already-derived CGTextures textures; that does not grant rights to arbitrary new CGTextures downloads.

The admitted subset is entirely inside `art/`, no conflicting asset-level restriction was found in these admitted XML/DAE files, and the original artwork license is included in `mods/kazakh_total_war/art/ktw-MILLENNIUM-LICENSE.txt`. Each admitted file has a source path, pinned revision and SHA-256 in `asset-manifest-millennium.json`. A generic COLLADA author value such as “Blender User” is not treated as a replacement for the explicit directory attribution. All altered actors retain CC BY-SA 3.0; engine-level licenses remain separate.

### Medieval

`LICENSE.MD` contains only two lines:

```
SPDX-License-Identifier: CC-BY-4.0
SPDX-License-Identifier: GPL-2.0-or-later
```

It does not map the two declarations to paths or state AND/OR. README credits BigTiger and Stan for art. Those facts are insufficient to assign a definite license to each mesh/texture as a matter of provenance. No Medieval file has been admitted. Quarantine is preferable to fabricating an OR license or assuming the repository badge covers every asset.

## Implemented art migration

`docs/vendor_millennium_art.py` reproduces the small import from the pinned Millennium checkout. It copies only transitive files available in that checkout and preserves base-game references. Imported actors, variants, meshes, animation and textures are namespaced under `ktw/millennium/`; the animated bow skeleton is installed under a unique filename. This avoids replacing the base game's or another mod's generic actors.

Five game-facing actors are provided:

| Actor | Visual status |
|---|---|
| `ktw/units/mounted_archer.xml` | Nomad proxy; corrected rider material slots; animated bow and rider attack variants |
| `ktw/units/light_cavalry.xml` | Original composite proxy with spear, nomad clothing and riding animation |
| `ktw/units/heavy_cavalry.xml` | Original composite proxy with iron helmet and lamellar horse armor; final Kazakh armor reconstruction pending |
| `ktw/units/spearman.xml` | Original composite proxy with nomad body and infantry spear animation |
| `ktw/units/infantry_archer.xml` | Original composite proxy with nomad body, bow and infantry archer animation |

Confirmed source material defect corrected: in `units/rus/cavalry_archer_b_r.xml`, `xion_cloth_norm.png` was assigned to `specTex` and `xion_cloth_spec.png` to `normTex`. Those slots are corrected, and a final group that would overwrite them with flat defaults is removed. No binary texture painting or generated imagery is used in this migration.

These are real render assets, not evidence of validated historical reconstruction or visual quality exceeding 0 A.D. Rendering, mounted shooting and production Windows behavior require engine tests. Static dependency-closure results are recorded separately when the verified Release 28 data archive is available.

## Release 28 static compatibility results

The complete restored official `public.zip` was inspected (52,829 archive entries). Official cached `.pmd`, `.psa`, `.dds` and `.xmb` assets were resolved as valid counterparts to source resource paths; their presence is not a missing-source error.

- Millennium: 833 actor/variant XML files checked against its own tree plus R28; **zero unresolved direct art references**; 52 paths override base-game art/GUI/simulation files. This does not certify the full mod's gameplay.
- Medieval: 146 actor/variant XML files checked; **13 unresolved references to five removed/missing material names**. These are concrete R28 compatibility failures, in addition to the five legacy technology-requirement fields. Full per-file evidence: `mod-compatibility-release28.json`.
- Admitted KTW subset: **232 transitive resources resolved, zero missing**. 45 shipped module resources, 61 base R28 XML resources and 126 official cached resources. Evidence: `art-closure-release28.json`. This remains static verification, not a GPU or animation test.
- R28 `simulation/components/Identity.js` includes `Requirements` and does not include `RequiredTechnology`; its inspected SHA-256 is in the compatibility JSON.

The Medieval material failures cannot be repaired responsibly by renaming files blindly. Each material's shader inputs, alpha behavior, player color and normal/specular texture bindings must be adapted to a supported R28 material and then rendered. Medieval remains quarantined.

Missing Medieval material paths:

- `art/materials/basic_spec.xml`
- `art/materials/basic_trans_spec.xml`
- `art/materials/player_trans_parallax.xml`
- `art/materials/player_trans_spec.xml`
- `art/materials/terrain_norm.xml`
