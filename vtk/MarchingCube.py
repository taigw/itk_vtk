import vtk
 
fileName='../data/Labels/labels.mhd'
 
# Prepare to read the file
 
readerVolume = vtk.vtkMetaImageReader()
readerVolume.SetFileName(fileName)
readerVolume.Update()
 
 
# Extract the region of interest
voi = vtk.vtkExtractVOI()
if vtk.VTK_MAJOR_VERSION <= 5:
    voi.SetInput(readerVolume.GetOutput())
else:
    voi.SetInputConnection(readerVolume.GetOutputPort())
 
voi.SetVOI(0,517, 0,228, 0,392)
voi.SetSampleRate(1,1,1)
#voi.SetSampleRate(3,3,3)
voi.Update()#necessary for GetScalarRange()
srange= voi.GetOutput().GetScalarRange()#needs Update() before!
print "Range", srange
 
 
##Prepare surface generation
#contour = vtk.vtkContourFilter()
#contour = vtk.vtkMarchingCubes()
marchingCube = vtk.vtkDiscreteMarchingCubes() #for label images
if vtk.VTK_MAJOR_VERSION <= 5:
    marchingCube.SetInput( voi.GetOutput() )
else:
    marchingCube.SetInputConnection( voi.GetOutputPort() )
marchingCube.ComputeNormalsOn()


index = 293
print "Doing label", index

marchingCube.SetValue(0, index)
marchingCube.Update() #needed for GetNumberOfPolys() !!!


smoother= vtk.vtkWindowedSincPolyDataFilter()
if vtk.VTK_MAJOR_VERSION <= 5:
    smoother.SetInput(marchingCube.GetOutput());
else:
    smoother.SetInputConnection(marchingCube.GetOutputPort());
smoother.SetNumberOfIterations(10);
#smoother.BoundarySmoothingOff();
#smoother.FeatureEdgeSmoothingOff();
#smoother.SetFeatureAngle(120.0);
#smoother.SetPassBand(.001);
smoother.NonManifoldSmoothingOn();
smoother.NormalizeCoordinatesOn();
smoother.Update();

segMeshData = smoother.GetOutput()
cellN = segMeshData.GetNumberOfCells()
colors = vtk.vtkUnsignedCharArray()
colors.SetNumberOfComponents(3)
for i in range(cellN):
    colors.InsertNextTupleValue((255,0,0))
segMeshData.GetCellData().SetScalars(colors)

segMeshMapper = vtk.vtkPolyDataMapper()
segMeshMapper.SetInputData(segMeshData)

segMeshActor = vtk.vtkActor()
segMeshActor.SetMapper(segMeshMapper)

aRenderer = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(aRenderer)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

aRenderer.AddActor(segMeshActor)
renWin.SetSize(640, 480)

# Interact with the data.
iren.Initialize()
renWin.Render()
iren.Start()