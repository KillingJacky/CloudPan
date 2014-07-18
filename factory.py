#!/usr/bin/python

#   Pan to MQTT gateway
#   Copyright (C) 2014 by seeedstudio
#   Author: Jack Shao (jacky.shaoxg@gmail.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


class Factory(object):
    """
    class factory, returns the appropriate class's instance given the type
    """

    classes = []

    @staticmethod
    def register(c):
        Factory.classes.append(c)

    def __new__(self, name):
        """
        Constructor, returns an instance of a filter given type
        """
        for c in self.classes:
            if c.__name__ == name:
                return c()
        return None
