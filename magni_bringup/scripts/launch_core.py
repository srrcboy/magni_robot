#!/usr/bin/python

###
# Eventually this should do something smarter, like launch sonars
# 3DTOF, etc, if they are installed.
###

import sys, os, subprocess, time
import roslaunch
import yaml

conf_path = "/etc/ubiquity/robot.yaml"

default_conf = \
{
    'raspicam' : {'position' : 'forward'},
    'sonars' : 'None'
}

def get_conf():
    try:
        with open(conf_path) as conf_file:
            conf = yaml.load(conf_file)
            if (conf is None):
                print('WARN /etc/ubiquity/robot.yaml is empty, using default configuration')
                return default_conf

            for key, value in default_conf.items():
                if key not in conf:
                    conf[key] = value

            return conf
    except IOError:
        print("WARN /etc/ubiquity/robot.yaml doesn't exist, using default configuration")
        return default_conf
    except yaml.parser.ParserError:
        print("WARN failed to parse /etc/ubiquity/robot.yaml, using default configuration")
        return default_conf

if __name__ == "__main__":
    conf = get_conf()

    if conf['sonars'] == 'pi_sonar_v1':
        conf['sonars'] = 'true'
    else:
        conf['sonars'] = 'false'

    print conf

    time.sleep(5)
    try:
        timeout = time.time() + 40 # up to 40 seconds
        while (1):
            if (time.time() > timeout): 
                print "Timed out"
                raise RuntimeError # go to default handling
            output = subprocess.check_output(["pifi", "status"])
            if "not activated" in output:
                time.sleep(5)
            if "acting as an Access Point" in output:
                break # dont bother with chrony in AP mode
            if "is connected to" in output:
                # we are connected to a network
                subprocess.call(["chronyc", "waitsync", "6"]) # Wait for chrony sync
    except (RuntimeError, OSError, subprocess.CalledProcessError) as e:
        print "Error calling pifi"
        if (time.time() < 1530403200): # If date before July 1, 2018
            subprocess.call(["chronyc", "waitsync", "6"]) # Wait for chrony sync

    # Ugly, but works 
    # just passing argv doesn't work with launch arguments, so we assign sys.argv
    sys.argv = ["roslaunch", "magni_bringup", "core.launch", 
                         "raspicam_mount:=%s" % conf['raspicam']['position'],
                         "sonars_installed:=%s" % conf['sonars']]

    roslaunch.main(sys.argv)
