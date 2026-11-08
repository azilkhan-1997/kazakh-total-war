// SPDX-License-Identifier: GPL-2.0-or-later
// Commands travel through the deterministic simulation, never through GUI mutation.
g_Commands.ktw = function(player, cmd)
{
	const controller = Engine.QueryInterface(SYSTEM_ENTITY, IID_KtwController);
	if (controller)
		controller.Command(player, cmd);
};
