import bpy
import os
from ..main.common import *
import json

class Multilayered:
    def __init__(self, BasePath,image_format):
        self.BasePath = str(BasePath)
        self.image_format = image_format
    def createBaseMaterial(self,matTemplateObj,name):
        CT = imageFromPath(self.BasePath + matTemplateObj["colorTexture"]["DepotPath"]["$value"],self.image_format)
        NT = imageFromPath(self.BasePath + matTemplateObj["normalTexture"]["DepotPath"]["$value"],self.image_format,isNormal = True)
        RT = imageFromPath(self.BasePath + matTemplateObj["roughnessTexture"]["DepotPath"]["$value"],self.image_format,isNormal = True)
        MT = imageFromPath(self.BasePath + matTemplateObj["metalnessTexture"]["DepotPath"]["$value"],self.image_format,isNormal = True)
    
        TileMult = float(matTemplateObj.get("tilingMultiplier",1))

        NG = bpy.data.node_groups.new(name[:-11],"ShaderNodeTree")
        TMI = NG.inputs.new('NodeSocketVector','Tile Multiplier')
        TMI.default_value = (1,1,1)
        NG.outputs.new('NodeSocketColor','Color')
        NG.outputs.new('NodeSocketColor','Metalness')
        NG.outputs.new('NodeSocketColor','Roughness')
        NG.outputs.new('NodeSocketColor','Normal')
    
        CTN = create_node( NG.nodes, "ShaderNodeTexImage",(0,0),image = CT)
    
        MTN = create_node( NG.nodes, "ShaderNodeTexImage",(0,-50*1),image = MT)
    
        RTN = create_node( NG.nodes, "ShaderNodeTexImage",(0,-50*2),image = RT)
    
        NTN = create_node( NG.nodes, "ShaderNodeTexImage",(0,-50*3),image = NT)
    
        MapN = create_node( NG.nodes, "ShaderNodeMapping",(-310,-64))
    
        TexCordN = create_node( NG.nodes, "ShaderNodeTexCoord",(-500,-64))
    
        TileMultN = create_node( NG.nodes, "ShaderNodeValue", (-700,-45*2))
        TileMultN.outputs[0].default_value = TileMult
    
        GroupInN = create_node( NG.nodes, "NodeGroupInput", (-700,-45*4))
    
        VecMathN = create_node( NG.nodes, "ShaderNodeVectorMath", (-500,-45*3), operation = 'MULTIPLY')
    
        NormSepN = create_node( NG.nodes, "ShaderNodeSeparateRGB", (300,-150))
    
        NormCombN = create_node( NG.nodes, "ShaderNodeCombineRGB", (500,-150))
        NormCombN.inputs[2].default_value = 1
    
        GroupOutN = create_node( NG.nodes, "NodeGroupOutput", (700,0))
    
        NG.links.new(TexCordN.outputs['UV'],MapN.inputs['Vector'])
        NG.links.new(VecMathN.outputs[0],MapN.inputs['Scale'])
        NG.links.new(MapN.outputs['Vector'],CTN.inputs['Vector'])
        NG.links.new(MapN.outputs['Vector'],NTN.inputs['Vector'])
        NG.links.new(MapN.outputs['Vector'],RTN.inputs['Vector'])
        NG.links.new(MapN.outputs['Vector'],MTN.inputs['Vector'])
        NG.links.new(TileMultN.outputs[0],VecMathN.inputs[0])
        NG.links.new(GroupInN.outputs[0],VecMathN.inputs[1])
        NG.links.new(CTN.outputs[0],GroupOutN.inputs[0])
        NG.links.new(MTN.outputs[0],GroupOutN.inputs[1])
        NG.links.new(RTN.outputs[0],GroupOutN.inputs[2])
        NG.links.new(NTN.outputs[0],NormSepN.inputs[0])
        NG.links.new(NormSepN.outputs[0],NormCombN.inputs[0])
        NG.links.new(NormSepN.outputs[1],NormCombN.inputs[1])
        NG.links.new(NormCombN.outputs[0],GroupOutN.inputs[3])
    
        return

    

    def setGlobNormal(self,normalimgpath,CurMat,input):
        GNN = create_node(CurMat.nodes, "ShaderNodeVectorMath",(-200,-250),operation='NORMALIZE')        
            
        GNA = create_node(CurMat.nodes, "ShaderNodeVectorMath",(-400,-250),operation='ADD')
    
        GNS = create_node(CurMat.nodes, "ShaderNodeVectorMath", (-600,-250),operation='SUBTRACT')
    
        GNGeo = create_node(CurMat.nodes, "ShaderNodeNewGeometry", (-800,-250))
    
        GNMap = CreateShaderNodeNormalMap(CurMat,self.BasePath + normalimgpath,-600,-550,'GlobalNormal',self.image_format)
        CurMat.links.new(GNGeo.outputs['Normal'],GNS.inputs[1])
        CurMat.links.new(GNMap.outputs[0],GNS.inputs[0])
        CurMat.links.new(GNS.outputs[0],GNA.inputs[1])
        CurMat.links.new(input,GNA.inputs[0])
        CurMat.links.new(GNA.outputs[0],GNN.inputs[0])
        return GNN.outputs[0]

    def createLayerMaterial(self,LayerName,LayerCount,CurMat,mlmaskpath,normalimgpath):
        
        for x in range(LayerCount-1):
            MaskTexture = imageFromPath(os.path.splitext(self.BasePath + mlmaskpath)[0]+"_"+str(x+1)+".png",self.image_format,isNormal = True)
            NG = bpy.data.node_groups.new("Layer_Blend_"+str(x),"ShaderNodeTree")#create layer's node group
            NG.inputs.new('NodeSocketColor','Color A')
            NG.inputs.new('NodeSocketColor','Metalness A')
            NG.inputs.new('NodeSocketColor','Roughness A')
            NG.inputs.new('NodeSocketColor','Normal A')
            NG.inputs.new('NodeSocketColor','Color B')
            NG.inputs.new('NodeSocketColor','Metalness B')
            NG.inputs.new('NodeSocketColor','Roughness B')
            NG.inputs.new('NodeSocketColor','Normal B')
            NG.inputs.new('NodeSocketColor','Mask')
            NG.outputs.new('NodeSocketColor','Color')
            NG.outputs.new('NodeSocketColor','Metalness')
            NG.outputs.new('NodeSocketColor','Roughness')
            NG.outputs.new('NodeSocketColor','Normal')
        
            GroupInN = create_node(NG.nodes,"NodeGroupInput", (-700,0), hide=False)
        
            GroupOutN = create_node(NG.nodes,"NodeGroupOutput",(200,0))
        
            ColorMixN = create_node(NG.nodes,"ShaderNodeMixRGB", (-300,100), label="Color Mix")
                    
            MetalMixN = create_node(NG.nodes,"ShaderNodeMixRGB", (-300,50), label = "Metal Mix")
        
            RoughMixN = create_node(NG.nodes,"ShaderNodeMixRGB", (-300,0), label = "Rough Mix")
        
            NormalMixN = create_node(NG.nodes,"ShaderNodeMixRGB",(-300,-50), label = "Normal Mix")
        
            LayerGroupN = create_node(CurMat.nodes,"ShaderNodeGroup", (-1400,400-100*x))
            LayerGroupN.node_tree = NG
            LayerGroupN.name = "Layer_"+str(x)
        
            MaskN = create_node(CurMat.nodes,"ShaderNodeTexImage",(-2400,400-100*x), image = MaskTexture,label="Layer_"+str(x+1))
            
            #if self.flipMaskY:
            # Mask flip deprecated in WolvenKit deveolpment build 8.7+
            #MaskN.texture_mapping.scale[1] = -1 #flip mask if needed
            
            if x == 0:
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"0"].outputs[0],LayerGroupN.inputs[0])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"0"].outputs[1],LayerGroupN.inputs[1])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"0"].outputs[2],LayerGroupN.inputs[2])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"0"].outputs[3],LayerGroupN.inputs[3])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"1"].outputs[0],LayerGroupN.inputs[4])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"1"].outputs[1],LayerGroupN.inputs[5])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"1"].outputs[2],LayerGroupN.inputs[6])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+"1"].outputs[3],LayerGroupN.inputs[7])
            else:
                CurMat.links.new(CurMat.nodes["Layer_"+str(x-1)].outputs[0],LayerGroupN.inputs[0])
                CurMat.links.new(CurMat.nodes["Layer_"+str(x-1)].outputs[1],LayerGroupN.inputs[1])
                CurMat.links.new(CurMat.nodes["Layer_"+str(x-1)].outputs[2],LayerGroupN.inputs[2])
                CurMat.links.new(CurMat.nodes["Layer_"+str(x-1)].outputs[3],LayerGroupN.inputs[3])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].outputs[0],LayerGroupN.inputs[4])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].outputs[1],LayerGroupN.inputs[5])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].outputs[2],LayerGroupN.inputs[6])
                CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].outputs[3],LayerGroupN.inputs[7])
            CurMat.links.new(MaskN.outputs[0],CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].inputs[7])
            CurMat.links.new(CurMat.nodes["Mat_Mod_Layer_"+str(x+1)].outputs[4],CurMat.nodes["Layer_"+str(x)].inputs[8])
            
            NG.links.new(GroupInN.outputs[0],ColorMixN.inputs[1])
            NG.links.new(GroupInN.outputs[1],MetalMixN.inputs[1])
            NG.links.new(GroupInN.outputs[2],RoughMixN.inputs[1])
            NG.links.new(GroupInN.outputs[3],NormalMixN.inputs[1])
            NG.links.new(GroupInN.outputs[4],ColorMixN.inputs[2])
            NG.links.new(GroupInN.outputs[5],MetalMixN.inputs[2])
            NG.links.new(GroupInN.outputs[6],RoughMixN.inputs[2])
            NG.links.new(GroupInN.outputs[7],NormalMixN.inputs[2])
            NG.links.new(GroupInN.outputs[8],ColorMixN.inputs[0])
            NG.links.new(GroupInN.outputs[8],NormalMixN.inputs[0])
            NG.links.new(GroupInN.outputs[8],RoughMixN.inputs[0])
            NG.links.new(GroupInN.outputs[8],MetalMixN.inputs[0])
        
            NG.links.new(ColorMixN.outputs[0],GroupOutN.inputs[0])
            NG.links.new(NormalMixN.outputs[0],GroupOutN.inputs[3])
            NG.links.new(RoughMixN.outputs[0],GroupOutN.inputs[2])
            NG.links.new(MetalMixN.outputs[0],GroupOutN.inputs[1])
        
        CurMat.links.new(CurMat.nodes["Layer_"+str(LayerCount-2)].outputs[0],CurMat.nodes['Principled BSDF'].inputs['Base Color'])
        if normalimgpath:
            yoink = self.setGlobNormal(normalimgpath,CurMat,CurMat.nodes["Layer_"+str(LayerCount-2)].outputs[3])
            CurMat.links.new(yoink,CurMat.nodes['Principled BSDF'].inputs['Normal'])
        else:
            CurMat.links.new(CurMat.nodes["Layer_"+str(LayerCount-2)].outputs[3],CurMat.nodes['Principled BSDF'].inputs['Normal'])
        CurMat.links.new(CurMat.nodes["Layer_"+str(LayerCount-2)].outputs[2],CurMat.nodes['Principled BSDF'].inputs['Roughness'])
        CurMat.links.new(CurMat.nodes["Layer_"+str(LayerCount-2)].outputs[1],CurMat.nodes['Principled BSDF'].inputs['Metallic'])
        return


    def create(self,Data,Mat):

        file = open(self.BasePath + Data["MultilayerSetup"] + ".json",mode='r')
        mlsetup = json.loads(file.read())["Data"]["RootChunk"]
        file.close()
        xllay = mlsetup.get("layers")
        if xllay is None:
            xllay = x.get("Layers")
        LayerCount = len(xllay)
    
        LayerIndex = 0
        CurMat = Mat.node_tree
        for x in (xllay):            
            MatTile = x.get("matTile")
            if MatTile is None:
                MatTile = x.get("MatTile")
            MbTile = x.get("mbTile")
            if MbTile is None:
                MbTile = x.get("MbTile")

            MbScale = 1
            if MatTile != None:
                MbScale = float(MatTile)
            if MbTile != None:
                MbScale = float(MbTile)
        
            Microblend = x["microblend"]["DepotPath"].get("$value")
            if Microblend is None:
                Microblend = x["Microblend"].get("$value")

            MicroblendContrast = x.get("microblendContrast")
            if MicroblendContrast is None:
                MicroblendContrast = x.get("Microblend",1)

            microblendNormalStrength = x.get("microblendNormalStrength")
            if microblendNormalStrength is None:
                microblendNormalStrength = x.get("MicroblendNormalStrength")

            opacity = x.get("opacity")
            if opacity is None:
                opacity = x.get("Opacity")
				
            material = x["material"]["DepotPath"].get("$value")
            if material is None:
                material = x["Material"]["DepotPath"].get("$value")

            colorScale = x["colorScale"].get("$value")
            if colorScale is None:
                colorScale = x["ColorScale"].get("$value")

            normalStrength = x["normalStrength"].get("$value")
            if normalStrength is None:
                normalStrength = x["NormalStrength"].get("$value")

            #roughLevelsIn = x["roughLevelsIn"]
            roughLevelsOut = x["roughLevelsOut"].get("$value")
            if roughLevelsOut is None:
                roughLevelsOut = x["RoughLevelsOut"].get("$value")

            #metalLevelsIn = x["metalLevelsIn"]
            metalLevelsOut = x["metalLevelsOut"].get("$value")
            if metalLevelsOut is None:
                metalLevelsOut = x["MetalLevelsOut"].get("$value")

            if Microblend != "null":
                MBI = imageFromPath(self.BasePath+Microblend,self.image_format,True)

            file = open(self.BasePath + material + ".json",mode='r')
            mltemplate = json.loads(file.read())["Data"]["RootChunk"]
            file.close()
            OverrideTable = createOverrideTable(mltemplate)#get override info for colors and what not

            NG = bpy.data.node_groups.new(os.path.basename(Data["MultilayerSetup"])[:-8]+"_Layer_"+str(LayerIndex),"ShaderNodeTree")#create layer's node group
            NG.inputs.new('NodeSocketColor','ColorScale')
            NG.inputs.new('NodeSocketFloat','MatTile')
            NG.inputs.new('NodeSocketFloat','MbTile')
            NG.inputs.new('NodeSocketFloat','MicroblendNormalStrength')
            NG.inputs.new('NodeSocketFloat','MicroblendContrast')
            NG.inputs.new('NodeSocketFloat','NormalStrength')
            NG.inputs.new('NodeSocketFloat','Opacity')
            NG.inputs.new('NodeSocketColor','Mask')
            NG.outputs.new('NodeSocketColor','Color')
            NG.outputs.new('NodeSocketColor','Metalness')
            NG.outputs.new('NodeSocketColor','Roughness')
            NG.outputs.new('NodeSocketColor','Normal')
            NG.outputs.new('NodeSocketColor','Layer Mask')
            
            NG.inputs[4].min_value = 0
            NG.inputs[6].min_value = 0
            NG.inputs[6].max_value = 1
            
            LayerGroupN = create_node(CurMat.nodes, "ShaderNodeGroup", (-2000,500-100*LayerIndex))
            LayerGroupN.width = 400
            LayerGroupN.node_tree = NG
            LayerGroupN.name = "Mat_Mod_Layer_"+str(LayerIndex)
            LayerIndex += 1
            
            GroupInN = create_node(NG.nodes, "NodeGroupInput", (-2600,0))
            
            GroupOutN = create_node(NG.nodes, "NodeGroupOutput", (200,0))

            if not bpy.data.node_groups.get(os.path.basename(material)[:-11]):
                self.createBaseMaterial(mltemplate,os.path.basename(material))

            BaseMat = bpy.data.node_groups.get(os.path.basename(material)[:-11])
            if BaseMat:
                BMN = create_node(NG.nodes,"ShaderNodeGroup", (-2000,0))
                BMN.width = 300
                BMN.node_tree = BaseMat
            
            # SET LAYER GROUP DEFAULT VALUES
            if colorScale != None and colorScale in OverrideTable["ColorScale"].keys():
                LayerGroupN.inputs[0].default_value = OverrideTable["ColorScale"][colorScale]
            else:
                LayerGroupN.inputs[0].default_value = (1.0,1.0,1.0,1)
            
            if MatTile != None:
                LayerGroupN.inputs[1].default_value = float(MatTile)
            else:
                LayerGroupN.inputs[1].default_value = 1
            
            if MbScale != None:
                LayerGroupN.inputs[2].default_value = float(MbScale)
            else:
                LayerGroupN.inputs[2].default_value = 1
            
            if microblendNormalStrength != None:
                LayerGroupN.inputs[3].default_value = float(microblendNormalStrength)
            else:
                LayerGroupN.inputs[3].default_value = 1
            
            if MicroblendContrast != None:
                LayerGroupN.inputs[4].default_value = float(MicroblendContrast)
            else:
                LayerGroupN.inputs[4].default_value = 1
            
            if normalStrength != None:
                LayerGroupN.inputs[5].default_value = OverrideTable["NormalStrength"][normalStrength]
            else:
                LayerGroupN.inputs[5].default_value = 1
            
            if opacity != None:
                LayerGroupN.inputs[6].default_value = float(opacity)
            else:
                LayerGroupN.inputs[6].default_value = 1
            
            
            # DEFINES MAIN MULTILAYERED PROPERTIES
        
            if colorScale != "null":
                ColorScaleMixN = create_node(NG.nodes,"ShaderNodeMixRGB",(-1500,50),blend_type='MULTIPLY')
                ColorScaleMixN.inputs[0].default_value=1
            
            MBN = create_node(NG.nodes,"ShaderNodeTexImage",(-2050,-250),image = MBI,label = "Microblend")
            
            MBRGBCurveN = create_node(NG.nodes,"ShaderNodeRGBCurve",(-1600,-250))
            MBRGBCurveN.mapping.curves[0].points[0].location = (0,1)
            MBRGBCurveN.mapping.curves[0].points[1].location = (1,0)
            MBRGBCurveN.mapping.curves[1].points[0].location = (0,1)
            MBRGBCurveN.mapping.curves[1].points[1].location = (1,0)
            
            MBGrtrThanN = create_node(NG.nodes,"ShaderNodeMath", (-1200,-350),operation = 'GREATER_THAN')
            MBGrtrThanN.inputs[1].default_value = 0
            
            MBMixN = create_node(NG.nodes,"ShaderNodeMixRGB", (-1200,-400), blend_type ='MIX')
            
            MBMixColorRamp = create_node(NG.nodes,"ShaderNodeValToRGB", (-1100,-500))
            MBMixColorRamp.color_ramp.elements.remove(MBMixColorRamp.color_ramp.elements[1])
            MBMix_colors = [(0.25,0.25,0.25,1), (1,1,1,1)]
            MBMix_positions = [0.9, 0.99608]
            
            elements = MBMixColorRamp.color_ramp.elements
            for i in range(len(MBMix_colors)):
                element = elements.new(MBMix_positions[i])
                element.color = MBMix_colors[i]
            
            MBMixNormStrength = create_node(NG.nodes,"ShaderNodeMixRGB", (-950,-350),blend_type ='MIX')
            MBMixNormStrength.inputs[2].default_value = (0.5,0.5,1.0,1.0)
            
            MBMapping = create_node(NG.nodes,"ShaderNodeMapping", (-2300,-50))
            
            MBTexCord = create_node(NG.nodes,"ShaderNodeTexCoord", (-2300,-100))
            
            MBNormAbsN = create_node(NG.nodes,"ShaderNodeMath", (-750,-300), operation = 'ABSOLUTE')
            
            MBNormalN = create_node(NG.nodes,"ShaderNodeNormalMap", (-750,-350))
            
            NormalCombineN = create_node(NG.nodes,"ShaderNodeVectorMath", (-550,-250))
            
            NormSubN = create_node(NG.nodes,"ShaderNodeVectorMath", (-550, -350), operation = 'SUBTRACT')
            
            NormalizeN =create_node(NG.nodes,"ShaderNodeVectorMath", (-350,-200), operation = 'NORMALIZE')
            
            GeoN = create_node(NG.nodes,"ShaderNodeNewGeometry", (-750, -450))
            
            NormStrengthN = create_node(NG.nodes,"ShaderNodeNormalMap", (-1200,-200), label = "NormalStrength")
         
            
            # Roughness
            RoughRampN = create_node(NG.nodes,"ShaderNodeMapRange", (-1400,-100), label = "Roughness Ramp")
            if roughLevelsOut in OverrideTable["RoughLevelsOut"].keys():
                RoughRampN.inputs['To Min'].default_value = (OverrideTable["RoughLevelsOut"][roughLevelsOut][1][0])
                RoughRampN.inputs['To Max'].default_value = (OverrideTable["RoughLevelsOut"][roughLevelsOut][0][0])
            
            
            # Metalness
            MetalRampN = create_node(NG.nodes,"ShaderNodeValToRGB", (-1400,-50),label = "Metal Ramp")
            if metalLevelsOut in OverrideTable["MetalLevelsOut"].keys():
                MetalRampN.color_ramp.elements[1].color = (OverrideTable["MetalLevelsOut"][metalLevelsOut][0])
                MetalRampN.color_ramp.elements[0].color = (OverrideTable["MetalLevelsOut"][metalLevelsOut][1])
            
			
			# Mask Layer
            MaskMBInvert = create_node(NG.nodes,"ShaderNodeInvert", (-1700,-350))
            MaskMBInvert.inputs[0].default_value = 1.0

            MaskRange = create_node(NG.nodes,"ShaderNodeMapRange", (-2200,-550))
            MaskRange.inputs['From Min'].default_value = (0)
            MaskRange.inputs['From Max'].default_value = (1)
            MaskRange.inputs['To Min'].default_value = (0)
            MaskRange.inputs['To Max'].default_value = (1)
            MaskRange.clamp = True

            MaskMBMultiplyAdd = create_node(NG.nodes,"ShaderNodeMath", (-2000,-650), operation = 'MULTIPLY_ADD')
            MaskMBMultiplyAdd.inputs[1].default_value = 1
            MaskMBMultiplyAdd.inputs[2].default_value = 0.5

            MaskMBAdd = create_node(NG.nodes,"ShaderNodeMath", (-1700,-650), operation = 'ADD')
            MaskMBAdd.inputs[0].default_value = 0

            MaskMBSubtract = create_node(NG.nodes,"ShaderNodeMath", (-1700,-750), operation = 'SUBTRACT')
            MaskMBSubtract.inputs[1].default_value = 1.0

            MaskRange2 = create_node(NG.nodes,"ShaderNodeMapRange", (-1400,-650))

            MaskMBContrastSubtract = create_node(NG.nodes,"ShaderNodeMath", (-1400,-550), operation = 'SUBTRACT')
            MaskMBContrastSubtract.inputs[0].default_value = 1.0

            MaskOpReroute = create_node(NG.nodes,"NodeReroute", (-1600,-650))

            MaskMBMix = create_node(NG.nodes,"ShaderNodeMix", (-900,-550), label = "MASK MB BLEND", blend_type ='LINEAR_LIGHT')
            MaskMBMix.data_type ='RGBA'

            MaskOpMix = create_node(NG.nodes,"ShaderNodeMixRGB", (-600,-550), label = "OPACITY MIX", blend_type ='MIX')
            MaskOpMix.inputs[1].default_value = (0,0,0,1)
            
            
            # CREATE FINAL LINKS
            NG.links.new(GroupInN.outputs[0],ColorScaleMixN.inputs[2])
            NG.links.new(GroupInN.outputs[1],BMN.inputs[0])
            NG.links.new(GroupInN.outputs[2],MBMapping.inputs[3])
            NG.links.new(GroupInN.outputs[3],MBGrtrThanN.inputs[0])
            NG.links.new(GroupInN.outputs[3],MBNormAbsN.inputs[0])
            NG.links.new(GroupInN.outputs[4],MaskMBMultiplyAdd.inputs[0])
            NG.links.new(GroupInN.outputs[4],MaskMBContrastSubtract.inputs[1])
            NG.links.new(GroupInN.outputs[5],NormStrengthN.inputs[0])
            NG.links.new(GroupInN.outputs[6],MaskOpReroute.inputs[0])
            NG.links.new(MaskOpReroute.outputs[0],MaskOpMix.inputs[0])
            NG.links.new(GroupInN.outputs[7],MaskRange.inputs[0])

            NG.links.new(MaskMBContrastSubtract.outputs[0],MaskMBMix.inputs[0])
            NG.links.new(MaskRange.outputs[0],MaskMBMix.inputs[6])
            NG.links.new(MaskRange2.outputs[0],MaskMBMix.inputs[7])

            NG.links.new(MaskMBMultiplyAdd.outputs[0],MaskMBAdd.inputs[1])
            NG.links.new(MaskMBMultiplyAdd.outputs[0],MaskMBSubtract.inputs[1])

            NG.links.new(MBN.outputs[1],MaskMBInvert.inputs[1])
            NG.links.new(MaskMBInvert.outputs[0],MaskRange2.inputs[0])
            NG.links.new(MaskMBAdd.outputs[0],MaskRange2.inputs[1])
            NG.links.new(MaskMBSubtract.outputs[0],MaskRange2.inputs[2])

            NG.links.new(MaskMBMix.outputs[2],MaskOpMix.inputs[2])

            NG.links.new(BMN.outputs[0],ColorScaleMixN.inputs[1])
            NG.links.new(BMN.outputs[1],MetalRampN.inputs[0])
            NG.links.new(BMN.outputs[2],RoughRampN.inputs[0])
            NG.links.new(BMN.outputs[3],NormStrengthN.inputs[1])
            
            NG.links.new(MBTexCord.outputs[2],MBMapping.inputs[0])
            NG.links.new(MBMapping.outputs[0],MBN.inputs[0])
            NG.links.new(MBN.outputs[0],MBRGBCurveN.inputs[1])
            NG.links.new(MBN.outputs[0],MBMixN.inputs[2])

            NG.links.new(MBMixColorRamp.outputs[0],MBMixNormStrength.inputs[0])
            
            NG.links.new(NormStrengthN.outputs[0],NormalCombineN.inputs[0])
            
            NG.links.new(MBGrtrThanN.outputs[0],MBMixN.inputs[0])
            NG.links.new(MBRGBCurveN.outputs[0],MBMixN.inputs[1])
            NG.links.new(MBMixN.outputs[0],MBMixNormStrength.inputs[1])
            NG.links.new(MBMixNormStrength.outputs[0],MBNormalN.inputs[1])
            NG.links.new(MBNormAbsN.outputs[0],MBNormalN.inputs[0])
            NG.links.new(MBNormalN.outputs[0],NormSubN.inputs[0])
            NG.links.new(GeoN.outputs['Normal'],NormSubN.inputs[1])
            NG.links.new(NormSubN.outputs[0],NormalCombineN.inputs[1])			
            NG.links.new(NormalCombineN.outputs[0],NormalizeN.inputs[0])
            
            NG.links.new(ColorScaleMixN.outputs[0],GroupOutN.inputs[0]) #Color output
            NG.links.new(MetalRampN.outputs[0],GroupOutN.inputs[1]) #Metalness output
            NG.links.new(RoughRampN.outputs[0],GroupOutN.inputs[2]) #Roughness output
            NG.links.new(NormalizeN.outputs[0],GroupOutN.inputs[3]) #Normal output
            NG.links.new(MaskOpMix.outputs[0],GroupOutN.inputs[4]) #Mask Layer output
        
        self.createLayerMaterial(os.path.basename(Data["MultilayerSetup"])[:-8]+"_Layer_",LayerCount,CurMat,Data["MultilayerMask"],Data["GlobalNormal"])