# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from dataclasses import dataclass, field
from math import sqrt

# This is your team name
CREATOR = "QStars"


@dataclass
class Vehicle:
    uid: str
    base_uid: str

    type: str = ""
    obj = None
    target = None

    position = np.array([0, 0])
    distance_since_last_dir = 0
    distance_since_last_dir_longest = 0

    def update_current_obj(self, obj):
        self.obj = obj

    def distance_to(self, x, y):
        if self.obj is None:
            return 99999
        dist = sqrt((x - self.obj.x) ** 2 + (y - self.obj.y) ** 2)
        return dist

    def kill(self):
        # remove from base
        if self.base_uid in bases:
            if self.uid in bases[self.base_uid].tanks:
                bases[self.base_uid].tanks.remove(self.uid)
            if self.uid in bases[self.base_uid].jets:
                bases[self.base_uid].jets.remove(self.uid)
        else:
            print("base not found")
            exit()
        del vehicles[self.uid]


vehicles: dict[str, Vehicle] = {}


@dataclass
class Base:
    uid: str

    tanks: set[str] = field(default_factory=set)
    ships: set[str] = field(default_factory=set)
    jets: set[str] = field(default_factory=set)

    def build_tank(self, base, seen_uids):
        if base.crystal > base.cost("tank"):
            # build_tank() returns the uid of the tank that was built
            tank_uid = base.build_tank(heading=360 * np.random.random())
            self.tanks.add(tank_uid)
            vehicles[tank_uid] = Vehicle(uid=tank_uid, base_uid=base.uid, type="tank")
            seen_uids.add(tank_uid)

    def build_mine(self, base):
        if base.crystal > base.cost("mine"):
            base.build_mine()

    def build_jet(self, base, seen_uids):
        if base.crystal > base.cost("jet"):
            jet_uid = base.build_jet(heading=360 * np.random.random())
            self.jets.add(jet_uid)
            vehicles[jet_uid] = Vehicle(uid=jet_uid, base_uid=base.uid, type="jet")
            seen_uids.add(jet_uid)

    def build_ship(self, base, seen_uids):
        if base.crystal > base.cost("ship"):
            ship_uid = base.build_ship(heading=360 * np.random.random())
            self.ships.add(ship_uid)
            vehicles[ship_uid] = Vehicle(uid=ship_uid, base_uid=base.uid, type="ship")
            seen_uids.add(ship_uid)

    def build(self, base):
        """base build decision tree."""

        seen_uids = set()

        # first make sure we build mines
        if base.mines < 2:
            self.build_mine(base)
        elif len(self.tanks) < 1:
            # make sure we have at least one tank defending the base
            self.build_tank(base, seen_uids)
        elif base.mines < 3:
            # increase the number of mines
            self.build_mine(base)
        elif len(self.jets) < 2:
            self.build_jet(base, seen_uids)
        elif len(self.tanks) < 3:
            # more tanks for defense
            self.build_tank(base, seen_uids)

        else:
            # keep expanding the army

            if len(self.ships) < len(self.jets):
                self.build_ship(base, seen_uids)
            elif len(self.tanks) < len(self.jets):
                self.build_tank(base, seen_uids)
            else:
                self.build_jet(base, seen_uids)

        return seen_uids


bases: dict[Base] = {}


