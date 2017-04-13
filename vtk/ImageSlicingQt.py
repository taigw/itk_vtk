#!/usr/bin/env python
 
import sys
import vtk
from PyQt4 import QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

def load_vtk_data(imgName):
    if(imgName.endswith('nii')):
        reader=vtk.vtkNIFTIImageReader()
    elif(imgName.endswith('mha')):
        reader = vtk.vtkMetaImageReader()
    else:
        raise ValueError('could not open file {0:}'.format(imgName))
    reader.SetFileName(imgName)
    reader.Update()
    img=reader.GetOutput()
    return img    

class SliceWidget(QVTKRenderWindowInteractor):
    # planeDirection: 'axial', 'sagittal', 'coronal'
    def __init__(self, parent = None, planeDirection='axial'):
        QVTKRenderWindowInteractor.__init__(self, parent)
        self.planeDirection = planeDirection
        self.reslice =  vtk.vtkImageReslice()
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetInterpolationModeToNearestNeighbor()
        self.mapToColor = vtk.vtkImageMapToColors()
                
        self.actor = vtk.vtkImageActor()
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(self.actor)
        self.GetRenderWindow().AddRenderer(self.ren)    
        self.interactorStyle = vtk.vtkInteractorStyleImage()
        self.SetInteractorStyle(self.interactorStyle)

    def SetColorTable(self, table):
        self.table = table
        self.mapToColor.SetLookupTable(self.table)
        
    def SetImage(self, img3d):
        self.img = img3d
    
    # the intersection point of three planes: [idx_x, idx_y, idx_z] 
    def SetIntersectionPoint(self, point):
        extent = self.img.GetExtent()
        spacing = self.img.GetSpacing()
        origin = self.img.GetOrigin()
        center = [origin[0] + spacing[0] * (extent[0] + point[0]),
                  origin[1] + spacing[1] * (extent[2] + point[1]),
                  origin[2] + spacing[2] * (extent[4] + point[2])]
        resliceMatrix = vtk.vtkMatrix4x4()
        if(self.planeDirection == 'axial'):
            resliceMatrix.DeepCopy((1, 0, 0, center[0],
                                    0, 1, 0, center[1],
                                    0, 0, 1, center[2],
                                    0, 0, 0, 1))
        elif(self.planeDirection == 'sagittal'):
            resliceMatrix.DeepCopy((1, 0, 0, center[0],
                                    0, 0, 1, center[1],
                                    0,-1, 0, center[2],
                                    0, 0, 0, 1))
        else:
            resliceMatrix.DeepCopy((0, 0,-1, center[0],
                                    1, 0, 0, center[1],
                                    0,-1, 0, center[2],
                                    0, 0, 0, 1))
        self.reslice.SetInputData(self.img)
        self.reslice.SetResliceAxes(resliceMatrix)   
        self.reslice.Update() 
        self.mapToColor.SetInputData(self.reslice.GetOutput())
        self.mapToColor.Update()
        self.actor.GetMapper().SetInputData(self.mapToColor.GetOutput())
        self.Start()

class SliceFrame(QtGui.QWidget):
    # planeDirection: 'axial', 'sagittal', 'coronal'
    def __init__(self, parent = None, planeDirection='axial'):
        QtGui.QWidget.__init__(self, parent)    
        self.sliceWidget = SliceWidget(self, planeDirection)
        
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.sliceWidget)
        self.setLayout(layout)
        
class VolumeViewWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        
        self.table = vtk.vtkLookupTable()
        self.table.SetRange(0,2000)
        self.table.SetValueRange(0.0, 1.0) # from black to white
        self.table.SetSaturationRange(0.0, 0.0) # no color saturation
        self.table.SetRampToLinear()
        self.table.Build()
        
        self.axialSliceFrame = SliceFrame(self,'axial')
        self.sagittalSliceFrame = SliceFrame(self,'sagittal')
        self.coronalSliceFrame = SliceFrame(self,'coronal')
        
        self.axialSliceFrame.sliceWidget.SetColorTable(self.table)
        self.sagittalSliceFrame.sliceWidget.SetColorTable(self.table)
        self.coronalSliceFrame.sliceWidget.SetColorTable(self.table)
        
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.axialSliceFrame, 0, 0)
        self.layout.addWidget(self.sagittalSliceFrame, 0, 1)
        self.layout.addWidget(self.coronalSliceFrame, 1, 0)
        self.setLayout(self.layout)
        
    def SetVolumeImage(self, vtkImg):
        self.img = vtkImg
        extent = self.img.GetExtent()
        point = [extent[1]/2, extent[3]/2, extent[5]/2]
        self.axialSliceFrame.sliceWidget.SetImage(self.img)
        self.sagittalSliceFrame.sliceWidget.SetImage(self.img)
        self.coronalSliceFrame.sliceWidget.SetImage(self.img)
        self.axialSliceFrame.sliceWidget.SetIntersectionPoint(point)
        self.sagittalSliceFrame.sliceWidget.SetIntersectionPoint(point)
        self.coronalSliceFrame.sliceWidget.SetIntersectionPoint(point)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):        
        QtGui.QMainWindow.__init__(self, parent)
        self.viewwidget = VolumeViewWidget()
        self.frame = QtGui.QFrame()
        self.vl = QtGui.QVBoxLayout()
        self.vl.addWidget(self.viewwidget)
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
 
        bar = self.menuBar()
        file = bar.addMenu("File")
        open = QAction("Open", self)
        open.setShortcut("Ctrl+O")
        file.addAction(open)
         
        save = QAction("Save",self)
        save.setShortcut("Ctrl+S")
        file.addAction(save)
                  
        quit = QAction("Quit",self) 
        file.addAction(quit)
        file.triggered[QAction].connect(self.processtrigger)
        self.setWindowTitle("slicing demo")
         
    def processtrigger(self,q):
        print q.text()+" is triggered"
      
    def LoadData(self):
        reader = vtk.vtkImageReader2()
        reader.SetFilePrefix("../data/headsq/quarter")
        reader.SetDataExtent(0, 63, 0, 63, 1, 93)
        reader.SetDataSpacing(3.2, 3.2, 1.5)
        reader.SetDataOrigin(0.0, 0.0, 0.0)
        reader.SetDataScalarTypeToUnsignedShort()
        reader.UpdateWholeExtent()
        
        data = reader.GetOutput()
        self.viewwidget.SetVolumeImage(data)
 
if __name__ == "__main__": 
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.LoadData()
    window.move(0,0)
    sys.exit(app.exec_())