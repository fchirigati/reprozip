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

class WfObject:
    """
    WfObject represents a VisTrails workflow object.
    """
    
    def __init__(self):
        """
        Init method for WfObject
        """
        
        self.__sub_element = None
        

    def get_sub_element(self):
        return self.__sub_element


    def set_sub_element(self, value):
        self.__sub_element = value

    sub_element = property(get_sub_element, set_sub_element, None, None)


class Module(WfObject):
    """
    Module represents a module in the VisTrails workflow.
    """
    
    def __init__(self, id, cache, name, namespace, package, version):
        """
        Init method for Module.
        
        -> id is the unique id of the object;
        -> cache indicates whether the module is cacheable or not;
        -> name is the name of the module;
        -> namespace is the namespace of the module;
        -> package is the package that contains the module;
        -> version is the version of the package
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__cache = cache
        self.__name = name
        self.__namespace = namespace
        self.__package = package
        self.__version = version


    def get_id(self):
        return self.__id


    def get_cache(self):
        return self.__cache


    def get_name(self):
        return self.__name


    def get_namespace(self):
        return self.__namespace


    def get_package(self):
        return self.__package


    def get_version(self):
        return self.__version

    id = property(get_id, None, None, None)
    cache = property(get_cache, None, None, None)
    name = property(get_name, None, None, None)
    namespace = property(get_namespace, None, None, None)
    package = property(get_package, None, None, None)
    version = property(get_version, None, None, None)
    

class Annotation(WfObject):
    """
    Annotation represents an annotation in an object of the VisTrails workflow.
    """
    
    def __init__(self, id, wf_object, key, value):
        """
        Init method for Annotation.
        
        -> id is the unique id of the annotation;
        -> wf_object is the object from the workflow with which the annotation
           is associated;
        -> key is the key of the annotation;
        -> value is the value of the annotation
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__wf_object = wf_object
        self.__key = key
        self.__value = value
        

    def get_id(self):
        return self.__id


    def get_wf_object(self):
        return self.__wf_object


    def get_key(self):
        return self.__key


    def get_value(self):
        return self.__value
    

    id = property(get_id, None, None, None)
    wf_object = property(get_wf_object, None, None, None)
    key = property(get_key, None, None, None)
    value = property(get_value, None, None, None)
    
    
class Location(WfObject):
    """
    Location represents the location of a VisTrails module.
    """
    
    def __init__(self, id, module, x, y):
        """
        Init method for Location.
        
        -> id is the unique id of the object;
        -> module is the module with which the location is associated;
        -> x is the position in the x axis;
        -> y is the position in the y axis
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__module = module
        self.__x = x
        self.__y = y
        

    def get_id(self):
        return self.__id


    def get_module(self):
        return self.__module


    def get_x(self):
        return self.__x


    def get_y(self):
        return self.__y


    id = property(get_id, None, None, None)
    module = property(get_module, None, None, None)
    x = property(get_x, None, None, None)
    y = property(get_y, None, None, None)
    
    
class Function(WfObject):
    """
    Function represents a function of a VisTrails module.
    """
    
    def __init__(self, id, module, name, pos):
        """
        Init method for Function.
        
        -> id is the unique id of the object;
        -> module is the module with which the function is associated;
        -> name is the name of the function;
        -> pos is... well, pos :-)
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__module = module
        self.__name = name
        self.__pos = pos
        

    def get_id(self):
        return self.__id


    def get_module(self):
        return self.__module


    def get_name(self):
        return self.__name


    def get_pos(self):
        return self.__pos
    

    id = property(get_id, None, None, None)
    module = property(get_module, None, None, None)
    name = property(get_name, None, None, None)
    pos = property(get_pos, None, None, None)
    
    
class Parameter(WfObject):
    """
    Parameter represents the parameter for a function in a VisTrails workflow.
    """
    
    def __init__(self, id, function, alias, name, pos, type, value):
        """
        Init method for Parameter.
        
        -> id is the unique id of the object;
        -> function is the function with which the parameter is associated;
        -> alias is an alias for the parameter;
        -> name is the name of the parameter;
        -> pos is, well... pos :-)
        -> type represents the type of the parameter;
        -> value is the value of the parameter, respecting the type
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__function = function
        self.__alias = alias
        self.__name = name
        self.__pos = pos
        self.__type = type
        self.__value = value
        

    def get_id(self):
        return self.__id


    def get_function(self):
        return self.__function


    def get_alias(self):
        return self.__alias


    def get_name(self):
        return self.__name


    def get_pos(self):
        return self.__pos


    def get_type(self):
        return self.__type


    def get_value(self):
        return self.__value


    id = property(get_id, None, None, None)
    function = property(get_function, None, None, None)
    alias = property(get_alias, None, None, None)
    name = property(get_name, None, None, None)
    pos = property(get_pos, None, None, None)
    type = property(get_type, None, None, None)
    value = property(get_value, None, None, None)
        

class Connection(WfObject):
    """
    Connection represents a connection in a VisTrails workflow.
    """
    
    def __init__(self, id, source, dst):
        """
        Init method for Connection.
        
        -> id is the unique id of the object;
        -> source is the source port of the connection;
        -> dst is the destination port of the connection
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__source = source
        self.__dst = dst


    def get_id(self):
        return self.__id


    def get_source(self):
        return self.__source


    def get_dst(self):
        return self.__dst
    

    id = property(get_id, None, None, None)
    source = property(get_source, None, None, None)
    dst = property(get_dst, None, None, None)
        
        
class Port(WfObject):
    """
    Port represents a port in a VisTrails connection.
    """
    
    def __init__(self, id, module, name, signature):
        """
        Init method for Port.
        
        -> id is the unique id of the object;
        -> module is the module with which the port is associated;
        -> name is the name of the port;
        -> signature is the signature of the port
        """
        
        WfObject.__init__(self)
        
        self.__id = id
        self.__module = module
        self.__name = name
        self.__signature = signature
        
        
    def get_id(self):
        return self.__id


    def get_module(self):
        return self.__module


    def get_name(self):
        return self.__name


    def get_signature(self):
        return self.__signature
    

    id = property(get_id, None, None, None)
    module = property(get_module, None, None, None)
    name = property(get_name, None, None, None)
    signature = property(get_signature, None, None, None)
