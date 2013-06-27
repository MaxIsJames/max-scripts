import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import os
import inspect

def load_ui():

    current_script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    if (cmds.window('softcluster', exists=True)):
        cmds.deleteUI('softcluster')
    window = cmds.loadUI(uiFile=os.path.join(current_script_path, 'softcluster.ui'))
    cmds.showWindow(window)

def toggle_spline(bool):
    cmds.checkBox('UI_Translate_CheckBox', e=True, v=bool)
    cmds.checkBox('UI_Rotate_CheckBox', e=True, v=bool)

def toggle_translate(bool):
    cmds.checkBox('UI_Spline_CheckBox', e=True, v=bool)

def paint_tool():
    if cmds.artAttrCtx('artAttrCtx1', q=True, ex=True) is not True:
        cmds.artAttrCtx('artAttrCtx1')
    cmds.setToolTo('artAttrCtx1')

 
def softSelection():
#Grab the soft selection
    selection = OpenMaya.MSelectionList()
    softSelection = OpenMaya.MRichSelection()
    OpenMaya.MGlobal.getRichSelection(softSelection)
    softSelection.getSelection(selection)
    
    dagPath = OpenMaya.MDagPath()
    component = OpenMaya.MObject()
    

    iter = OpenMaya.MItSelectionList( selection,OpenMaya.MFn.kMeshVertComponent )
    elements, weights = [], []
    while not iter.isDone(): 
        iter.getDagPath( dagPath, component )
        dagPath.pop()
        node = dagPath.fullPathName()
        fnComp = OpenMaya.MFnSingleIndexedComponent(component)   
        getWeight = lambda i: fnComp.weight(i).influence() if fnComp.hasWeights() else 1.0
        
        for i in range(fnComp.elementCount()):
            elements.append('%s.vtx[%i]' % (node, fnComp.element(i)))
            weights.append(getWeight(i)) 
        iter.next()
        
    return elements, weights

def create_guide():
    if cmds.objExists('loc_guide_deformer'):
        cmds.delete('loc_guide_deformer')
    bound_centre = [0,0,0]
    if len(cmds.ls(sl=True)) is not 0:
        bound = cmds.exactWorldBoundingBox(cmds.ls (sl = True))
        bound_centre = [(bound[0] + bound[3])/2, (bound[1] + bound[4])/2, (bound[2] + bound[5])/2]
    cmds.spaceLocator (n="loc_guide_deformer", a = True, p = (bound_centre[0], bound_centre[1], bound_centre[2]))
    cmds.CenterPivot()

def create_cluster():
    cluster_name = cmds.textField('UI_cluster_clusterPrefix', q=True, tx=True) + cmds.textField('UI_cluster_clusterName', q=True, tx=True)
    cluster_name = cluster_name.replace (" ", "_")
    
# cluster soft selections
    # Use Weight Set Override
    if cmds.checkBox('UI_useWeights_CheckBox', q=True, value=True) is True:
        elements, weights = use_weight_set()
    else:
        elements, weights = softSelection()
        cmds.softSelect( sse=0)
        mel.eval("polyConvertToShell;")
    vertex_count = cmds.ls(sl=True, fl=True)


    if cmds.objExists("loc_guide_deformer") is True:
        parent_cluster(cluster_name)
    else:
        cmds.cluster (name = cluster_name, bs = True)
    for vertex in vertex_count:
        cmds.percent (cluster_name, vertex, value = 0)
    for x in range(len(elements)):
        cmds.percent (cluster_name, elements[x], value = weights[x])

def parent_cluster(cluster_name):
    cluster_parent = cmds.textField('UI_cluster_clusterName', q=True, tx=True)
    cluster_parent = cluster_parent.replace (" ", "_")
    cluster_parent = cmds.createNode( 'transform', n= 'trn_' + cluster_parent, ss=True)
    centre = cmds.objectCenter("loc_guide_deformer", gl=True)
    cmds.move(centre[0], centre[1], centre[2], cluster_parent)
    cmds.cluster (name = cluster_name, bs = True, wn = (cluster_parent, cluster_parent))
    cmds.delete("loc_guide_deformer")


def use_weight_set():
    cmds.select(cmds.cluster(cmds.textScrollList('UI_cluster_list', q=True, si=True)[0], q=True, g=True)[0])
    mel.eval("ConvertSelectionToVertices;")
    weights = cmds.percent (cmds.textScrollList('UI_cluster_list', q=True, si=True)[0], q=True, v=True)
    cmds.filterExpand( ex=True, sm=31 )
    elements = cmds.ls(sl=True, fl=True)
    return elements, weights
    

def list_clusters():
    cmds.textScrollList('UI_cluster_list', e=True, ra=True)
    nodelist = cmds.listHistory( cmds.ls (sl =True ), pdo = True, il = 1)
    for item in nodelist:
        splititem = item.split('_')
        if splititem[0] == 'def':
            cmds.textScrollList('UI_cluster_list', e=True, append=item)

def select_cluster():
     cmds.select (cmds.textScrollList('UI_cluster_list', q=True, si=True)[0])