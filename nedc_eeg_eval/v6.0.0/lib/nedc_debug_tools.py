#!/usr/bin/env python
#
# file: $NEDC_NFC/class/python/nedc_sys_tools/nedc_debug_tools.py
#                                                                              
# revision history:
#
# 20250128 (SP): added set_seed() method to Dbgl class
# 20241003 (JP): added a log function to timestamp programs
# 20230622 (AB): refactored code to new comment format
# 20200531 (JP): refactored code
# 20200514 (JP): initial version
#                                                                              
# This file contains classes that facilitate debugging and information display.
#------------------------------------------------------------------------------

# import system modules
#
import os
import random
import sys
import time

import numpy as np
from numpy.random import default_rng

# import NEDC modules
#

#------------------------------------------------------------------------------
#                                                                              
# global variables are listed here                                             
#                                                                              
#------------------------------------------------------------------------------

# define a numerically ordered list of 'levels'
#
NONE = int(0)
BRIEF = int(1)
SHORT = int(2)
MEDIUM = int(3)
DETAILED = int(4)
FULL = int(5)

# define a dictionary indexed by name and reverse it so we have it by level
#
LEVELS = {'NONE': NONE, 'BRIEF': BRIEF, 'SHORT': SHORT,
          'MEDIUM': MEDIUM, 'DETAILED': DETAILED, 'FULL': FULL}
NAMES = {val: key for key, val in LEVELS.items()}

# define a constant that controls the amount of precision used
# to check floating point numbers. we use two constants - max precision
# for detailed checks and min precision for curosry checks.
#
MIN_PRECISION = int(4)
MAX_PRECISION = int(10)

# define a constant that is used to seed random number generators
# from a common starting point
#
RANDSEED = int(27)

# define a newline delimiter
#
DELIM_EQUAL = '='
DELIM_NEWLINE = '\n'

#------------------------------------------------------------------------------
#
# classes are listed here
#
#------------------------------------------------------------------------------
                                                                         
class __NAME__(object):
    """
    Class: __NAME__
    
    arguments:
     none

    description: 
     This class is used to get the function name. This is analogous to
     __NAME__ in C++. This class is hidden from the user.
    """
    # method: default constructor
    #
    #    def __init__(self):
    #        pass

    def __repr__(self):
        """
        method: __repr__
        
        arguments:
         none

        return: 
         none

        description: 
         a built-in function that returns an object representation
        """
        try:
            raise Exception
        except:
            return str(sys.exc_info()[2].tb_frame.f_back.f_code.co_name)

#
# end of class
                                                                          
class __LINE__(object):
    """
    Class: __LINE__
    
    arguments:
     none

    description: 
     This class is used to get the line number. This is analogous to
     __LINE__ in C++. This clas is hidden from the user.
    """

    # method: a built-in function that returns an object representation
    #
    def __repr__(self):
        try:
            raise Exception
        except:
            return str(sys.exc_info()[2].tb_frame.f_back.f_lineno)

#
# end of class

# define an abbreviations for the above classes:
#  These have to come after the class definitions, and are the symbols
#  that programmers will use.
#
# define an abbreviation for the above class:
#  __FILE__ must unfortunately be put in each file.
#
__NAME__ = __NAME__()
__LINE__ = __LINE__()
__FILE__ = os.path.basename(__file__)

