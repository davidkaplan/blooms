import math
import pymel.core as pm


def run():
    # Clear scene
    pm.select(allDagObjects=True)
    if pm.selected():
        pm.delete()

    # Make settings
    r = 20
    settings = pm.group(empty=True, name='settings', )
    pm.addAttr(settings, longName='delta_height', defaultValue=0.25, minValue=0.05, maxValue=1)
    pm.addAttr(settings, longName='delta_theta', defaultValue=137.5, minValue=0, maxValue=360)
    pm.addAttr(settings, longName='numPoints', defaultValue=250, minValue=100, maxValue=500, attributeType='byte')
    pm.addAttr(settings, longName='start_angle', defaultValue=0, minValue=-85, maxValue=85, attributeType='double')
    pm.addAttr(settings, longName='start_height', defaultValue=0, attributeType='double')
    pm.expression(settings, s='%s = %d * tan(%s * 3.1459/180)' % (settings.start_height, 1, settings.start_angle))

    # Seed object
    seed = pm.polyPyramid(name='seedObj')

    # Group locators
    loc_group = pm.group(empty=True, name='group_locators')

    #turn off history
    pm.undoInfo(state=False)

    # Do loop
    #pm.progressWindow(title='Creating Bloom Locators', progress=0, isInteruptable=True)
    amount = 0
    pm.progressWindow(title='Creating Bloom', progress=0, status='calculating...', isInterruptable=True )
    try:
        n = settings.numPoints.get()
        for i in range(n):
            if pm.progressWindow( query=True, isCancelled=True ) :
                break

            # Inner locator
            loc = pm.spaceLocator(position=[0,0,0], name='loc_%i_inner' % i)
            loc.translateX.set(r)
            pm.addAttr(longName='index', defaultValue=i)
            loc.setAttr('index', lock=True)
            loc.setRotationOrder('XZY', True)
            loc.rotateX.lock()
            loc.translate.lock()
            pm.expression(loc, s='%s.rotateZ = 180*atan(%s + %i*%s/%i)/3.1459' % (loc.nodeName(), settings.start_height, i, settings.delta_height, r))
            pm.expression(loc, s='%s.rotateY = %i*%s' % (loc.nodeName(), i, settings.delta_theta))
            #pm.parent(loc, loc_group, absolute=True)

            # Outer locator
            #loc_outer = pm.spaceLocator( name='loc_%i_outer' % i)
            #loc_outer.translateX.set(5)
            #pm.parent(loc_outer, loc, relative=True)

            #pm.expression(s='%s = %s + %s/90 * %s' * (loc_outer.localPositionX, loc.localPositionX, loc.rotateZ, 10))
            #loc_outer.translateY.lock()
            #loc_outer.translateZ.lock()
            #loc_outer.rotate.lock()

            # Update progress
            pm.progressWindow( edit=True, progress=100*i/n)

    except Exception, e:
        print 'Error', e

    pm.progressWindow(endProgress=1)
    pm.undoInfo(state=True)
    pm.select(settings)


# sel_list = pm.selected()
# sel_xform = sel_list[0]
# sel_shapes = sel_xform.listRelatives(shapes=True)
# sel_shape = sel_shapes[0]
# lat, latxform, latbasexform = pm.lattice(sel_shape, dv=(2,2,2), objectCentered=True, outsideLattice=1)
# latxform.scale.set([1,1,1])
# latbasexform.scale.set([1,1,1])
# point1 = latxform.pt[0][0][0]
# pm.listAttr(point1)
# cluster1 = pm.cluster(point1)

# locator1 = pm.spaceLocator(name='loc1', position=[5,0,0])
# locator1.setRotatePivot([0,0,0])
# locator1.setRotationOrder('XZY', True)
# locator1.rotateOrder.set(1)
# locator1.rotate.set([0, 40, 20])