// SPDX-License-Identifier: GPL-2.0-or-later
// Native Pyrogenesis campaign / battle bridge. All fields serialize with engine saves.
function KtwController() {}

KtwController.prototype.Schema = "<a:component type='system'/><empty/>";

KtwController.prototype.Init = function()
{
	this.mode = "inactive";
	this.state = null;
	this.transition = null;
	this.error = "";
	this.markers = [];
	this.units = [];
	this.regiments = [];
	this.elapsed = 0;
	this.timer = null;
	this.battleStats = null;
	this.lastResult = null;
	this.worldSize = 1024;
	this.commanders = [];
};

// Preserve the engine's original serialization shape. Adding a custom
// Deserialize would change the binary layout expected by existing v0.1 saves.
// R28 broadcasts this message after all components and entities are restored.
KtwController.prototype.OnDeserialized = function()
{
	if (!this.state)
		return;
	try
	{
		const upgraded = KtwCampaign.upgrade(this.state);
		const mappings = this.commanders === undefined ? [] : this.commanders;
		if (!Array.isArray(mappings) || mappings.length > 2)
			throw new Error("KTW_SAVE_COMMANDER_ENTITIES");
		const characterIds = new Set(), entityIds = new Set(), armyIds = new Set();
		for (const mapping of mappings)
		{
			const army = upgraded.armies.find(a => a.id === mapping.armyId);
			const character = upgraded.characters.find(c => c.id === mapping.characterId);
			const unit = (this.units || []).find(u => u.entity === mapping.entity);
			const snapshot = upgraded.pendingBattle && upgraded.pendingBattle.armies.find(a => a.id === mapping.armyId);
			if (!army || !character || !unit || character.factionId !== army.faction ||
				unit.owner !== (army.faction === "kazakh" ? 1 : 2) ||
				!army.regiments.some(r => r.id === unit.regimentId) ||
				(snapshot && snapshot.commander !== character.id) ||
				characterIds.has(character.id) || entityIds.has(mapping.entity) || armyIds.has(army.id))
				throw new Error("KTW_SAVE_COMMANDER_ENTITIES");
			characterIds.add(character.id); entityIds.add(mapping.entity); armyIds.add(army.id);
		}
		// Old battles had no commander-to-entity identity. Do not retrospectively
		// invent one or infer a historical character death from old losses.
		this.commanders = mappings;
		this.state = upgraded;
		this.error = "";
	}
	catch (e)
	{
		// Leave the serialized state untouched; disable commands and simulation.
		this.error = "KTW_LOAD_RECOVERY_REQUIRED: " + String(e.message || e);
		error(this.error);
	}
};

KtwController.prototype.OnGlobalInitGame = function()
{
	const settings = InitAttributes && InitAttributes.settings;
	if (!settings || !settings.KtwMode)
		return;
	try
	{
		this.mode = settings.KtwMode;
		if (!["campaign", "battle"].includes(this.mode))
			throw new Error("KTW_MODE");
		this.state = settings.KtwCampaign ? KtwCampaign.upgrade(settings.KtwCampaign) : KtwCampaign.create(settings.Seed || 1465);
		KtwCampaign.validate(this.state);
		this.worldSize = (settings.Size || 256) * 4;
		for (let player = 1; player <= 2; ++player)
		{
			const diplomacy = QueryPlayerIDInterface(player, IID_Diplomacy);
			if (diplomacy)
				diplomacy.SetEnemy(player === 1 ? 2 : 1);
			const range = Engine.QueryInterface(SYSTEM_ENTITY, IID_RangeManager);
			range.SetLosRevealAll(player, true);
		}
		if (this.mode === "campaign")
			this.BuildCampaignScene();
		else
			this.BuildBattleScene();
		this.timer = Engine.QueryInterface(SYSTEM_ENTITY, IID_Timer).SetInterval(SYSTEM_ENTITY, IID_KtwController, "Tick", 1000, 1000, null);
	}
	catch (e)
	{
		this.error = String(e.message || e);
		error("KTW initialization: " + this.error);
	}
};

