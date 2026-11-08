/* SPDX-License-Identifier: GPL-2.0-or-later
 * Versioned campaign interchange format; native .0adsave remains engine-owned.
 */
var KtwSaveSystem = (function() {
"use strict";
function fail(code) { throw new Error('KTW_' + code); }
function checksum(text) {
  var hash = 2166136261;
  for (var i = 0; i < text.length; ++i) hash = Math.imul(hash ^ text.charCodeAt(i), 16777619);
  return (hash >>> 0).toString(16);
}
function encode(state) {
  var payload = JSON.stringify(state);
  var envelope = JSON.stringify({ format: 'KTW_CAMPAIGN', version: state.schemaVersion, checksum: checksum(payload), payload: payload });
  if (envelope.length > 2000000) fail('SAVE_SIZE');
  return envelope;
}
function decode(text) {
  if (typeof text !== 'string' || text.length > 2000000) fail('SAVE_SIZE');
  var envelope;
  try { envelope = JSON.parse(text); } catch (_) { fail('SAVE_JSON'); }
  // Verify the original bytes before parsing or migrating the payload.
  if (!envelope || envelope.format !== 'KTW_CAMPAIGN' || ![1, 2].includes(envelope.version) || typeof envelope.payload !== 'string' || checksum(envelope.payload) !== envelope.checksum) fail('SAVE_CHECKSUM');
  var state;
  try { state = JSON.parse(envelope.payload); } catch (_) { fail('SAVE_JSON'); }
  if (!state || state.schemaVersion !== envelope.version) fail('SAVE_VERSION');
  return state;
}
function recover(primary, backup, restore) {
  try { return { state: restore(primary), source: 'primary', recovered: false, primaryError: null }; }
  catch (e) {
    var message = String(e.message || e);
    try { return { state: restore(backup), source: 'backup', recovered: true, primaryError: message }; }
    catch (_) { fail('SAVE_RECOVERY_FAILED'); }
  }
}
return { encode: encode, decode: decode, recover: recover };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = KtwSaveSystem;
if (typeof Engine !== 'undefined') Engine.RegisterGlobal('KtwSaveSystem', KtwSaveSystem);
