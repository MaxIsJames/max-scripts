import maya.cmds as cmds
import maya.mel as mel
import os
import inspect

def load_ui():

    current_script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    if (cmds.window('SingleAxisCorrect', exists=True)):
        cmds.deleteUI('SingleAxisCorrect')
    window = cmds.loadUI(uiFile=os.path.join(current_script_path, 'corrective_blend.ui'))
    cmds.showWindow(window)
    
def errorcode(err):
		errorlist = ['no selection', 'bad selection', 'skin node not found', 'polyCount is different', 'Nothing to move', 'Joint Required']
		cmds.error( errorlist[err] )

def select_basemesh():
#takes transform and stores mesh
	if len(cmds.ls(sl=True)) is not 1:
		errorcode(0)
	else:
		filter_mesh = cmds.listRelatives(cmds.ls(sl=True), typ='mesh')
		if (type(filter_mesh) == list) is not True:
			errorcode(1)
		else:
			#cmds.textField('mesh_store', e=True, tx= filter_mesh[0])
			selection = cmds.ls(sl=True)
			cmds.textField('mesh_store', e=True, tx= selection[0])

def select_joint():
	selected_joints = cmds.ls(sl=True, typ='joint')
	if len(selected_joints) is 1:
		cmds.textField('joint_store', e=True, tx=selected_joints[0])
	else:
		errorcode(1)
		
def refreshblendnode():
	cmds.textScrollList('blendnode_list', e=True, ra=True)
	mesh_history = cmds.listHistory((cmds.textField('mesh_store', q=True, tx=True)), ac = True)
	cmds.select(mesh_history)
	cmds.textScrollList('blendnode_list', e=True, append=cmds.ls(sl=True, typ='blendShape'))
	cmds.select(d=True)


