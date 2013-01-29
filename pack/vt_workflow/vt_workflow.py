###############################################################################
##
## Copyright (C) 2012-2013, NYU-Poly. 
## All rights reserved.
## Contact: fchirigati@nyu.edu
##
## This file is part of ReproZip.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of NYU-Poly nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################

from xml.etree.ElementTree import Element, SubElement, tostring
from workflow_utils import Module, Annotation, Location, Function, Parameter, Connection, Port

class VTWorkflow:
    """
    VTWorkflow represents a workflow object for the VisTrails workflow system.
    Basically, it allows the creation of a XML representing the workflow.
    """
    
    def __init__(self, schema_version):
        """
        Init method for VTWorkflow. It creates the workflow root of the XML.
        
        -> schema_version is the version of of the VT schema for the workflow
        """
        
        # Identifiers for the VT workflow
        self.__port_id = 0
        self.__module_id = 0
        self.__function_id = 0
        self.__location_id = 0
        self.__connection_id = 0
        self.__annotation_id = 0
        self.__parameter_id = 0
        
        # Workflow (root node of the XML file)
        self.__wf = Element('workflow')
        self.__wf.set('id', '0')
        self.__wf.set('name', 'untitled')
        self.__wf.set('version', schema_version)
        self.__wf.set('vistrail_id', '')
        self.__wf.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        self.__wf.set('xsi:schemaLocation', 'http://www.vistrails.org/workflow.xsd')
        
    def add_module(self, cache, name, namespace, package, version, return_obj):
        """
        Method used to add a module in the workflow.
        """
        
        module = Module(self.__module_id, cache, name, namespace, package, version)
        self.__module_id += 1
        
        module_elem = SubElement(self.__wf, 'module')
        module_elem.set('cache', cache)
        module_elem.set('id', str(module.id))
        module_elem.set('name', name)
        module_elem.set('namespace', namespace)
        module_elem.set('package', package)
        module_elem.set('version', version)
        
        module.sub_element = module_elem
        
        if return_obj:
            return module
    
    def add_annotation(self, wf_object, key, value, return_obj):
        """
        Method used to add an annotation in a workflow object.
        """
        
        annotation = Annotation(self.__annotation_id, wf_object, key, value)
        self.__annotation_id += 1
        
        annotation_elem = SubElement(wf_object.sub_element, 'annotation')
        annotation_elem.set('id', str(annotation.id))
        annotation_elem.set('key', key)
        annotation_elem.set('value', value)
        
        annotation.sub_element = annotation_elem
        
        if return_obj:
            return annotation
    
    def add_location(self, module, x, y, return_obj):
        """
        Method used to add a location for a VisTrails module.
        """
        
        location = Location(self.__location_id, module, x, y)
        self.__location_id += 1
        
        location_elem = SubElement(module.sub_element, 'location')
        location_elem.set('id', str(location.id))
        location_elem.set('x', x)
        location_elem.set('y', y)
        
        location.sub_element = location_elem
        
        if return_obj:
            return location
    
    def add_function(self, module, name, pos, return_obj):
        """
        Method used to add a function to a VisTrails module.
        """
        
        function = Function(self.__function_id, module, name, pos)
        self.__function_id += 1
        
        function_elem = SubElement(module.sub_element, 'function')
        function_elem.set('id', str(function.id))
        function_elem.set('name', name)
        function_elem.set('pos', pos)
        
        function.sub_element = function_elem
        
        if return_obj:
            return function
    
    def add_parameter(self, function, alias, name, pos, type, value, return_obj):
        """
        Method used to add a parameter to a VisTrails module function.
        """
        
        parameter = Parameter(self.__parameter_id, function, alias, name, pos,
                              type, value)
        self.__parameter_id += 1
        
        parameter_elem = SubElement(function.sub_element, 'parameter')
        parameter_elem.set('alias', alias)
        parameter_elem.set('id', str(parameter.id))
        parameter_elem.set('name', name)
        parameter_elem.set('pos', pos)
        parameter_elem.set('type', type)
        parameter_elem.set('val', value)
        
        parameter.sub_element = parameter_elem
        
        if return_obj:
            return parameter
        
    def add_connection(self, source, dst, return_obj):
        """
        Method used to add a connection in the workflow.
        """
        
        conn = Connection(self.__connection_id, source, dst)
        self.__connection_id += 1
        
        conn_elem = SubElement(self.__wf, 'connection')
        conn_elem.set('id', str(conn.id))
        
        conn.sub_element = conn_elem
        
        port_elem = SubElement(conn.sub_element, 'port')
        port_elem.set('id', str(source.id))
        port_elem.set('moduleId', str(source.module.id))
        port_elem.set('moduleName', source.module.name)
        port_elem.set('name', source.name)
        port_elem.set('signature', source.signature)
        port_elem.set('type', 'source')

        port_elem = SubElement(conn.sub_element, 'port')
        port_elem.set('id', str(dst.id))
        port_elem.set('moduleId', str(dst.module.id))
        port_elem.set('moduleName', dst.module.name)
        port_elem.set('name', dst.name)
        port_elem.set('signature', dst.signature)
        port_elem.set('type', 'destination')
        
        if return_obj:
            return conn
        
    def create_port(self, module, name, signature):
        """
        Method used to create a port in a VisTrails module.
        This method DOES NOT add the port to the workflow; the method
        add_connection must be called for this purpose.
        """
        
        port = Port(self.__port_id, module, name, signature)
        self.__port_id += 1
        
        return port
    
    def get_str_repr(self):
        """
        Method used to return a string representation of the workflow.
        """
        
        return tostring(self.__wf, 'utf-8')
        