# This is the AI bot that will be instantiated for the competition
class PlayerAi:
    def __init__(self):
        self.team = CREATOR  # Mandatory attribute

        # Record the previous positions of all my vehicles
        self.previous_positions = {}

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
            vehicles[uid].kill()

        # loop over enemies and set the targets for vehicles
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    if "bases" in info[name]:
                        # bases are priority targets
                        for base in info[name]["bases"]:
                            # find the closest vehicle to the base without a target and
                            # set the target to the base
                            closest_distance = 99999
                            closest_vehicle = None

                            for key in vehicles.keys():
                                vehicle = vehicles[key]
                                distance = vehicle.distance_to(base.x, base.y)
                                if (
                                    distance < closest_distance
                                    and vehicle.target is None
                                ):
                                    closest_distance = distance
                                    closest_vehicle = vehicle
                            if closest_vehicle is not None:
                                closest_vehicle.target = [base.x, base.y]
                    if "boats" in info[name]:
                        # boats are priority targets but only reachable by jets
                        for boat in info[name]["boats"]:
                            # find the closest vehicle to the base without a target and
                            # set the target to the base
                            closest_distance = 99999
                            closest_vehicle = None

                            for key in vehicles.keys():
                                vehicle = vehicles[key]
                                if not vehicle.type == "jet":
                                    continue
                                distance = vehicle.distance_to(base.x, base.y)
                                if (
                                    distance < closest_distance
                                    and vehicle.target is None
                                ):
                                    closest_distance = distance
                                    closest_vehicle = vehicle
                            if closest_vehicle is not None:
                                closest_vehicle.target = [boat.x, boat.y]

                    if "tanks" in info[name]:
                        for tank in info[name]["tanks"]:
                            closest_distance = 99999
                            closest_vehicle = None

                            for key in vehicles.keys():
                                vehicle = vehicles[key]
                                if not vehicle.type == "tank":
                                    continue
                                distance = vehicle.distance_to(tank.x, tank.y)
                                if (
                                    distance < closest_distance
                                    and vehicle.target is None
                                ):
                                    closest_distance = distance
                                    closest_vehicle = vehicle
                            if closest_vehicle is not None:
                                closest_vehicle.target = [tank.x, tank.y]

                    if "jets" in info[name]:
                        for jet in info[name]["jets"]:
                            closest_distance = 99999
                            closest_vehicle = None

                            for key in vehicles.keys():
                                vehicle = vehicles[key]
                                if not vehicle.type == "jet" or vehicle.type == "tank":
                                    continue
                                distance = vehicle.distance_to(jet.x, jet.y)
                                if (
                                    distance < closest_distance
                                    and vehicle.target is None
                                ):
                                    closest_distance = distance
                                    closest_vehicle = vehicle
                            if closest_vehicle is not None:
                                closest_vehicle.target = [jet.x, jet.y]

        # loop over all vehicles that have no target and resume normal operations

        # Iterate through all my tanks
        # tanks stay at the base and defend it. If it hasn't got a target, it will scan
        if "tanks" in myinfo:
            for tank in myinfo["tanks"]:
                if vehicles[tank.uid].target == None:
                    tank.set_heading((tank.heading + 45) % 360)
                else:
                    tank.goto(
                        vehicles[tank.uid].target[0], vehicles[tank.uid].target[1]
                    )

        if "jets" in myinfo:
            for jet in myinfo["jets"]:
                j = vehicles[jet.uid]
                if j.target == None:
                    j.distance_since_last_dir = j.distance_since_last_dir + 1
                    if j.distance_since_last_dir > j.distance_since_last_dir_longest:
                        j.distance_since_last_dir_longest = j.distance_since_last_dir
                        j.distance_since_last_dir = 0
                        jet.set_heading((jet.heading + 30) % 360)
                else:
                    jet.goto(j.target[0], j.target[1])

        # Iterate through all my ships
        if "ships" in myinfo:
            for ship in myinfo["ships"]:
                if ship.uid in self.previous_positions:
                    # If the ship position is the same as the previous position,
                    # convert the ship to a base if it is far from the owning base,
                    # set a random heading otherwise
                    if all(ship.position == self.previous_positions[ship.uid]):
                        if ship.get_distance(ship.owner.x, ship.owner.y) > 20:
                            ship.convert_to_base()
                        else:
                            ship.set_heading(np.random.random() * 360.0)
                # Store the previous position of this ship for the next time step
                self.previous_positions[ship.uid] = ship.position
