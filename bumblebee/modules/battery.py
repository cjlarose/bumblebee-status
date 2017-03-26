# pylint: disable=C0111,R0903

"""Displays battery status, remaining percentage and charging information.

Parameters:
    * battery.device  : The device to read information from (defaults to BAT0)
    * battery.warning : Warning threshold in % of remaining charge (defaults to 20)
    * battery.critical: Critical threshold in % of remaining charge (defaults to 10)
"""

import os

import bumblebee.input
import bumblebee.output
import bumblebee.engine

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        super(Module, self).__init__(engine, config,
            bumblebee.output.Widget(full_text=self.charge)
        )
        battery = self.parameter("device", "BAT0")
        self._path = "/sys/class/power_supply/{}".format(battery)
        self._charge = 1.0
        self._ac = False

    def charge(self, widget):
        if self._ac:
            return "ac"
        if self._charge is None:
            return "n/a"
        return "{0:.0f}%".format(self._charge * 100)

    def update(self, widgets):
        widget = widgets[0]
        self._ac = False
        if not os.path.exists(self._path):
            self._ac = True
            self._charge = 1
            return

        try:
            with open(os.path.join(self._path, 'charge_full')) as f:
                capacity = int(f.read())
            with open(os.path.join(self._path, 'charge_now')) as f:
                charge = float(f.read())
            self._charge = min(charge / capacity, 1)
        except IOError:
            self._charge = None

    def state(self, widget):
        state = []

        if self._charge < 0.01:
            return ["critical", "unknown"]

        if self._charge < float(self.parameter("critical", 10)) / 100:
            state.append("critical")
        elif self._charge < float(self.parameter("warning", 20)) / 100:
            state.append("warning")

        if self._ac:
            state.append("AC")
        else:
            charge = ""
            with open(self._path + "/status") as f:
                charge = f.read().strip()
            if charge == "Discharging":
                state.append("discharging-{}".format(min([10, 25, 50, 80, 100] , key=lambda i:abs(i - self._charge * 100))))
            else:
                if self._charge > 0.95:
                    state.append("charged")
                else:
                    state.append("charging")

        return state

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