class Dbgl:
    """
    Class: Dbgl
    
    arguments:
     none

    description: 
     This class is a parallel implementation of our C++ class Dbgl. Please see
     $NEDC_NFC/class/cpp/Dbgl/Dbgl.h for more information about this class. The
     definitions here need to be exactly the same as those in that class.
     
     Note that we prefer to manipulate this class using integer values
     rather than strings. Strings are only really used for the command line
     interface. All other operations should be done on integers.
    """

    #--------------------------------------------------------------------------
    #
    # static data declarations
    #
    #--------------------------------------------------------------------------

    # define a static variable to hold the value
    #
    level_d = NONE

    #--------------------------------------------------------------------------
    #
    # constructors
    #
    #--------------------------------------------------------------------------

    def __init__(self):
        """
        method: constructor
        
        arguments:
         none

        return: 
         none

        description: 
         note this method cannot set the value or this overrides
         values set elsewhere in a program. the set method must be called.
        """
         
        Dbgl.__CLASS_NAME__ = self.__class__.__name__
        
        # set the seed for random number generators to a common value so
        # that we can reproduce results
        #
        self.set_seed(value = RANDSEED)
    
    #--------------------------------------------------------------------------
    #
    # operator overloads:
    #  we keep the definitions concise
    #
    #--------------------------------------------------------------------------

    def __int__(self):
        """
        method: int()
        
        arguments:
         none

        return: 
         none

        description: 
         cast conversion to int

        """
         
        return int(self.level_d)

    def __gt__(self, level):
        """
        method: >
        
        arguments:
         none

        return: 
         none

        description: 
         overload > (greater than) operator
        """
         
        if Dbgl.level_d > level:
            return True
        return False

    def __ge__(self, level):
        """
        method: >=
        
        arguments:
         none

        return: 
         none

        description: 
         overload >= (greater than or equal to) operator
         none
        """
         
        if Dbgl.level_d >= level:
            return True
        return False

    def __ne__(self, level):
        """
        method: !=
        
        arguments:
         none

        return: 
         none

        description: 
         overload != (not equal to) operator
        """
         
        if Dbgl.level_d != level:
            return True
        return False

    def __lt__(self, level):
        """
        method: <
        
        arguments:
         none

        return: 
         none

        description: 
         overload < (less than) operator
        """
         
        if Dbgl.level_d < level:
            return True
        return False

    def __le__(self, level):
        """
        method: <=
        
        arguments:
         none

        return: 
         none

        description: 
         overload <= (less than or equal to) operator
        """
         
        if Dbgl.level_d <= level:
            return True
        return False

    def __eq__(self, level):
        """
        method: ==
        
        arguments:
         none

        return: 
         none

        description: 
         overload == (equal to) operator
        """
         
        if Dbgl.level_d == level:
            return True
        return False

    #--------------------------------------------------------------------------
    #
    # set and get methods
    #
    #--------------------------------------------------------------------------

    def set(self, level = None, name = None):
        """
        method: set
        
        arguments:
         none

        return: 
         none
 
        description: 
         none
        """
 
        # check and set the level by value
        #
        if level is not None:
            if self.check(level) == False:
                print("Error: %s (line: %s) %s::%s: invalid value (%d)" %
                      (__FILE__, __LINE__, Dbgl.__CLASS_NAME__, __NAME__,
                       level))
                sys.exit(os.EX_SOFTWARE)
            else:
                Dbgl.level_d = int(level)

        # check and set the level by name
        #
        elif name is not None:
            try:
                Dbgl.level_d = LEVELS[name.upper()]
            except KeyError as e:
                print("Error: %s (line: %s) %s::%s: invalid value (%s)" %
                      (__FILE__, __LINE__, Dbgl.__CLASS_NAME__, __NAME__,
                       name))
                sys.exit(os.EX_SOFTWARE)

        # if neither is specified, set to NONE
        #
        else:
            Dbgl.level_d = NONE

        # exit gracefully
        #
        return Dbgl.level_d
    
    def set_seed(self, value: int) -> None:
        """
        method: set_seed
        arguments:
         value: the seed value
        return:
         none
        description:
         This method sets the seed for random number generators.
        """
        
        # set the seed for Python's random number generators
        #
        random.seed(value)
        # set the seed for numpy's random number generators
        #
        np.random.seed(value)
        # set the seed for numpy's random number generators
        rng = default_rng(value)
        
        # set the seed for Python's hash function
        #
        os.environ['PYTHONHASHSEED'] = str(value)
        
        # exit gracefully
        #
        return rng
        
    def get(self):
        """
        method: get
        
        arguments:
         none

        return: 
         none

        description: 
         note that we don't provide a method to return the integer value
         because int(), a pseudo-cast operator, can do this.
        """
         
        return NAMES[Dbgl.level_d]

    def check(self, level):
        """
        method: check
        
        arguments:
         none

        return: 
         none

        description: 
         none

        """
         
        if (level < NONE) or (level > FULL):
            return False;
        else:
            return True

    #--------------------------------------------------------------------------
    #
    # miscellaneous methods
    #
    #--------------------------------------------------------------------------

    def log(self, fname, version):

        """
        method: log
        
        arguments:
         fname: the filename to be timestamped
         version: the user-defined version of the software

        return: 
         a string containing the log message

        description: 
         this method produces a standard log message that is used
         to timestamp programs.

        """

        # convert the filename to an absolute path:
        #  this displays the path in a user-friendly way
        #
        aname = os.path.abspath(os.path.expanduser(os.path.expandvars(fname)))

        # add a preamble
        #
        str = DELIM_EQUAL * 78 + DELIM_NEWLINE

        # print out various timestamps for the executable
        #
        aname_ctime = time.ctime(os.path.getmtime(fname))
        str += "     Date: %s" % (time.strftime("%c") + DELIM_NEWLINE)
        str += "     File: %s" % (aname + DELIM_NEWLINE)
        str += "  Version: %s" % (version + DELIM_NEWLINE)
        str += " Mod Time: %s" % (aname_ctime + DELIM_NEWLINE)

        # add an epilogue
        #
        str += DELIM_EQUAL * 78 + DELIM_NEWLINE

        # exit gracefully
        #
        return str

