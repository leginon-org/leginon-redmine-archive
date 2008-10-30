# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import copy
import math
import tem

class SimTEM(tem.TEM):
    name = 'SimTEM'
    def __init__(self):
        tem.TEM.__init__(self)

        self.high_tension = 120000.0

        self.magnifications = [
            50.0,
            100.0,
            500.0,
            1000.0,
            5000.0,
            25000.0,
            50000.0,
        ]
        self.magnification_index = 0

        self.stage_axes = ['x', 'y', 'z', 'a']
        self.stage_range = {
            'x': (-1e-3, 1e-3),
            'y': (-1e-3, 1e-3),
            'z': (-5e-4, 5e-4),
            'a': (-math.pi/2, math.pi/2),
        }
        self.stage_position = {}
        for axis in self.stage_axes:
            self.stage_position[axis] = 0.0

        self.screen_current = 0.000001
        self.intensity_range = (0.0, 1.0)
        self.intensity = 0.0

        self.stigmators = {
            'condenser': {
                'x': 0.0,
                'y': 0.0,
            },
            'objective': {
                'x': 0.0,
                'y': 0.0,
            },
            'diffraction': {
                'x': 0.0,
                'y': 0.0,
                },
        }

        self.spot_sizes = range(1, 11)
        self.spot_size = self.spot_sizes[0]

        self.beam_tilt = {'x': 0.0, 'y': 0.0}
        self.beam_shift = {'x': 0.0, 'y': 0.0}
        self.image_shift = {'x': 0.0, 'y': 0.0}
        self.raw_image_shift = {'x': 0.0, 'y': 0.0}

        self.focus = 0.0
        self.zero_defocus = 0.0

        self.main_screen_scale = 1.0

        self.main_screen_positions = ['up', 'down']
        self.main_screen_position = self.main_screen_positions[0]

    def getHighTension(self):
        return self.high_tension

    def setHighTension(self, value):
        self.high_tension = value

    def getStagePosition(self):
        return copy.copy(self.stage_position)

    def setStagePosition(self, value):
        for axis in self.stage_axes:
            try:
                if value[axis] < self.stage_range[axis][0]:
                    raise ValueError('Stage position %s out of range' % axis)
                if value[axis] > self.stage_range[axis][1]:
                    m = 'invalid stage position for %s axis'
                    raise ValueError(m % axis)
            except KeyError:
                pass

        for axis in self.stage_axes:
            try:
                self.stage_position[axis] = value[axis]
            except KeyError:
                pass

    def normalizeLens(self, lens='all'):
        pass

    def getScreenCurrent(self):
        return self.screen_current
    
    def getIntensity(self):
        return self.intensity
    
    def setIntensity(self, value):
        if value < self.intensity_range[0] or value > self.intensity_range[1]:
            raise ValueError('invalid intensity')

    def getStigmator(self):
        return copy.deepcopy(self.stigmators)
        
    def setStigmator(self, value):
        for key in self.stigmators.keys():
            for axis in self.stigmators[key].keys():
                try:
                    self.stigmators[key][axis] = value[key][axis]
                except KeyError:
                    pass

    def getSpotSize(self):
        return self.spot_size
    
    def setSpotSize(self, value):
        if value not in self.spot_sizes:
            raise ValueError('invalid spot size')
        self.spot_size = value
    
    def getBeamTilt(self):
        return copy.copy(self.beam_tilt)
    
    def setBeamTilt(self, value):
        for axis in self.beam_tilt.keys():
            try:
                self.beam_tilt[axis] = value[axis]
            except KeyError:
                pass
    
    def getBeamShift(self):
        return copy.copy(self.beam_shift)

    def setBeamShift(self, value):
        for axis in self.beam_shift.keys():
            try:
                self.beam_shift[axis] = value[axis]
            except KeyError:
                pass
    
    def getImageShift(self):
        return copy.copy(self.image_shift)
    
    def setImageShift(self, value):
        for axis in self.image_shift.keys():
            try:
                self.image_shift[axis] = value[axis]
            except KeyError:
                pass
    
    def getRawImageShift(self):
        return copy.copy(self.raw_image_shift)
    
    def setRawImageShift(self, value):
        for axis in self.raw_image_shift.keys():
            try:
                self.raw_image_shift[axis] = value[axis]
            except KeyError:
                pass
    
    def getDefocus(self):
        return self.focus - self.zero_defocus
    
    def setDefocus(self, value):
        self.focus = value + self.zero_defocus
    
    def resetDefocus(self):
        self.zero_defocus = self.focus

    def getMagnification(self, index=None):
        if index is None:
            index = self.magnification_index
        try:
            return self.magnifications[index]
        except IndexError:
            raise ValueError('invalid magnification')

    def getMainScreenMagnification(self, index=None):
        return self.main_screen_scale*self.getMagnification(index=index)

    def getMainScreenScale(self):
        return self.main_screen_scale

    def setMainScreenScale(self, value):
        self.main_screen_scale = value

    def setMagnification(self, value):
        try:
            self.magnification_index = self.magnifications.index(float(value))
        except ValueError:
            raise ValueError('invalid magnification')

    def getMagnificationIndex(self, magnification=None):
        if magnification is not None:
            return self.magnifications.index(magnification)
        return self.magnification_index

    def setMagnificationIndex(self, value):
        if value < 0 or value >= len(self.magnifications):
            raise ValueError('invalid magnification index')
        self.magnification_index = value

    def getMagnifications(self):
        return list(self.magnifications)

    def getMainScreenPositions(self):
        return list(self.main_screen_positions)

    def getMainScreenPosition(self):
        return self.main_screen_position

    def setMainScreenPosition(self, value):
        if value not in self.main_screen_positions:
            raise ValueError('invalid main screen position')
        self.main_screen_position = value

    def getFocus(self):
        return self.focus

    def setFocus(self, value):
        self.focus = value

    def runBufferCycle(self):
        pass

