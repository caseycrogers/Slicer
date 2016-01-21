# Slicer
This is a very early version of Slicer. Slicer is a Fusion 360 script that chops a body into layers. This makes your design look like it was 3D printed and lets you make some pretty cool looking renders.

# Attributions:
Includes helper functions written by Kris Kaplan

## NOTE:
Currently Slice only works in designs that are set to "z-up". I will add support for the default "y-up" setting in the near future, but for now you can change Fusion to "z-up" in the preferences menu (will only apply to designs made AFTER the setting was changed). I strongly encourage you to use "z-up" as that is the standard used by most 3D software (including slicers for 3D printing).

# How To Use Slicer
Download this Github Repository by clicking "Download As ZIP" or by using "git pull <insert repository address>"  in terminal. If you downloaded as a zip, extract the contents of the zip to the location of yoru chosing. \s\s
In Fusion, open the "Scripts and Add-Ins" tool. Press the green plus sign in the scripts tab and navigate to "Slicer.py". From the scripts and add-ins menu, select Slicer and click "run". The program's inputs should be self-explanatory. \s\s

# Current Features
+ Slice a body

# Planned Features
+ Support y-up orientation (but really, please go change your preferences to "z-up" right now)
+ Optional rounding applied to the layers to give a more realistic effect
+ Combine all the layers into a single body to reduce clutter

# Known Bugs (working on fixes)
