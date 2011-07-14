'''
Created on 22/09/2010

@author: piranna
'''

# Based on code from http://wiki.python.org/moin/ModulesAsPlugins


import imp, inspect, os

import louie


connect = louie.connect
send = louie.send

#def connect(receiver, signal=louie.All, sender=louie.Any, weak=True):
#    print >> sys.stderr, '*** connect', receiver, signal, sender, weak
#    return louie.connect(receiver, signal, sender, weak)

#def send(signal=louie.All, sender=louie.Anonymous, *arguments, **named):
#    print >> sys.stderr, '*** send', signal, sender, arguments, named
#    return louie.send(signal, sender, arguments, named)



class Plugin:
    """Base class for plugins"""
    dependencies = ()
    replaces = ()


class Manager:
    """Class to manage the plugins load and dependencies"""
    def __init__(self):
        """Constructor"""
        self.__loaded = {}
        self.__pending = set()


    def Load_Dir(self, path):
        """Load python modules from a defined path

        @param path: path of the dir containing the modules to load
        @type path: string
        """
#        print >> sys.stderr, '*** Load_Dir', path

        for name in self.__Find_Modules(path):
            self.Load_Module(name, [path])


    def Load_Module(self, name, path='.'):
        """Load a named module found in a given path.

        @param name: name of the module to load from a path
        @type name: string
        @param path: path or group of paths where to search the module to load
        @type path: string or iterable of strings
        """
#        print >> sys.stderr, '*** Load_Module', name, path

        if isinstance(path, basestring):
            path = [path]

        # Load module
        (file, pathname, description) = imp.find_module(name, path)
        module = imp.load_module(name, file, pathname, description)

        # Load plugins from modules
        for obj in module.__dict__.values():
            if inspect.isclass(obj) and issubclass(obj, Plugin):
                try:
                    self.Load_Plugin(obj)
                # plugin is not a true Plugin
                except AttributeError:
                    pass


    def Load_Plugin(self, plugin):
        """Load a new plugin if it's a valid one.

        If the plugin has all it's dependencies satisfacted it is loaded and the
        pending ones are checked, else it is added to the pending ones.

        @param plugin: plugin to be loaded
        @type plugin: Plugin class
        """
#        print >> sys.stderr, '*** Load_Plugin', plugin

#        plugin.dependencies = set(plugin.dependencies)
#        plugin.replaces = set(plugin.replaces)

        # Plugin has not dependencies or they are all loaded - load it now
        if plugin.dependencies.issubset(self.__loaded):
            self.__Load_Plugin(plugin)

        # Plugin has some dependencies pending - load it later
        else:
            self.__pending.add(plugin)


    def __Find_Modules(self, path="."):
        """Return names of modules in a directory.

        Returns module names in a list. Filenames that end in ".py" or
        ".pyc" are considered to be modules. The extension is not included
        in the returned list.

        @param path: path of the dir with the modules
        @type path: string
        """
        modules = set()

        for filename in os.listdir(path):
            filename = os.path.splitext(filename)

            if filename[1] in (".py", ".pyc"):
                modules.add(filename[0])

        return list(modules)


    def __Load_Plugin(self, plugin):
        """Private version of Load_Plugin.

        Load effectively the plugin and check if pending ones can be loaded now.

        @param plugin: plugin to be loaded
        @type plugin: Plugin class
        """
#        print >> sys.stderr, '*** __Load_Plugin', plugin

        # Add plugin to loaded ones
        # and remove from pending
        self.__loaded[plugin.__name__] = plugin()
        self.__pending.discard(plugin)

        # Check pendings
        for plugin in self.__pending:
            if plugin.dependencies.issubset(self.__loaded):
                self.__Load_Plugin(plugin)