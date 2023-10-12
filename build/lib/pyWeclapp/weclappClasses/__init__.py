from .. import weclapp
from .salesOrder import *
from .salesInvoice import *
from .contract import *
from .customer import *
from .article import *
from .addresses import *
from .contact import *
from .shipment import *
from .quotation import *
from .ticket import *
from .extraInfoForApp import *



from typing import *




class WeclappClassCreator:
    def __init__(self, entityName:Literal["salesOrder", "shipment", "contract", "article", "etc."], expamleEntityId:str, targetDirectory:str):
        self.entity = weclapp.GET(entityName, expamleEntityId, query={"serializeNulls": ""})
        self.entityName = entityName
        self.targetDirectory = targetDirectory
        self.itemsNames = {
            "salesOrder": "orderItems",
            "shipment": "shipmentItems",
            "contract": "contractItems",
            "article": "articlePrices",
            } 
        self.classTemplates = []
    
    def capitalize(self, string:str):
        return string[:1].upper() + string[1:]
        
    def createclassTemplates(self, entityName:str, entity:dict) -> str:
        className = self.capitalize(entityName)
        fileContent = f"class {className}(BaseModel, Blueprint):\n"   
        itemsName = None
        
        for key, value in entity.items():
            if key == "customAttributes":
                fileContent += f"\t{key}: List[WeclappMetaData] = []\n"
                
            elif isinstance(value, list):
                if len(value) > 0:
                    childName = self.createclassTemplates(key, value[0])
                    fileContent += f"\t{key}: List[{childName}] = []\n"
                        
                if key == self.itemsNames.get(entityName, None):
                    itemsName = key
                    
            elif isinstance(value, dict):
                childName = self.createclassTemplates(key, value)
                fileContent += f"\t{key}: {childName} = "
                fileContent += "{}\n"
                
            else:
                attributeType = type(value)
                if attributeType.__name__ == "NoneType":
                    logging.warning(f"Attribute {key} of {entityName} is NoneType -> estimating type as str -> please check manually")
                    fileContent += f"\t{key}:str = None\n"
                else:
                    fileContent += f"\t{key}: {attributeType.__name__} = None\n"
                    
        # AutomationData
        fileContent += f"\n\n\n\t# AutomationData"
        fileContent += f'\tITEMS_NAME: str = "{itemsName}"\n'
        fileContent += f"\tUSED_ATTRIBUTES: dict = dict()\n"
        fileContent += f"\t__setattr__ = Blueprint.__setattr__\n\n\n"

        
        fileContent += f"\tdef __init__(self, **kwargs):\n"
        fileContent += f"\t\tBaseModel.__init__(self, **kwargs)\n"
        fileContent += f"\t\tBlueprint.__init__(self, self.ITEMS_NAME, self.USED_ATTRIBUTES)\n\n\n\n"
        self.classTemplates.append(fileContent)
        return className
        
        
        
    def createPythonFile(self):
        fileContent = f"from pyWeclapp.weclappClasses import Blueprint, WeclappMetaData\nfrom pydantic import BaseModel\nfrom typing import *\n\n\n\n"   
        _ = self.createclassTemplates(self.entityName, self.entity)
        
        
        for classTemplate in self.classTemplates:
            fileContent += classTemplate
        
        fileName = f"weclapp_{self.entityName}"
        with open(f"{self.targetDirectory}/{fileName}.py", "w+") as file:
            file.write(fileContent)
            
        self.updateInitFile(fileName)
    
    
    def updateInitFile(self, fileName:str):
        import os
        
        initPath = f"{self.targetDirectory}/__init__.py"
        currentImports = []
        if os.path.exists(initPath):
            with open(initPath, "r+") as file:
                for line in file.readlines():
                    if line.startswith(f"from ."):
                        currentImports.append(line.strip('\n'))
                        
        if not any(fileName in line for line in currentImports):
            currentImports.append(f"from .{fileName} import *")
            
        with open(f"{self.targetDirectory}/__init__.py", "w+") as file:
            currentImports.insert(0, "# dynamic File please do not edit\n")
            file.write("\n".join(currentImports))
            
                    
        
            
    
    
    