import math
import pymel.core as pm


def run():
    # Get Selected Objects
    if not pm.ls(selection=True):
        pm.error("No Object selected in the scene. Please select an object and try again.")
    objs = pm.ls(selection=True, type='mesh', dag=True, allPaths=True, noIntermediate=True)
    if not objs:
        pm.error("No geometry object to operate on. Please select and try again.")
    if len(objs) > 1:
        pm.error("Please select only 1 object.")
    seed = objs[0]
    
    # Get rid of display layers
    [pm.delete(l) for l in pm.ls(type='displayLayer')[:-1]]

    # Hardcoded Values
    nodes = [8, 13]
    r = 20
    n = 200
    
    # Make Settings
    settings = pm.group(empty=True, name='settings', )
    pm.addAttr(settings, longName='delta_height', defaultValue=0.25, minValue=0.05, maxValue=1)
    pm.addAttr(settings, longName='delta_theta', defaultValue=137.5, minValue=0, maxValue=360)
    pm.addAttr(settings, longName='start_angle', defaultValue=0, minValue=-85, maxValue=85, attributeType='double')
    pm.addAttr(settings, longName='start_height', defaultValue=0, attributeType='double')
    pm.expression(settings, s='%s = %d * tan(%s * %d/180)' % (settings.start_height, 1, settings.start_angle, math.pi))

    # Make the snapshots
    group_snap = pm.group(empty=True, name='group_snapshots')
    snapshots = []
    for i in range(1, n+1):
        geomVarGroup, motionTrail = pm.snapshot(seed, constructionHistory=True, startTime=i, endTime=i)
        snapshots.append(geomVarGroup)
        pm.parent(geomVarGroup, group_snap)
        
    #pm.error()
        

    # Group locators
    loc_group = pm.group(empty=True, name='group_locators')

    # Python objects
    points = []

    #turn off history
    pm.undoInfo(state=False)

    # Do loop
    progress = 0
    pm.progressWindow(title='Creating Bloom', progress=progress, status='Creating Locators...', isInterruptable=True )
    progressTotal = 2*n + 2*(n - sum(nodes))
    try:
        for i in range(n):
            if pm.progressWindow( query=True, isCancelled=True ) :
                break

            # Set up rotation equations
            grp = pm.group(empty=True, name='group_%i' % i)
            pm.addAttr(longName='index', attributeType='long', defaultValue=i)
            grp.setAttr('index', lock=True)
            grp.setRotationOrder('XZY', True)
            grp.rotateX.lock()
            grp.translate.lock()
            pm.expression(grp, s='%s.rotateY = %i*%s' % (grp.nodeName(), i, settings.delta_theta))
            pm.parent(grp, loc_group)

            # Inner locator
            loc_inner = pm.spaceLocator(name='loc_%i_inner' % i)
            loc_inner.translateX.set(r)
            pm.parent(loc_inner, grp, relative=True)

            # Outer locator
            loc_outer = pm.spaceLocator(name='loc_%i_outer' % i)
            pm.parent(loc_outer, loc_inner, relative=True)
            r2 = 5
            pm.expression(loc_outer, s='%s.translateX = %d * (1 - %s / 90)' % (loc_outer.nodeName(), r2, grp.rotateZ))

            # Keep track of objects
            points.append([grp, loc_inner, loc_outer])

            # Update progress
            progress += 1
            pm.progressWindow( edit=True, progress=100*progress/progressTotal)

    except Exception, e:
        print 'Error', e

    def setPhiLocators():
        theta = settings.start_angle.get()
        for grp, loc_inner, loc_outer in points:
            # This Point
            grp.rotateZ.set(theta)
            x, y, z = pm.xform(loc_inner, query=True, worldSpace=True, translation=True)
            # Next Point
            h_prime = y + settings.delta_height.get()
            r_prime = math.sqrt(x**2 + z**2)
            theta = math.degrees(math.atan(h_prime/r_prime))

    setPhiLocators()
    pm.scriptJob(attributeChange=['settings.delta_height', setPhiLocators])
    pm.scriptJob(attributeChange=['settings.start_angle', setPhiLocators])

    # Construct clusters
    clusters = []
    #group_clusters = pm.group(empty=True, name='group_clusters')

    for locator_group in loc_group.listRelatives(children=True, type='transform'):
        if pm.progressWindow( query=True, isCancelled=True ) :
            break
        index = locator_group.getAttr('index')
        inner = locator_group.listRelatives(children=True, type='transform')[0]
        outer = inner.listRelatives(children=True, type='transform')[0]

        pm.select(clear=True)
        cluster_inner_transform, cluster_inner_handle = pm.cluster(name='cluster_%i_inner' % index)
        pm.parent(cluster_inner_handle, inner, relative=True)

        pm.select(clear=True)
        cluster_outer_transform, cluster_outer_handle  = pm.cluster(name='cluster_%i_outer' % index)
        pm.parent(cluster_outer_handle, outer, relative=True)

        clusters.append({'inner':{'xform': cluster_inner_transform, 'handle': cluster_inner_handle}, 'outer':{'xform': cluster_outer_transform, 'handle':cluster_outer_handle}})

        progress += 1
        pm.progressWindow( edit=True, progress=100*progress/progressTotal, status='Creating Clusters...')

    # Lattices
    total = n - (nodes[0] + nodes[1])

    lattices = []
    group_lattices = pm.group(empty=True, name='group_lattices')

    for group, loc_inner, loc_outer in points[:-sum(nodes)]:
        if pm.progressWindow( query=True, isCancelled=True ) :
            break

        index = group.getAttr('index')

        # Lattice
        pm.select(clear=True)
        lat, latxform, latbasexform = pm.lattice(dv=(2,2,2), objectCentered=True, outsideLattice=1)
        pm.parent([latxform, latbasexform], group_lattices)
        lattices.append({'ffd': lat, 'xform': latxform, 'base':latbasexform})
        latxform.scale.set([1,1,1])
        latbasexform.scale.set([1,1,1])

        # Clusters
        #
        # BL = 0
        # BR = 8
        # TL = 13
        # TR = 21
        #
        bot_left_inner = latxform.pt[1][0][1]
        bot_right_inner = latxform.pt[1][0][0]
        top_left_inner = latxform.pt[0][0][1]
        top_right_inner = latxform.pt[0][0][0]
        bot_left_outer = latxform.pt[1][1][1]
        bot_right_outer = latxform.pt[1][1][0]
        top_left_outer = latxform.pt[0][1][1]
        top_right_outer = latxform.pt[0][1][0]

        lattice_pts = [bot_left_inner, bot_right_inner, top_left_inner, top_right_inner,
                        bot_left_outer, bot_right_outer, top_left_outer, top_right_outer]

        map(lambda x: pm.move(x, [0,0,0]), lattice_pts)

        pm.cluster(clusters[index]['inner']['handle'], edit=True, g=bot_left_inner)
        pm.cluster(clusters[index+nodes[0]]['inner']['handle'], edit=True, g=bot_right_inner)
        pm.cluster(clusters[index+nodes[1]]['inner']['handle'], edit=True, g=top_left_inner)
        pm.cluster(clusters[index+sum(nodes)]['inner']['handle'], edit=True, g=top_right_inner)

        pm.cluster(clusters[index]['outer']['handle'], edit=True, g=bot_left_outer)
        pm.cluster(clusters[index+nodes[0]]['outer']['handle'], edit=True, g=bot_right_outer)
        pm.cluster(clusters[index+nodes[1]]['outer']['handle'], edit=True, g=top_left_outer)
        pm.cluster(clusters[index+sum(nodes)]['outer']['handle'], edit=True, g=top_right_outer)

        progress += 1
        pm.progressWindow( edit=True, progress=100*progress/progressTotal, status='Creating Lattices...')

    group_geom = pm.group(empty=True, name='group_geom')
 
    for i, lattice in enumerate(lattices):
        if pm.progressWindow( query=True, isCancelled=True ) :
            break
        #newseed = pm.instance(seed)[0]
        newseed = snapshots[i]
        pm.lattice(lattice['ffd'], e=True, g=newseed, split=True)
        pm.parent(newseed, group_geom)

        progress += 1
        pm.progressWindow( edit=True, progress=100*progress/progressTotal, status='Instancing Geometry...')

    pm.progressWindow( edit=True, progress=99, status='Finishing Up...', )

    # Display layers
    layerGeom = pm.createDisplayLayer(empty=True, name='Geometry').addMembers(group_geom)
    layerLattices = pm.createDisplayLayer(empty=True, name='Lattices').addMembers(group_lattices)
    layerLocators = pm.createDisplayLayer(empty=True, name='Locators').addMembers(loc_group)

    # Animate it
    pm.setKeyframe(loc_group, attribute='rotateY', time=0, value=0, inTangentType='linear', outTangentType='linear')
    pm.setKeyframe(loc_group, attribute='rotateY', time=1, value=137.647, inTangentType='linear', outTangentType='linear')
    pm.setInfinity(loc_group, attribute='rotateY', preInfinite='cycleRelative', postInfinite='cycleRelative')
    pm.playbackOptions(edit=True, animationEndTime='34')

    pm.undoInfo(state=True)
    pm.select(settings)

    pm.progressWindow(endProgress=True)

    print "Finished."

