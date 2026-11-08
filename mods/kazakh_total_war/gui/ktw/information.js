/* SPDX-License-Identifier: GPL-2.0-or-later */
function init() {
 Engine.GetGUIObjectByName("ktwInfoTitle").caption=ktwText("credits");
 Engine.GetGUIObjectByName("ktwInfoBody").caption=ktwText("creditsBody");
 Engine.GetGUIObjectByName("ktwInfoClose").caption=ktwText("close");
 return new Promise(closePageCallback => { Engine.GetGUIObjectByName("ktwInfoClose").onPress=closePageCallback; });
}