#
# end of class

class Vrbl:
    """
    Class: Vrbl
    
    arguments:
     none

    description: 
     This class is a parallel implementation of our C++ class Vrbl. Please see
     $NEDC_NFC/class/cpp/Vrbl/Vrbl.h for more information about this class. The
     definitions here need to be exactly the same as those in that class.
    """

    #--------------------------------------------------------------------------
    #
    # static data declarations
    #
    #--------------------------------------------------------------------------

    # define a static variable to hold the value
    #
    level_d = NONE

    #--------------------------------------------------------------------------
    #
    # constructors
    #
    #--------------------------------------------------------------------------

    def __init__(self):
        """
        method: constructor
        
        arguments:
         none

        return: 
         none

        description: 
         note this method cannot set the value or this overrides
         values set elsewhere in a program. the set method must be called.
        """
         
        Vrbl.__CLASS_NAME__ = self.__class__.__name__
    
    #--------------------------------------------------------------------------
    #
    # operator overloads
    #
    #--------------------------------------------------------------------------

    def __int__(self):
        """
        method: int()
        
        arguments:
         none
 
        return: 
         none

        description: 
         cast conversion to int
        """
         
        return int(self.level_d)

    def __gt__(self, level):
        """
        method: >
        
        arguments:
         none

        return: 
         none

        description: 
         overload > (greater than) operator
        """
         
        if Vrbl.level_d > level:
            return True
        return False

    def __ge__(self, level):
        """
        method: >=
        
        arguments:
         none

        return: 
         none

        description: 
         overload >= (greater than or equal to) operator
        """
         
        if Vrbl.level_d >= level:
            return True
        return False

    def __ne__(self, level):
        """
        method: !=
        
        arguments:
         none

        return: 
         none

        description: 
         overload != (not equal to) operator
        """
         
        if Vrbl.level_d != level:
            return True
        return False

    def __lt__(self, level):
        """
        method: <
        
        arguments:
         none

        return: 
         none

        description: 
         overload < (less than) operator
        """
         
        if Vrbl.level_d < level:
            return True
        return False

    def __le__(self, level):
        """
        method: <=
        
        arguments:
         none

        return: 
         none

        description: 
         overload <= (less than or equal to) operator
        """
         
        if Vrbl.level_d <= level:
            return True
        return False

    def __eq__(self, level):
        """
        method: ==
        
        arguments:
         none

        return: 
         none

        description: 
         overload == (equal to) operator
        """
         
        if Vrbl.level_d == level:
            return True
        return False

    #--------------------------------------------------------------------------
    #
    # set and get methods
    #
    #--------------------------------------------------------------------------

    def set(self, level = None, name = None):
        """
        method: set
        
        arguments:
         none

        return: 
         none

        description: 
         none
        """
 
        # check and set the level by value
        #
        if level is not None:
            if self.check(level) == False:
                print("Error: %s (line: %s) %s::%s: invalid value (%d)" %
                      (__FILE__, __LINE__, Vrbl.__CLASS_NAME__, __NAME__,
                       level))
                sys.exit(os.EX_SOFTWARE)
            else:
                Vrbl.level_d = int(level)

        # check and set the level by name
        #
        elif name is not None:
            try:
                Vrbl.level_d = LEVELS[name.upper()]
            except KeyError as e:
                print("Error: %s (line: %s) %s::%s: invalid value (%s)" %
                      (__FILE__, __LINE__, Vrbl.__CLASS_NAME__, __NAME__,
                       name))
                sys.exit(os.EX_SOFTWARE)

        # if neither is specified, set to NONE
        #
        else:
            Vrbl.level_d = NONE

        # exit gracefully
        #
        return Vrbl.level_d

    def get(self):
        """
        method: get
        
        arguments:
         none

        return: 
         none

        description: 
         note that we don't provide a method to return the integer value
         because int(), a pseudo-cast operator, can do this.
        """
         
        return NAMES[Vrbl.level_d]

    # method: Vrbl::check
    # 
    def check(self, level):
        """
        method: check
        
        arguments:
         none

        return: 
         none

        description: 
         none
        """
         
        if (level < NONE) or (level > FULL):
            return False;
        else:
            return True

#
# end of class

#                                                                              
# end of file 

