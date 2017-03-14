# NOTE: This script is tested with Abaqus/CAE Release 6.13-2
#       To work properly, It is recomended to run this  script 
#       in a fresh CAE session.
#
#  This python script uses Abaqus Standard to perform a parametric
#  study on a particulate inclusion composite. The boundary conditions
#  of the problem will remain unchanged. There is a single inclusion
#  at the center of the matrix. We change the radius of the inclusion 
#  in a range (rIncRange) to find out the optimum radius at which mean 
#  temperature on the bottom edge maximizes.
#
#  Further description of the problem can be found at Section 5.1:
#  A.R. Najafi, M. Safdari, D.A. Tortorelli, P.H. Geubelle, 
#  "A gradient-based shape optimization scheme using an interface-enriched 
#  generalized FEM", Computer Methods in Applied Mechanics and Engineering, 
#  Volume 296, 1 November 2015, Pages 1-17, 
#  ISSN 0045-7825, http://dx.doi.org/10.1016/j.cma.2015.07.024.
#  (http://www.sciencedirect.com/science/article/pii/S0045782515002455)
#
#  Run sequence: 
#          1) copy script to the current work folder
#          2) start abaqus cae
#          3) choose run script (or form file -> run script)
#
#  Problem will be solved iteratively and finally the distribution of the
#  temperature w.r.t inclusion radius will be plotted.
#          
#
#  Copyright Masoud Safdari
#  University of Illinois 2015
#

## Initial imports
from abaqus import *
from abaqusConstants import *
from numpy import *

########          Problem definition       ########################################
# Use consistent units (Currently SI)
# Dimensions 
LMat = 0.1                               # square domain side length
rIncRange = arange(0.01, 0.045, 0.005)   # inclusion radii range (initial, final, step)
# Material properties
KMat = 17                                # Thermal conductivity for matirx
KInc = 100                               # Thermal conductivity for inclusion
# BCs                 
QGenInc = 50000                          # volumetirc heat generation in inclusion
QGenMat = 10                             # volumetric heat generation in matirx
TTop = 20                                # top edge temperature
qBot = 1000                              # heat flux at the bottom edge
###################################################################################

## Importing tools from Abaqus library
session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=320.0, 
    height=180.0)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].maximize()
from caeModules import *
from abaqus import backwardCompatibility
backwardCompatibility.setValues(reportDeprecated=False)
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
    referenceRepresentation=ON)
