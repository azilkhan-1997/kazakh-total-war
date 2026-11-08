/* SPDX-License-Identifier: GPL-2.0-or-later */
function init(data) { if(ktwSyncEngineLocale())return; ktwMenuRefresh(); if (data && data.ktwError) Engine.GetGUIObjectByName("ktwMenuError").caption = data.ktwError; }
function ktwMenuRefresh() {
 Engine.GetGUIObjectByName("ktwLangkk").caption="ҚАЗ"; Engine.GetGUIObjectByName("ktwLangru").caption="РУС"; Engine.GetGUIObjectByName("ktwLangen").caption="ENG";
 ["Continue","Settings","Hotkeys","Credits"].forEach(function(key){Engine.GetGUIObjectByName("ktw"+key).caption=ktwText(key.toLowerCase());});
 var save=ktwLatestSave();
 Engine.GetGUIObjectByName("ktwContinue").enabled=!!save;
 Engine.GetGUIObjectByName("ktwContinue").tooltip=save?save.metadata.description || ktwText("continue"):ktwText("noSave");
 Engine.GetGUIObjectByName("ktwNew").caption=ktwText("new");
 Engine.GetGUIObjectByName("ktwLoad").caption=ktwText("load");
 Engine.GetGUIObjectByName("ktwQuit").caption=ktwText("quit");
 Engine.GetGUIObjectByName("ktwMenuSlogan").caption=ktwText("slogan");
 Engine.GetGUIObjectByName("ktwMenuStats").caption=ktwText("stats");
 Engine.GetGUIObjectByName("ktwMenuNotice").caption=ktwText("prototype")+"\n"+ktwData().notice[ktwLanguage()]+(ktwLanguage()==="kk"?"\nҚазақша интерфейс; Pyrogenesis-тің дайын диалогтары әзірше орысша.":"");
}
function ktwNewCampaign() { ktwLaunch("campaign",null,false); }
