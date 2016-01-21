#Author-
#Description-Takes a body and Voxelizes it with the given parameters

import adsk.core, adsk.fusion, traceback

app = None
ui  = None
commandId = 'SliceInput'
commandName = 'Slice Input'
commandDescription = 'Input for the Slicer script.'

# Global set of event handlers to keep them referenced for the duration of the command
handlers = []

def slice(layerHeight, body):
    design = app.activeProduct
    if not design:
        ui.messageBox('No active Fusion design', 'No Design')
        return
    timeline = design.timeline
    rootComp = design.rootComponent
    sketches = rootComp.sketches
    planes = rootComp.constructionPlanes
    extrudes = rootComp.features.extrudeFeatures
    combines = rootComp.features.combineFeatures
    
    startIndex = timeline.markerPosition
    box = body.boundingBox
    startHeight = box.minPoint.z
    stopHeight = box.maxPoint.z
    currHeight = startHeight + layerHeight/2.0
    dist = adsk.core.ValueInput.createByReal(layerHeight/2.0)
    
    layerBodies = adsk.core.ObjectCollection.create()
    firstBody = None    

    numLayers = int((stopHeight-startHeight)//layerHeight)
    yn = ui.messageBox("%i layers, continue?" % (numLayers), "Slicer", 1)
    if yn != 0:
        return

    body.isVisible = False
    while currHeight < stopHeight:
        # Create a plane at the middle of the current layer height
        inputPlane = planes.createInput()
        origin = adsk.core.Point3D.create(0, 0, currHeight)
        normal = adsk.core.Vector3D.create(0, 0, 1)
        inputPlane.setByPlane(adsk.core.Plane.create(origin, normal))
        plane = planes.add(inputPlane)
    
        # Create a sketch and intersect the body with it
        sketch = sketches.add(plane)
        try:
            sketch.projectCutEdges(body)
        except:
            currHeight += layerHeight
            continue
        
        # Extrude all the profiles in the sketch to build a layer
        extProfiles = adsk.core.ObjectCollection.create()
        positiveSpaceProfiles = findPositiveProfiles(sketch.profiles)
        for profile in positiveSpaceProfiles:
            extProfiles.add(profile)
        extInput = extrudes.createInput(extProfiles, \
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput.setTwoSidesDistanceExtent(dist, dist)
        
        ext = extrudes.add(extInput)
        """for body in ext.bodies:
            if not firstBody:
                firstBody = body
            layerBodies.add(body)"""
        adsk.doEvents()
        app.activeViewport.refresh()
        currHeight += layerHeight
    """combInput = combines.createInput(firstBody, layerBodies)
    combines.add(combInput)"""
    endIndex = timeline.markerPosition
    if startIndex != endIndex:
        timeline.timelineGroups.add(startIndex, endIndex-1)


"""HELPER FUNCTIONS"""

""" Returns true if a profile created by an intersect represents positive space.
    Takes in one profile and a collection of all the profiles created by
    an intersect
    Depricated, replaced by profileSketchEntities"""
def intersects(profile, profiles):
    numInterior = 0
    for prof in profiles:
        if interior(profile.boundingBox, prof.boundingBox):
            numInterior += 1
    return (numInterior % 2) == 0

def interior(bBox1, bBox2):
    return bBox1.minPoint.x > bBox2.minPoint.x and \
    bBox1.maxPoint.x < bBox2.maxPoint.x

"""KRAZY CODE BY KRIS KAPLAN"""
def profileLoopSketchEntities(profileLoop):
    entities = []
    for profileCurve in profileLoop.profileCurves:
        if not profileCurve.sketchEntity in entities:
            entities.append(profileCurve.sketchEntity)
    return entities

def profileLoopsEqual(profileLoop1, profileLoop2):
    # simple compare of sketch entities only.  More rigorous would be comparing all curve geometry.
    entities1 = profileLoopSketchEntities(profileLoop1)
    entities2 = profileLoopSketchEntities(profileLoop2)
    for ent in entities1:
        if not ent in entities2:
            return False
    return len(entities1) == len(entities2)

def findPositiveProfiles(profiles):
    unclassifiedOuterLoops = []
    unclassifiedInnerLoops = []
    for profile in profiles:
        for loop in profile.profileLoops:
            if loop.isOuter:
                unclassifiedOuterLoops.append(loop)
            else:
                unclassifiedInnerLoops.append(loop)

    positiveSpaceProfiles = []
    positiveSpaceInnerLoops = []
    negativeSpaceInnerLoops = []
    progressMade = True
    firstPass = True
    while progressMade and unclassifiedOuterLoops:
        progressMade = False
        loopsToRemove = []
        for thisLoop in unclassifiedOuterLoops:
            isPositive = False
            isNegative = False
            if firstPass:
                # search for absolute outer profiles
                isPositive = True
                for otherLoop in unclassifiedInnerLoops:
                    if profileLoopsEqual(thisLoop, otherLoop):
                        isPositive = False
                        break
            else:                    
                for otherLoop in negativeSpaceInnerLoops:
                    if profileLoopsEqual(thisLoop, otherLoop):
                        isPositive = True
                        break
                if not isPositive:
                    for otherLoop in positiveSpaceInnerLoops:
                        if profileLoopsEqual(thisLoop, otherLoop):
                            isNegative = True
                            break
                        
            if isPositive:
                positiveSpaceProfiles.append(thisLoop.parentProfile)
                loopsToRemove.append(thisLoop)
                for loop in thisLoop.parentProfile.profileLoops:
                    if not loop.isOuter:
                        positiveSpaceInnerLoops.append(loop)
                progressMade = True
            elif isNegative:
                loopsToRemove.append(thisLoop)
                for loop in thisLoop.parentProfile.profileLoops:
                    if not loop.isOuter:
                        negativeSpaceInnerLoops.append(loop)
                progressMade = True
        firstPass = False
        for loop in loopsToRemove:
            unclassifiedOuterLoops.remove(loop)
    assert not unclassifiedOuterLoops
    return positiveSpaceProfiles


""" REALLY ANNOYING USER INTERFACE SETUP STUFF"""
class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # This will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.command
            onDestroy = MyCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # Keep the handler referenced beyond this function
            handlers.append(onDestroy)
            inputs = cmd.commandInputs
            global commandId

            # Create selection input
            selectionInput = inputs.addSelectionInput(commandId + '_selection', 'Select', 'Basic select command input')
            selectionInput.setSelectionLimits(1,1)
            selectionInput.addSelectionFilter("Bodies")
            # Create value input
            inputs.addValueInput(commandId + '_lh', 'Layer Height', \
            app.activeProduct.unitsManager.defaultLengthUnits, \
            adsk.core.ValueInput.createByReal(0.0))

            # Connect up to command related events.
            onExecute = CommandExecutedHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)        
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CommandExecutedHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = args.firingEvent.sender

            # Get the data and settings from the command inputs
            layerHeight = None
            body = None
            for input in command.commandInputs:
                if input.id == commandId + '_lh':
                    layerHeight = input.value
                elif input.id == commandId + '_selection':                                                
                    body = input.selection(0).entity
            slice(layerHeight, body)
        except:
            if ui:
                ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))

def run(context):
    ui = None
    try:
        global app
        app = adsk.core.Application.get()
        global ui
        ui = app.userInterface

        global commandId
        global commandName
        global commandDescription

        # Create command defintion
        cmdDef = ui.commandDefinitions.itemById(commandId)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(commandId, commandName, commandDescription)

        # Add command created event
        onCommandCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # Keep the handler referenced beyond this function
        handlers.append(onCommandCreated)

        # Execute command
        cmdDef.execute()

        # Prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))