def create_sculpt():
	if len(cmds.textField('joint_store', q=True, tx=True)) is 0:
		errorcode(5)
	locked_attrs =['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
	dupe_name = cmds.textField('mesh_store', q=True, tx=True) + '_' + cmds.textField('blendname_input', q=True, tx=True) + '_sculpt_dupe'
	dupe_name = dupe_name.replace (" ", "_")
	cmds.duplicate(cmds.textField('mesh_store', q=True, tx=True), rr=True, name=dupe_name)
	for attr in locked_attrs:
		unlock = dupe_name + attr
		cmds.setAttr (unlock, lock = False)
#move to the side based on bounding box size
	bounding = cmds.polyEvaluate(dupe_name, b=True)
	cmds.move ((bounding[0][1]-bounding[0][0])*2, 0, 0, dupe_name)
#custom attributes
	cmds.addAttr (dupe_name, longName='xRotation', at='double')
	cmds.setAttr (dupe_name + '.xRotation', cmds.getAttr(cmds.textField('joint_store', q=True, tx=True) + '.rx'))
	cmds.addAttr (dupe_name, longName='yRotation', at='double')
	cmds.setAttr (dupe_name + '.yRotation', cmds.getAttr(cmds.textField('joint_store', q=True, tx=True) + '.ry'))
	cmds.addAttr (dupe_name, longName='zRotation', at='double')
	cmds.setAttr (dupe_name + '.zRotation', cmds.getAttr(cmds.textField('joint_store', q=True, tx=True) + '.rz'))
	cmds.addAttr (dupe_name, longName='nameOfJoint', dt='string')
	cmds.setAttr (dupe_name + '.nameOfJoint', cmds.textField('joint_store', q=True, tx=True), type='string')
	
def get_blendshapes():
	cmds.textScrollList('blendshape_list', e=True, ra=True)
	cmds.textScrollList('blendshape_list', e=True, append=cmds.listAttr(cmds.textScrollList('blendnode_list', q=True, si=True), k=True, m=True))
#not finished

def Corrective_Shape_Monster():
	target_mesh=cmds.ls(sl=True)
	base_mesh=cmds.textField('mesh_store', q=True, tx=True)
	mesh_history=cmds.listHistory(base_mesh, ac = True)
	cmds.select(mesh_history)
	skin_node = cmds.ls(sl=True, typ='skinCluster')
	tweak_node = cmds.ls(sl=True, typ='tweak')
	cmds.select(d=True)
	if len(skin_node) is 0:
		errorcode(2)
	target_offset = [cmds.getAttr(target_mesh[0] + '.translateX') - cmds.getAttr(base_mesh + '.translateX'), cmds.getAttr(target_mesh[0] + '.translateY') - cmds.getAttr(base_mesh + '.translateY'), cmds.getAttr(target_mesh[0] + '.translateZ') - cmds.getAttr(base_mesh + '.translateZ')]
	print (cmds.polyEvaluate(target_mesh, v=True))
	print (cmds.polyEvaluate(base_mesh, v=True))
	#if (cmds.polyEvaluate(target_mesh, v=True)) is not (cmds.polyEvaluate(base_mesh, v=True)):
	#	errorcode(3)
	vertex_count = range(cmds.polyEvaluate(base_mesh, v=True))
	vertexWorldPos = []
	vertexTargetPos = []
	vertexRelativePos = []
	vertexNameList = []
	for vert in vertex_count:
		base_mesh_vertex = base_mesh + '.vtx[' + str(vert) + ']'
		target_mesh_vertex = target_mesh[0] + '.vtx[' + str(vert) + ']'
		vertex_data = vertex_position(target_mesh_vertex, base_mesh_vertex, target_offset[0], target_offset[1], target_offset[2])
		if vertex_data[0] is 1:
			vertexNameList.append (base_mesh_vertex)
			vertexWorldPos.append([vertex_data[1], vertex_data[2], vertex_data[3]])
			vertexTargetPos.append([vertex_data[4], vertex_data[5], vertex_data[6]])
			vertexRelativePos.append([vertex_data[7], vertex_data[8], vertex_data[9]])
			vertexNumber = 0
	for vertexName in vertexNameList:
		vertex_Vector_Move(vertexName, vertexWorldPos[vertexNumber], vertexTargetPos[vertexNumber], vertexRelativePos[vertexNumber])
		vertexNumber += 1
	cmds.setAttr (skin_node[0] + '.envelope', 0)
	toggleDeformers(base_mesh, 0)
	duplicate_name = cmds.textField('blendname_input', q=True, tx=True) + cmds.textField('blendname_suffix', q=True, tx=True)
	duplicate_name = duplicate_name.replace (" ", "_")
	cmds.duplicate (base_mesh, name = duplicate_name, rr=True, rc=True)
	locked_attrs =['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
	for attr in locked_attrs:
		unlock = duplicate_name + attr
		cmds.setAttr (unlock, lock = False)
	cmds.setAttr (skin_node[0] + '.envelope', 1)
	toggleDeformers(base_mesh, 1)
	for vertexname in vertexNameList:
		cmds.setAttr (vertexname, 0,0,0)
	shapesInNode = len(cmds.listAttr (cmds.textScrollList('blendnode_list', q=True, si=True), k = True, m = True))
	cmds.blendShape( cmds.textScrollList('blendnode_list', q=True, si=True), edit=True, t=(base_mesh, shapesInNode, duplicate_name, 1))
	if cmds.checkBox('deletesculpt_check', q=True, value=True) is True:
		cmds.delete(target_mesh[0])
	if cmds.checkBox('deletecorrection_check', q=True, value=True) is True:
		cmds.delete(duplicate_name)
		
		
def toggleDeformers(mesh, value):
	mesh_history = cmds.listHistory(mesh, ac = True)
	cmds.select(mesh_history)
	print (mesh_history)
	blend_nodes = cmds.ls(sl=True, typ='blendShape')
	print (blend_nodes)
	for node in blend_nodes:
		print (node)
		cmds.setAttr (node + '.envelope', value)
	cmds.select(d=True)

def vertex_Vector_Move(vertexName, vertexWorldPos, vertexTargetPos, vertexRelativePos):
	
	theMatrix = [0,0,0,0,0,0,0,0,0,0,0,0]
	moveVec = []
	cmds.move(1, 0, 0, vertexName, r=True)
	tempPos = cmds.pointPosition(vertexName, w=True)
	
	theMatrix[0] = tempPos[0]-vertexWorldPos[0]
	theMatrix[4] = tempPos[1]-vertexWorldPos[1]
	theMatrix[8] = tempPos[2]-vertexWorldPos[2]
	theMatrix[3] = vertexTargetPos[0]
	
	cmds.move(-1, 1, 0, vertexName, r=True)
	tempPos = cmds.pointPosition(vertexName, w=True)
	theMatrix[1] = tempPos[0]-vertexWorldPos[0]
	theMatrix[5] = tempPos[1]-vertexWorldPos[1]
	theMatrix[9] = tempPos[2]-vertexWorldPos[2]
	theMatrix[7] = vertexTargetPos[1]
	
	#print (tempPos)
	
	cmds.move(0, -1, 1, vertexName, r=True)
	tempPos = cmds.pointPosition(vertexName, w=True)
	theMatrix[2] = tempPos[0]-vertexWorldPos[0]
	theMatrix[6] = tempPos[1]-vertexWorldPos[1]
	theMatrix[10] = tempPos[2]-vertexWorldPos[2]
	theMatrix[11] = vertexTargetPos[2]
	print (vertexName)
	print (theMatrix)
	
	
	cmds.move(0, 0, -1, vertexName, r=True)
	
	denominator = (
	(theMatrix[0] * ((theMatrix[5]*theMatrix[10]) - (theMatrix[6]*theMatrix[9]))) -
	(theMatrix[1] * ((theMatrix[4]*theMatrix[10]) - (theMatrix[6]*theMatrix[8]))) +
	(theMatrix[2] * ((theMatrix[4]*theMatrix[9] ) - (theMatrix[5]*theMatrix[8]))))
	print type(denominator)
	print (denominator)
	moveVec = [0, 0, 0]
	if denominator > 0.001:
		moveVec[0] = (
		((theMatrix[3] * ((theMatrix[5]*theMatrix[10]) - (theMatrix[6]*theMatrix[9]))) -
		(theMatrix[1] * ((theMatrix[7]*theMatrix[10]) - (theMatrix[6]*theMatrix[11]))) +
		(theMatrix[2] * ((theMatrix[7]*theMatrix[9] ) - (theMatrix[5]*theMatrix[11])))) / denominator)
		
		moveVec[1] = (
		((theMatrix[0] * ((theMatrix[7]*theMatrix[10]) - (theMatrix[6]*theMatrix[11]))) -
		(theMatrix[3] * ((theMatrix[4]*theMatrix[10]) - (theMatrix[6]*theMatrix[8]))) +
		(theMatrix[2] * ((theMatrix[4]*theMatrix[11]) - (theMatrix[7]*theMatrix[8])))) / denominator)
		
		moveVec[2] = (
		((theMatrix[0] * ((theMatrix[5]*theMatrix[11]) - (theMatrix[7]*theMatrix[9]))) -
		(theMatrix[1] * ((theMatrix[4]*theMatrix[11]) - (theMatrix[7]*theMatrix[8]))) +
		(theMatrix[3] * ((theMatrix[4]*theMatrix[9] ) - (theMatrix[5]*theMatrix[8])))) / denominator)
	
			
		cmds.move(moveVec[0], moveVec[1], moveVec[2], vertexName, r=True)
		
		print ('moveVec =')
		print (moveVec)
		
	
def key_blend():
	if cmds.radioButton('TimeRadio', q=True, sl=True) is True:
		cmds.setKeyframe(cmds.textScrollList('blendnode_list', q=True, si=True)[0] + '.' + cmds.textScrollList('blendshape_list', q=True, si=True)[0])
	else:
		if len(cmds.textField('joint_store', q=True, tx=True)) is 0:
			errorcode(5)
		if cmds.radioButton('blend_radio_X_ui', q=True, sl=True) is True:
			joint_Axis = '.rx'
		if cmds.radioButton('blend_radio_Y_ui', q=True, sl=True) is True:
			joint_Axis = '.ry'
		if cmds.radioButton('blend_radio_Z_ui', q=True, sl=True) is True:
			joint_Axis = '.rz'
		driverjoint = cmds.textField('joint_store', q=True, tx=True) + joint_Axis
		drivenshape = (cmds.textScrollList('blendnode_list', q=True, si=True)[0] + '.' + cmds.textScrollList('blendshape_list', q=True, si=True)[0])
		print (driverjoint + '|' + drivenshape)
		cmds.setDrivenKeyframe (drivenshape , cd= driverjoint )
	
def show_curve():
	cmds.select(cmds.textField('mesh_store', q=True, tx=True), r = True)
	cmds.select(cmds.textScrollList('blendnode_list', q=True, si=True), addFirst = True)
	mel.eval('GraphEditor; FrameSelected;')

def vertex_position(Target_Vertex, Base_Vertex, offsetX, offsetY, offsetZ):
	targetVertWorld = cmds.pointPosition(Target_Vertex, w=True)
	baseVertPos = cmds.pointPosition(Base_Vertex, w=True)
	relVertPos = cmds.getAttr (Base_Vertex)
	
	targetPos = [targetVertWorld[0] - (baseVertPos[0] + offsetX), targetVertWorld[1] - (baseVertPos[1] + offsetY), targetVertWorld[2] - (baseVertPos[2] + offsetZ)]
	
	if 0.001 > targetPos[0] > -0.001 and 0.001 > targetPos[1] > -0.001 and 0.001 > targetPos[2] > -0.001:
		return [0]
	else:
		return [1, baseVertPos[0], baseVertPos[1], baseVertPos[2], targetPos[0], targetPos[1], targetPos[2], relVertPos[0][0], relVertPos[0][1], relVertPos[0][2]]
		
def set_blend_amount():
	slider_value = cmds.intSlider('blend_shape_slider_ui', query=True, v=True) / 100.0
	cmds.setAttr ( cmds.textScrollList('blendnode_list', q=True, si=True)[0] + '.' + cmds.textScrollList('blendshape_list', q=True, si=True)[0] , slider_value)
	cmds.textField('blend_percent_ui', e=True, tx= str(cmds.intSlider('blend_shape_slider_ui', query=True, v=True)) + '%')
	#if cmds.radioButton('blend_radio_X_ui', q=True, value=True) = True
	#	joint_Axis = '.rx'
	#if cmds.radioButton('blend_radio_Y_ui', q=True, value=True) = True
	#	joint_Axis = '.ry'
	#if cmds.radioButton('blend_radio_Z_ui', q=True, value=True) = True
		#joint_Axis = '.rz'