KtwController.prototype.Spawn = function(template, owner, x, z, angle)
{
	const id = Engine.AddEntity(template);
	if (id === INVALID_ENTITY)
		throw new Error("KTW_TEMPLATE: " + template);
	const position = Engine.QueryInterface(id, IID_Position);
	if (position)
	{
		position.JumpTo(x, z);
		position.SetYRotation(angle || 0);
	}
	const ownership = Engine.QueryInterface(id, IID_Ownership);
	if (ownership)
		ownership.SetOwner(owner);
	return id;
};

KtwController.prototype.ProvincePoint = function(province)
{
	return {
		x: this.worldSize * (0.12 + 0.76 * province.mapPosition.x),
		z: this.worldSize * (0.12 + 0.76 * province.mapPosition.z)
	};
};

KtwController.prototype.BuildCampaignScene = function()
{
	for (const marker of this.markers)
		Engine.DestroyEntity(marker.entity);
	this.markers = [];
	for (const province of this.state.provinces)
	{
		const point = this.ProvincePoint(province);
		const owner = province.owner === "kazakh" ? 1 : 2;
		const entity = this.Spawn("structures/ktw/settlement", owner, point.x, point.z, 0);
		this.markers.push({ entity, provinceId: province.id, kind: "province", x: point.x, z: point.z });
	}
	for (const army of this.state.armies)
	{
		if (!KtwCampaign.soldiers(army))
			continue;
		const province = this.state.provinces.find(p => p.id === army.province);
		const point = this.ProvincePoint(province);
		const entity = this.Spawn("units/ktw/army_marker", army.faction === "kazakh" ? 1 : 2, point.x + 19, point.z + 16, -Math.PI / 4);
		this.markers.push({ entity, armyId: army.id, provinceId: province.id, kind: "army", x: point.x + 19, z: point.z + 16 });
	}
};

KtwController.prototype.BuildBattleScene = function()
{
	if (!this.state.pendingBattle)
		throw new Error("KTW_NO_BATTLE");
	this.units = [];
	this.regiments = [];
	this.commanders = [];
	for (const army of this.state.pendingBattle.armies)
	{
		let commanderAssigned = false;
		const owner = army.faction === "kazakh" ? 1 : 2;
		const facing = owner === 1 ? 0 : Math.PI;
		const rows = army.regiments.length;
		for (let r = 0; r < rows; ++r)
		{
			const regiment = army.regiments[r];
			const info = {
				id: regiment.id, type: regiment.type, faction: army.faction,
				initial: regiment.count, morale: regiment.morale, fatigue: regiment.fatigue,
				routed: false, entities: []
			};
			const column = r % 3;
			const line = Math.floor(r / 3);
			const cavalry = ["mounted_archer", "light_cavalry", "heavy_cavalry"].includes(regiment.type);
			const spacing = cavalry ? 3.4 : 2.4;
			for (let i = 0; i < regiment.count; ++i)
			{
				const x = this.worldSize / 2 + (column - 1) * 44 + (i % 6 - 2.5) * spacing;
				const z = this.worldSize * (owner === 1 ? 0.38 : 0.62) + (line * 24 + Math.floor(i / 6) * spacing) * (owner === 1 ? -1 : 1);
				const entity = this.Spawn("units/ktw/" + regiment.type, owner, x, z, facing);
				info.entities.push(entity);
				this.units.push({ entity, regimentId: regiment.id, owner, type: regiment.type });
				// One existing warrior represents the commander: troop totals stay
				// exact, while his fate comes from real engine Health, not RNG.
				if (!commanderAssigned && army.commander)
				{
					this.commanders.push({ characterId: army.commander, armyId: army.id, entity });
					commanderAssigned = true;
				}
				const unitAI = Engine.QueryInterface(entity, IID_UnitAI);
				if (unitAI)
					unitAI.SwitchToStance(owner === 1 ? "defensive" : "aggressive");
			}
			this.regiments.push(info);
		}
	}
	this.UpdateBattleStats();
};

KtwController.prototype.IsAlive = function(entity)
{
	const health = Engine.QueryInterface(entity, IID_Health);
	return !!health && health.GetHitpoints() > 0;
};