Mdb()
## Optimmization problem setting
meanBotNT = []
## Running iterations
for rInc in rIncRange:
        ## Creating the part (p)
	## Creating square domain
	session.viewports['Viewport: 1'].setValues(displayedObject=None)
	s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=5.0)
	g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
	s.setPrimaryObject(option=STANDALONE)
	s.rectangle(point1=(0.0, 0.0), point2=(LMat, LMat))
	p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=TWO_D_PLANAR, 
	    type=DEFORMABLE_BODY)
	p = mdb.models['Model-1'].parts['Part-1']
	p.BaseShell(sketch=s)
	s.unsetPrimaryObject()
	p = mdb.models['Model-1'].parts['Part-1']
	session.viewports['Viewport: 1'].setValues(displayedObject=p)
	del mdb.models['Model-1'].sketches['__profile__']
	## Adding circular partition
	f, e, d1 = p.faces, p.edges, p.datums
	t = p.MakeSketchTransform(sketchPlane=f[0], sketchPlaneSide=SIDE1, origin=(LMat/2.0, 
	    LMat/2.0, 0.0))
	s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
	    sheetSize=2.26, gridSpacing=0.05, transform=t)
	g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
	s1.setPrimaryObject(option=SUPERIMPOSE)
	p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)
	s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(rInc, 0.0))
	f = p.faces
	pickedFaces = f.getSequenceFromMask(mask=('[#1 ]', ), )
	e1, d2 = p.edges, p.datums
	p.PartitionFaceBySketch(faces=pickedFaces, sketch=s1)
	s1.unsetPrimaryObject()
	del mdb.models['Model-1'].sketches['__profile__']
	## Defining matrix material
	session.viewports['Viewport: 1'].partDisplay.setValues(sectionAssignments=ON, 
	    engineeringFeatures=ON)
	session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(
	    referenceRepresentation=OFF)
	mdb.models['Model-1'].Material(name='Material-1')
	mdb.models['Model-1'].materials['Material-1'].Conductivity(table=((KMat, ), ))
	mdb.models['Model-1'].materials['Material-1'].SpecificHeat(table=((1.0, ), ))
	mdb.models['Model-1'].materials['Material-1'].Density(table=((1.0, ), ))
	## Defining inclusion material
	mdb.models['Model-1'].Material(name='Material-2')
	mdb.models['Model-1'].materials['Material-2'].Conductivity(table=((KInc, ), ))
	mdb.models['Model-1'].materials['Material-2'].SpecificHeat(table=((1.0, ), ))
	mdb.models['Model-1'].materials['Material-2'].Density(table=((1.0, ), ))
	## Section assignement
	mdb.models['Model-1'].HomogeneousSolidSection(name='matrix', 
	    material='Material-1', thickness=None)
	mdb.models['Model-1'].HomogeneousSolidSection(name='inclusion', 
	    material='Material-2', thickness=None)
	f = p.faces
	faces = f.getSequenceFromMask(mask=('[#1 ]', ), )
	region = p.Set(faces=faces, name='matrix')
	p.SectionAssignment(region=region, sectionName='matrix', offset=0.0, 
	    offsetType=MIDDLE_SURFACE, offsetField='', 
	    thicknessAssignment=FROM_SECTION)
	f = p.faces
	faces = f.getSequenceFromMask(mask=('[#2 ]', ), )
	region = p.Set(faces=faces, name='inclusion')
	p.SectionAssignment(region=region, sectionName='inclusion', offset=0.0, 
	    offsetType=MIDDLE_SURFACE, offsetField='', 
	    thicknessAssignment=FROM_SECTION)
	## Creating the Assembly (a)
	a = mdb.models['Model-1'].rootAssembly
	session.viewports['Viewport: 1'].setValues(displayedObject=a)
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(
	    optimizationTasks=OFF, geometricRestrictions=OFF, stopConditions=OFF)
	a.DatumCsysByDefault(CARTESIAN)
	a.Instance(name='Part-1-1', part=p, dependent=ON)
	a.makeIndependent(instances=(a.instances['Part-1-1'], ))
	## Step
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(
	    adaptiveMeshConstraints=ON)
	mdb.models['Model-1'].HeatTransferStep(name='heat', previous='Initial', 
	    deltmx=100.0)
	## BCs
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(step='heat')
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(loads=ON, bcs=ON, 
	    predefinedFields=ON, connectors=ON, adaptiveMeshConstraints=OFF)
	region = a.instances['Part-1-1'].sets['inclusion']
	mdb.models['Model-1'].BodyHeatFlux(name='Load-1', createStepName='heat', 
	    region=region, magnitude=QGenInc)
	region = a.instances['Part-1-1'].sets['matrix']
	mdb.models['Model-1'].BodyHeatFlux(name='Load-2', createStepName='heat', 
	    region=region, magnitude=QGenMat)
	e1 = a.instances['Part-1-1'].edges
	edges1 = e1.getSequenceFromMask(mask=('[#4 ]', ), )
	region = a.Set(edges=edges1, name='top')
	mdb.models['Model-1'].TemperatureBC(name='top', createStepName='heat', 
	    region=region, fixed=OFF, distributionType=UNIFORM, fieldName='', 
	    magnitude=TTop, amplitude=UNSET)
	s1 = a.instances['Part-1-1'].edges
	side1Edges1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
	region = a.Surface(side1Edges=side1Edges1, name='bot')
	mdb.models['Model-1'].SurfaceHeatFlux(name='qBot', createStepName='heat', 
	    region=region, magnitude=qBot)
	## Mesh generation
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON, loads=OFF, 
	    bcs=OFF, predefinedFields=OFF, connectors=OFF)
	session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(
	    meshTechnique=ON)
	partInstances =(a.instances['Part-1-1'], )
	a.seedPartInstance(regions=partInstances, size=LMat/30, deviationFactor=0.1, 
	    minSizeFactor=0.1)
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON)
	session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(
	    meshTechnique=ON)
	elemType1 = mesh.ElemType(elemCode=DC2D4, elemLibrary=STANDARD)
	elemType2 = mesh.ElemType(elemCode=DC2D3, elemLibrary=STANDARD)
	f1 = a.instances['Part-1-1'].faces
	faces1 = f1.getSequenceFromMask(mask=('[#3 ]', ), )
	pickedRegions =(faces1, )
	a.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2))
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=OFF)
	session.viewports['Viewport: 1'].assemblyDisplay.meshOptions.setValues(
	    meshTechnique=OFF)
	partInstances =(a.instances['Part-1-1'], )
	a.generateMesh(regions=partInstances)
	## Bottom nodes set
	session.viewports['Viewport: 1'].assemblyDisplay.setValues(mesh=ON)
	n1 = a.instances['Part-1-1'].nodes
	nodes1 = n1.getSequenceFromMask(mask=('[#ffffffe3 #3 ]', ), )
	a.Set(nodes=nodes1, name='bot')
	regionDef=mdb.models['Model-1'].rootAssembly.sets['bot']
	## Job
	mdb.Job(name='heatOpt', model='Model-1', description='', type=ANALYSIS, 
	    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
	    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
	    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, 
	    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
	    scratch='', multiprocessingMode=DEFAULT, numCpus=1, numGPUs=0)
	## Saving the work
	mdb.saveAs(pathName='heatOpt.cae')
	## Submitting the job and waiting for completion
	mdb.jobs['heatOpt'].submit(consistencyChecking=OFF)
	mdb.jobs['heatOpt'].waitForCompletion()
	## Reading ODB (o)
	o = session.openOdb(name='heatOpt.odb')
	session.viewports['Viewport: 1'].setValues(displayedObject=o)
	session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(
	    CONTOURS_ON_DEF, ))
	session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(
	    variableLabel='NT11', outputPosition=NODAL, )
	## Reading Temperatures of the bottom edges
	botNTData= o.steps['heat'].frames[1].fieldOutputs['NT11'].getSubset(region = o.rootAssembly.nodeSets['BOT']);
	botNT = [];
	for val in botNTData.values:
		botNT.append(val.data)
	meanBotNT.append(mean(botNT))
	## Closing the odb
	session.odbs['heatOpt.odb'].close()
## Creating XY plot
xyPair = []
for dataIdx in range(len(meanBotNT)):
	xyPair.append([rIncRange[dataIdx], meanBotNT[dataIdx]])
xyd = xyPlot.XYData(data = xyPair, name = 'TvsR')
xyp = session.XYPlot(name='TvsR')
xyp.xyPlotOptions.setValues(yAxisMinAutoCompute=OFF,yAxisMinValue=20,yAxisMaxAutoCompute=OFF,yAxisMaxValue=28)
xyc = xyp.Curve('TvsR', xyd)
xyp.charts['Chart-1'].setValues(curvesToPlot=xyc)
## Showing the plot
vp = session.viewports[session.currentViewportName]
vp.setValues(displayedObject=xyp)
