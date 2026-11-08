# Native Release 28 headless battle fixture

This is an exact copy of the test-only `ktw_test` overlay used for the successful
headless engine run recorded in `docs/native-simulation-test.json`. It is not a
production mod and must not be included in a normal player installation.

The overlay replaces the upstream autostart class solely for QA. It passes the
same deterministic campaign snapshot (seed 1465, pending `battle-1`) to the real
engine, starts `ktw_battle.js`, and samples the actual controller every 30
simulation seconds. It does not fabricate damage, casualties or a winner. Its
post-transition logging repeats the final result; the complete original log is
therefore compressed in `evidence/headless-battle-full.log.gz`.

## Reproduce on ordinary Linux

Requirements: a working **0 A.D. / Pyrogenesis 0.28.0** executable and its matching
public game data, GNU `timeout`, and an ordinary non-root Linux account. Native
development dependencies or a graphics display are not required for this
headless check. Do not substitute a different release.

Run from the root of this source project:

```bash
KTW_PROJECT="$PWD"
KTW_QA_PROFILE="$(mktemp -d)"
mkdir -p "$KTW_QA_PROFILE/data/0ad/mods" "$KTW_QA_PROFILE/config" "$KTW_QA_PROFILE/cache" "$KTW_QA_PROFILE/state"
ln -s "$KTW_PROJECT/mods/kazakh_total_war" "$KTW_QA_PROFILE/data/0ad/mods/kazakh_total_war"
ln -s "$KTW_PROJECT/tests/native_fixture/ktw_test" "$KTW_QA_PROFILE/data/0ad/mods/ktw_test"
XDG_DATA_HOME="$KTW_QA_PROFILE/data" \
XDG_CONFIG_HOME="$KTW_QA_PROFILE/config" \
XDG_CACHE_HOME="$KTW_QA_PROFILE/cache" \
XDG_STATE_HOME="$KTW_QA_PROFILE/state" \
timeout 20s pyrogenesis \
  -mod=public -mod=kazakh_total_war -mod=ktw_test \
  -autostart=random/ktw_battle -autostart-nonvisual -nosound \
  > "$KTW_QA_PROFILE/battle.log" 2>&1
```

Use the full path to the installed `pyrogenesis` binary if it is not on `PATH`.
The exit code **124** is expected when `timeout` terminates the otherwise
continuing simulation. Twenty wall-clock seconds was sufficient in the original
environment; slower hardware can need a longer timeout. The authoritative
success signal is a `KTW_QA` sample with `"transition":"campaign"` and a complete
result, not the timeout or a particular number of wall-clock seconds.

Expected successful baseline: 170 Kazakh and 155 Abulkhair soldiers at time 1;
actual combat and losses; at simulation time 289, Kazakh victory with 49 and 16
survivors. Compare results only with the same production code and assets; later
balance changes can legitimately produce another outcome.

The original execution used the exact command arguments above and these
relative workspace resources:

- executable: `upstream/runtime/usr/games/pyrogenesis`;
- engine libraries: `upstream/runtime/usr/lib/games/0ad` and
  `upstream/runtime/usr/lib/x86_64-linux-gnu` via `LD_LIBRARY_PATH`;
- XDG profile: `upstream/simtest/{data,config,cache,state}`;
- matching official public data from `upstream/0ad-0.28.0/binaries/data`.

The original constrained sandbox mapped only UID 0 and needed a local,
test-only compatibility shim for the engine's root-user check. That shim is
**not part of this fixture or production package**. Ordinary non-root Linux
execution must not use it. No privilege adjustment is needed in a normal test
installation.

## Evidence and limits

`fixture-integrity.json` records hashes of the exact copied fixture and the full
uncompressed original log. `evidence/headless-battle.log` is a readable excerpt
with every distinct QA sample. The gzip file preserves the complete log.

This test proves native simulation initialization and a battle result. It does
not prove Windows compatibility, rendering quality, frame rate, or persistence
across an application restart. The engine rejects `-serializationtest` for
random maps, so that flag was intentionally absent from the successful run.
Save/load and GUI map transitions require the separate interactive tests.
