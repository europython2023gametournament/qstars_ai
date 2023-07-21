# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from dataclasses import dataclass, field
from pprint import pp

# This is your team name
CREATOR = "QStars"


@dataclass
class Vehicle:
    uid: str
    base_uid: str

    type: str = ""

    position = np.array([0, 0])
    distance_since_last_dir = 0
    distance_since_last_dir_longest = 0

    def update_current_obj(self, obj):
        pass

    def distance_to(self, x, y):
        pass
        # get own position

        # calc distance to x, y


vehicles: dict[str, Vehicle] = {}


@dataclass
class Base:
    uid: str

    tanks: list[str] = field(default_factory=list)
    ships: list[str] = field(default_factory=list)
    jets: list[str] = field(default_factory=list)

    def build_tank(self, base):
        if base.crystal > base.cost("tank"):
            # build_tank() returns the uid of the tank that was built
            tank_uid = base.build_tank(heading=0)
            self.tanks.append(tank_uid)
            vehicles[tank_uid] = Vehicle(uid=tank_uid, base_uid=base.uid)
            return tank_uid

    def build(self, base):
        """base build decision tree."""

        seen_uids = set()

        # first make sure we build mines
        if base.mines < 2:
            if base.crystal > base.cost("mine"):
                base.build_mine()
        elif base.crystal > base.cost("tank") and len(self.tanks) < 1:
            seen_uids.add(self.build_tank(base))
        elif len(self.jets) < 2 and base.crystal > base.cost("jet"):
            jet_uid = base.build_jet(heading=360 * np.random.random())
            self.jets.append(jet_uid)

            vehicles[jet_uid] = Vehicle(uid=jet_uid, base_uid=base.uid)
            seen_uids.add(jet_uid)

        return seen_uids


bases: dict[Base] = {}


# This is the AI bot that will be instantiated for the competition
class PlayerAi:
    def __init__(self):
        self.team = CREATOR  # Mandatory attribute

        self.uid_lookup: dict[Vehicle | Base] = {}

    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        # Get information about my team
        myinfo = info[self.team]
        # to later remove obects that no longer exist, to be able to upkeep the army
        seen_uids = set()

        # loop over the bases in info
        for info_base in myinfo["bases"]:
            # seen_uids.add(info_base.uid)

            if not info_base.uid in bases:
                bases[info_base.uid] = Base(uid=info_base.uid)

            base = bases[info_base.uid]

            new_vehicles = base.build(base=info_base)

            seen_uids = seen_uids | new_vehicles

        # loop over all vehicles once. Remove the vehicles that no longer exist and update the current objects
        if "tanks" in myinfo:
            for tank in myinfo["tanks"]:
                seen_uids.add(tank.uid)
                vehicles[tank.uid].update_current_obj(tank)

        if "ships" in myinfo:
            for ship in myinfo["ships"]:
                seen_uids.add(ship.uid)
                vehicles[ship.uid].update_current_obj(ship)

        if "jets" in myinfo:
            for jet in myinfo["jets"]:
                seen_uids.add(jet.uid)
                vehicles[jet.uid].update_current_obj(jet)

        # remove the vehicles that no longer exist

        # get the difference between seen_uids and vehicles
        dead = set(vehicles.keys()) - seen_uids

        # remove the dead vehicles
        for uid in dead:
            del vehicles[uid]

        # loop over enemies and set the targets for vehicles
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    if "bases" in info[name]:
                        for base in info[name]["bases"]:
                            pass

                    # if the target is a base, direct the closest jet

                    # if the target is a near a tank, direct the tanks at it

                    pass
                # Target only bases
                # if "bases" in info[name]:
                #     # Simply target the first base
                #     t = info[name]["bases"][0]
                #     target = [t.x, t.y]

        # loop over all vehicles that have no target and resume normal operations