KtwController.prototype.UpdateBattleStats = function()
{
	const stats = { kazakh: 0, abulkhair: 0, seconds: this.elapsed, regiments: [] };
	for (const regiment of this.regiments)
	{
		const remaining = regiment.entities.filter(entity => this.IsAlive(entity)).length;
		stats[regiment.faction] += remaining;
		stats.regiments.push({ id: regiment.id, type: regiment.type, faction: regiment.faction,
			remaining, initial: regiment.initial, morale: regiment.morale, fatigue: regiment.fatigue, routed: regiment.routed });
	}
	this.battleStats = stats;
	return stats;
};

KtwController.prototype.Tick = function()
{
	if (this.mode !== "battle" || this.transition || !this.state || !this.state.pendingBattle || this.error.indexOf("KTW_LOAD_RECOVERY_REQUIRED") === 0)
		return;
	++this.elapsed;
	const stats = this.UpdateBattleStats();
	if (!stats.kazakh || !stats.abulkhair)
	{
		this.FinishBattle(stats.kazakh ? "kazakh" : stats.abulkhair ? "abulkhair" : "draw");
		return;
	}
	const ownLiving = this.units.filter(u => u.owner === 1 && this.IsAlive(u.entity));
	for (const regiment of this.regiments)
	{
		const living = regiment.entities.filter(entity => this.IsAlive(entity));
		const proportion = living.length / Math.max(1, regiment.initial);
		regiment.morale = Math.max(0, Math.round(80 - (1 - proportion) * 85));
		// Running consumes stamina; stationary units recover. This is intentionally small and deterministic.
		const moving = living.some(entity => {
			const motion = Engine.QueryInterface(entity, IID_UnitMotion);
			return motion && motion.GetCurrentSpeed() > 1;
		});
		regiment.fatigue = Math.max(0, Math.min(100, regiment.fatigue + (moving ? 0.5 : -0.4)));
		if (proportion < 0.22 && this.elapsed > 12)
			regiment.routed = true;
		for (const entity of living)
		{
			const motion = Engine.QueryInterface(entity, IID_UnitMotion);
			if (motion)
				motion.SetSpeedMultiplier(1 - regiment.fatigue * 0.0025);
			const ai = Engine.QueryInterface(entity, IID_UnitAI);
			if (!ai)
				continue;
			if (regiment.routed)
			{
				ai.Walk(this.worldSize / 2, this.worldSize * (regiment.faction === "kazakh" ? 0.14 : 0.86), false);
				continue;
			}
			if (regiment.faction !== "abulkhair" || this.elapsed < 6 || this.elapsed % 5 !== 1)
				continue;
			const pos = Engine.QueryInterface(entity, IID_Position).GetPosition2D();
			let nearest = null, distance = Infinity;
			for (const target of ownLiving)
			{
				const targetPos = Engine.QueryInterface(target.entity, IID_Position);
				if (!targetPos || !targetPos.IsInWorld())
					continue;
				const p = targetPos.GetPosition2D();
				const d = (p.x - pos.x) ** 2 + (p.y - pos.y) ** 2;
				if (d < distance) { nearest = { entity: target.entity, point: p }; distance = d; }
			}
			if (!nearest)
				continue;
			if (regiment.type === "mounted_archer" && distance < 28 * 28 && this.elapsed % 15 < 6)
			{
				const dx = pos.x - nearest.point.x, dz = pos.y - nearest.point.y;
				const len = Math.max(1, Math.sqrt(dx * dx + dz * dz));
				ai.Walk(Math.max(24, Math.min(this.worldSize - 24, pos.x + dx / len * 35)), Math.max(24, Math.min(this.worldSize - 24, pos.y + dz / len * 35)), false);
			}
			else
				ai.Attack(nearest.entity, true, false);
		}
	}
	const active = faction => this.regiments.some(r => r.faction === faction && !r.routed && r.entities.some(e => this.IsAlive(e)));
	if (!active("kazakh") || !active("abulkhair"))
		this.FinishBattle(active("kazakh") ? "kazakh" : active("abulkhair") ? "abulkhair" : "draw");
};

KtwController.prototype.FinishBattle = function(winner)
{
	if (!this.state.pendingBattle || this.transition)
		return;
	const survivors = {};
	for (const regiment of this.regiments)
		survivors[regiment.id] = regiment.entities.filter(entity => this.IsAlive(entity)).length;
	const result = { battleId: this.state.pendingBattle.id, winner, survivors };
	if (this.commanders && this.commanders.length)
	{
		result.commanderOutcomes = {};
		for (const commander of this.commanders)
			result.commanderOutcomes[commander.characterId] = this.IsAlive(commander.entity) ? "alive" : "dead";
	}
	try
	{
		KtwCampaign.resolveBattle(this.state, result);
		this.lastResult = result;
		this.UpdateBattleStats();
		this.transition = "campaign";
	}
	catch (e)
	{
		// Transaction failed: retain pending battle and its units for a save or
		// retry; never transition to an inconsistent campaign.
		this.error = String(e.message || e);
	}
};

KtwController.prototype.Command = function(player, cmd)
{
	if (player !== 1 || !this.state || this.transition || this.error.indexOf("KTW_LOAD_RECOVERY_REQUIRED") === 0)
		return;
	this.error = "";
	try
	{
		if (this.mode === "battle")
		{
			if (cmd.action === "surrender")
				this.FinishBattle("abulkhair");
			else
				throw new Error("KTW_BATTLE_COMMAND");
			return;
		}
		switch (cmd.action)
		{
		case "select": KtwCampaign.select(this.state, cmd.armyId, cmd.provinceId); break;
		case "move": KtwCampaign.moveArmy(this.state, cmd.armyId || "kazakh_main", cmd.provinceId); break;
		case "endTurn": KtwCampaign.endTurn(this.state); break;
		case "recruit":
			if (!["mounted_archer", "light_cavalry", "heavy_cavalry", "spearman", "infantry_archer"].includes(cmd.unitType))
				throw new Error("KTW_UNIT_NOT_IMPLEMENTED");
			KtwCampaign.recruit(this.state, cmd.armyId || "kazakh_main", cmd.unitType, cmd.count === undefined ? 20 : cmd.count);
			break;
		case "build": KtwCampaign.build(this.state, cmd.provinceId, cmd.kind); break;
		case "diplomacy": KtwCampaign.diplomacy(this.state, cmd.proposal); break;
		case "autoresolve": KtwCampaign.autoresolve(this.state); break;
		case "retreat": KtwCampaign.retreat(this.state); break;
		case "fight":
			if (!this.state.pendingBattle) throw new Error("KTW_NO_BATTLE");
			this.transition = "battle";
			break;
		default: throw new Error("KTW_UNKNOWN_COMMAND");
		}
		if (!this.transition)
			this.BuildCampaignScene();
	}
	catch (e)
	{
		this.error = String(e.message || e);
	}
};

KtwController.prototype.GetState = function()
{
	const recovering = this.error.indexOf("KTW_LOAD_RECOVERY_REQUIRED") === 0;
	return {
		mode: this.mode, state: this.state, transition: this.transition, error: this.error,
		markers: this.markers, battleStats: this.battleStats, lastResult: this.lastResult,
		council: this.state && this.state.schemaVersion === 2 && !recovering ? KtwCampaign.describeCouncil(this.state, "kazakh") : null,
		commanders: (recovering ? [] : this.commanders || []).map(c => ({ characterId: c.characterId, armyId: c.armyId, entity: c.entity, alive: this.IsAlive(c.entity) }))
	};
};

// Extend the stable GUI gateway without copying its 2,000+ line upstream file.
const KtwBaseScriptCall = GuiInterface.prototype.ScriptCall;
GuiInterface.prototype.ScriptCall = function(player, name, args)
{
	if (name === "KtwGetState")
		return Engine.QueryInterface(SYSTEM_ENTITY, IID_KtwController).GetState();
	return KtwBaseScriptCall.call(this, player, name, args);
};

Engine.RegisterSystemComponentType(IID_KtwController, "KtwController", KtwController);
