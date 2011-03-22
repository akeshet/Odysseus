#!/usr/bin/python

"""
The basic interface and implementation for a plugin system.

Also define the basic mechanism to add functionalities to the base
PluginManager. A few *principles* to follow in this case:

If the new functionalities do not overlap the ones already
implemented, then they must be implemented as a Decorator class of the
base plugin. This should be done by inheriting the
``PluginManagerDecorator``.

If this previous way is not possible, then the functionalities should
be added as a subclass of ``PluginManager``.

The first method is highly prefered since it makes it possible to have
a more flexible design where one can pick several functionalities and
litterally *add* them to get an object corresponding to one's precise
needs.
"""

import sys, os
import logging
import ConfigParser
import types

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

from mplwidgets import BlankCanvas


# A forbiden string that can later be used to describe lists of
# plugins for instance (see ``ConfigurablePluginManager``)
PLUGIN_NAME_FORBIDEN_STRING=";;"

# prints all logged messages with level debug or higher
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='pluginlogger.log',
                    filemode='w')


class IPlugin(object):
    """Defines the basic interfaces for a plugin.

    These interfaces are inherited by the *core* class of a plugin.
    The *core* class of a plugin is then the one that will be notified the
    activation/deactivation of a plugin via the ``activate/deactivate``
    methods.

    For simple (near trivial) plugin systems, one can directly use the
    following interfaces.

    When designing a non-trivial plugin system, one should create new
    plugin interfaces that inherit the following interfaces.
    """

    def __init__(self):
        """
        Set the basic variables.
        """
        self.is_activated = False

    def activate(self):
        """
        Called at plugin activation.
        """
        self.is_activated = True

    def deactivate(self):
        """
        Called when the plugin is disabled.
        """
        self.is_activated = False


class DialogPlugin(IPlugin):
    """Defines the interface for a plugin that pops up a dialog with an image"""

    def create_window(self, rawframes, img, roi, name, path):
        """Create dialog and image inside it

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        """

        self.window = PluginDialog(name)
        # make ax more easily accessible
        self.ax = self.window.ax
        # call the user-implemented functionality
        self.main(img[roi])
        # show the window
        self.window.show()

        return self.window


    def main(self, img):
        """This method is to be implemented by plugins, they do the work"""
        pass
    
class VerboseDialogPlugin(IPlugin):
    """Defines the interface for a plugin that pops up a dialog with an image"""

    def create_window(self, rawframes, img, roi, name, path):
        """Create dialog and image inside it

        **Inputs**

          * img: 2d-array, containing the image data
          * roi: tuple of slices, contains two slice objects, one for each
                 image axis. The tuple can be used as a 2D slice object.
          * name: string, the name of the plugin

        """

        self.window = PluginDialog(name)
        # make ax more easily accessible
        self.ax = self.window.ax
        # call the user-implemented functionality
        self.main(rawframes, img, roi, name, path)
        # show the window
        self.window.show()

        return self.window


    def main(self, rawframes, img, roi, name, path):
        """This method is to be implemented by plugins, they do the work"""
        pass


class PluginDialog(QDialog):
    """Handles the window that plugins can pop up"""

    def __init__(self, name, parent=None):
        super(PluginDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(name)

        layout = QVBoxLayout()
        self.fig = BlankCanvas()
        self.ax = self.fig.ax

        self.toolbar = NavigationToolbar2QT(self.fig, self)
        layout.addWidget(self.fig)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)


class PluginInfo(object):
    """Gather some info about a plugin

    This includes name, author,description, etc.
    """

    def __init__(self, plugin_name, plugin_path):
        """Set the name and path of the plugin

        The default values for other useful variables are set as well.

        .. warning:: The ``path`` attribute is the full path to the
            plugin if it is organised as a directory or the full path
            to a file without the ``.py`` extension if the plugin is
            defined by a simple file. In the later case, the actual
            plugin is reached via ``plugin_info.path+'.py'``.

        """
        self.name = plugin_name
        self.path = plugin_path
        self.author = "Unknown"
        self.version = "?.?"
        self.website = "None"
        self.copyright = "Unknown"
        self.description = ""
        self.plugin_object = None
        self.category = None

    def _getIsActivated(self):
        """Return the activated state of the plugin object.

        Makes it possible to define a property.
        """

        return self.plugin_object.is_activated
    is_activated = property(fget=_getIsActivated)

    def setVersion(self, vstring):
        """Set the version of the plugin.

        Used by subclasses to provide different handling of the
        version number.
        """
        self.version = vstring


class PluginManager(object):
    """Manage several plugins by ordering them in several categories.

    The mechanism for searching and loading the plugins is already
    implemented in this class so that it can be used directly (hence
    it can be considered as a bit more than a mere interface)

    The file describing a plugin should be written in the sytax
    compatible with Python's ConfigParser module as in the following
    example::

      [Core Information]
      Name= My plugin Name
      Module=the_name_of_the_plugin_to_load_with_no_py_ending

      [Documentation]
      Description=What my plugin broadly does
      Author= My very own name
      Website= My very own website
      Version=the_version_number_of_the_plugin
    """

    def __init__(self, categories_filter={"Default":IPlugin}, \
                 directories_list=None, plugin_info_ext="yapsy-plugin"):
        """Initialize PluginManager.

        Initialize the mapping of the categories and set the list of
        directories where plugins may be. This can also be set by
        direct call the methods:

        - ``setCategoriesFilter`` for ``categories_filter``
        - ``setPluginPlaces`` for ``directories_list``
        - ``setPluginInfoExtension`` for ``plugin_info_ext``

        You may look at these function's documentation for the meaning
        of each corresponding arguments.
        """
        self.setPluginInfoClass(PluginInfo)
        self.setCategoriesFilter(categories_filter)
        self.setPluginPlaces(directories_list)
        self.setPluginInfoExtension(plugin_info_ext)

    def setCategoriesFilter(self, categories_filter):
        """Set the categories of plugins to be looked for.

        The ``categories_filter`` first defines the various categories
        in which the plugins will be stored via its keys and it also
        defines the interface tha has to be inherited by the actual
        plugin class belonging to each category.
        """
        self.categories_interfaces = categories_filter.copy()
        # prepare the mapping from categories to plugin lists
        self.category_mapping = {}
        # also maps the plugin info files (useful to avoid loading
        # twice the same plugin...)
        self._category_file_mapping = {}
        for categ in categories_filter.keys():
            self.category_mapping[categ] = []
            self._category_file_mapping[categ] = []


    def setPluginInfoClass(self,picls):
        """Set the class that holds PluginInfo.

        The class should inherit from ``PluginInfo``.
        """
        self._plugin_info_cls = picls

    def getPluginInfoClass(self):
        """Get the class that holds PluginInfo.

        The class should inherit from ``PluginInfo``.
        """
        return self._plugin_info_cls

    def setPluginPlaces(self, directories_list):
        """Set the list of directories where to look for plugin places."""
        if directories_list is None:
            directories_list = [os.path.dirname(__file__)]
        self.plugins_places = directories_list

    def setPluginInfoExtension(self,plugin_info_ext):
        """Set the extension that identifies a plugin info file.

        The ``plugin_info_ext`` is the extension that will have the
        informative files describing the plugins and that are used to
        actually detect the presence of a plugin (see
        ``collectPlugins``).
        """
        self.plugin_info_ext = plugin_info_ext

    def getCategories(self):
        """Return the list of all categories."""
        return self.category_mapping.keys()

    def getPluginsOfCategory(self,category_name):
        """Return the list of all plugins belonging to a category."""
        return self.category_mapping[category_name]

    def _gatherCorePluginInfo(self, directory, filename):
        """Gather the core information about a plugin.

        The plugin is described by it's info file (found at
        'directory/filename'), the core information is the plugin's
        name and module to be loaded.

        Return an instance of ``self.plugin_info_cls`` and the
        config_parser used to gather the core data *in a tuple*, if the
        required info could be localised, else return ``(None,None)``.

        .. note:: This is supposed to be used internally by subclasses
            and decorators.
        """
        # now we can consider the file as a serious candidate
        candidate_infofile = os.path.join(directory,filename)
        # parse the information file to get info about the plugin
        config_parser = ConfigParser.SafeConfigParser()
        try:
            config_parser.read(candidate_infofile)
        except:
            logging.debug("Could not parse the plugin file %s" \
                          %candidate_infofile)
            return (None, None)
        # check if the basic info is available
        if not config_parser.has_section("Core"):
            logging.debug("Plugin info file has no 'Core' section (in %s)" \
                          %candidate_infofile)
            return (None, None)
        if not config_parser.has_option("Core","Name") or not \
           config_parser.has_option("Core","Module"):
            logging.debug('Plugin info file has no "Name" or "Module" section (in %s)'\
                          %candidate_infofile)
            return (None, None)
        # check that the given name is valid
        name = config_parser.get("Core", "Name")
        name = name.strip()
        if PLUGIN_NAME_FORBIDEN_STRING in name:
            logging.debug("Plugin name contains forbiden character: %s (in %s)"\
                          %(PLUGIN_NAME_FORBIDEN_STRING, candidate_infofile))
            return (None, None)
        # start collecting essential info
        plugin_info = self._plugin_info_cls(name,
                                            os.path.join(directory, \
                                                         config_parser.get("Core", "Module")))
        return (plugin_info,config_parser)

    def gatherBasicPluginInfo(self, directory,filename):
        """Gather some basic documentation about the plugin.

        This info is described by the plugin's info file
        (found at 'directory/filename').

        Return an instance of ``self.plugin_info_cls`` gathering the
        required informations.

        See also ``self._gatherCorePluginInfo``
        """
        plugin_info,config_parser = self._gatherCorePluginInfo(directory, filename)
        if plugin_info is None:
            return None
        # collect additional (but usually quite usefull) information
        if config_parser.has_section("Documentation"):
            if config_parser.has_option("Documentation","Author"):
                plugin_info.author = config_parser.get("Documentation", "Author")
            if config_parser.has_option("Documentation","Version"):
                plugin_info.setVersion(config_parser.get("Documentation", "Version"))
            if config_parser.has_option("Documentation","Website"):
                plugin_info.website = config_parser.get("Documentation", "Website")
            if config_parser.has_option("Documentation","Copyright"):
                plugin_info.copyright = config_parser.get("Documentation", "Copyright")
            if config_parser.has_option("Documentation","Description"):
                plugin_info.description = config_parser.get("Documentation", "Description")
        return plugin_info

    def locatePlugins(self):
        """Walk through the plugins' places and look for plugins.

        Return the number of plugins found.
        """
        #print "%s.locatePlugins" % self.__class__
        self._candidates = []
        for directory in map(os.path.abspath,self.plugins_places):
            # first of all, is it a directory :)
            if not os.path.isdir(directory):
                logging.debug("%s skips %s (not a directory)" \
                              %(self.__class__.__name__,directory))
                continue
            # iteratively walks through the directory
            logging.debug("%s walks into directory: %s" \
                          %(self.__class__.__name__,directory))
            for item in os.walk(directory):
                dirpath = item[0]
                for filename in item[2]:
                    # eliminate the obvious non plugin files
                    if not filename.endswith(".%s" % self.plugin_info_ext):
                        continue
                    candidate_infofile = os.path.join(dirpath,filename)
                    logging.debug('%s found a candidate: \
                                  %s' % (self.__class__.__name__, \
                                         candidate_infofile))
                    plugin_info = self.gatherBasicPluginInfo(dirpath,filename)
                    if plugin_info is None:
                        logging.debug("""Candidate rejected:
                                      %s""" % candidate_infofile)
                        continue
                    # now determine the path of the file to execute,
                    # depending on wether the path indicated is a
                    # directory or a file
                    if os.path.isdir(plugin_info.path):
                        candidate_filepath = os.path.join(plugin_info.path, \
                                                          "__init__")
                    elif os.path.isfile(plugin_info.path+".py"):
                        candidate_filepath = plugin_info.path
                    else:
                        continue
                    self._candidates.append((candidate_infofile, \
                                             candidate_filepath, plugin_info))
        return len(self._candidates)

    def loadPlugins(self, callback=None):
        """Load the candidate plugins.

	These have been identified through a previous call to locatePlugins.
	For each plugin candidate look for its category, load it and store it
	in the appropriate slot of the ``category_mapping``.

	If a callback function is specified, call it before every load
	attempt.  The ``plugin_info`` instance is passed as an argument to
	the callback.
	"""
        if not hasattr(self, '_candidates'):
            raise ValueError("locatePlugins must be called before loadPlugins")

        for candidate_infofile, candidate_filepath, plugin_info in self._candidates:
            # if a callback exists, call it before attempting to load
            # the plugin so that a message can be displayed to the
            # user
            if callback is not None:
                callback(plugin_info)
            # now execute the file and get its content into a
            # specific dictionnary
            candidate_globals = {"__file__":candidate_filepath+".py"}
            if "__init__" in  os.path.basename(candidate_filepath):
                sys.path.append(plugin_info.path)
            try:
                execfile(candidate_filepath+".py",candidate_globals)
            except Exception,e:
                logging.debug("Unable to execute the code in plugin: %s" \
                              %candidate_filepath)
                logging.debug("\t The following problem occured: %s %s " \
                              %(os.linesep, e))
                if "__init__" in  os.path.basename(candidate_filepath):
                    sys.path.remove(plugin_info.path)
                continue

            if "__init__" in  os.path.basename(candidate_filepath):
                sys.path.remove(plugin_info.path)
            # now try to find and initialise the first subclass of the correct
            #plugin interface
            for element in candidate_globals.values():
                current_category = None
                for category_name in self.categories_interfaces.keys():
                    try:
                        is_correct_subclass = issubclass(element, \
                                                         self.categories_interfaces[category_name])
                    except:
                        continue
                    if is_correct_subclass:
                        if element is not self.categories_interfaces[category_name]:
                            current_category = category_name
                            break
                if current_category is not None:
                    if not (candidate_infofile in self._category_file_mapping[current_category]):
                        # we found a new plugin: initialise it and search for the next one
                        plugin_info.plugin_object = element()
                        plugin_info.category = current_category
                        self.category_mapping[current_category].append(plugin_info)
                        self._category_file_mapping[current_category].append(candidate_infofile)
                        current_category = None
                    break

        # Remove candidates list since we don't need them any more and
        # don't need to take up the space
        delattr(self, '_candidates')

    def collectPlugins(self):
        """Walk through the plugins' places and look for plugins.

	Then for each plugin candidate look for its category, load it and
	stores it in the appropriate slot of the category_mapping.
	"""
        self.locatePlugins()
        self.loadPlugins()


    def getPluginByName(self,name,category="Default"):
        """Get the plugin corresponding to a given category and name"""
        if self.category_mapping.has_key(category):
            for item in self.category_mapping[category]:
                if item.name == name:
                    return item
        return None

    def activatePluginByName(self,name,category="Default"):
        """Activate a plugin corresponding to a given category + name."""
        pta_item = self.getPluginByName(name,category)
        if pta_item is not None:
            plugin_to_activate = pta_item.plugin_object
            if plugin_to_activate is not None:
                logging.debug("Activating plugin: %s.%s"% (category,name))
                plugin_to_activate.activate()
                return plugin_to_activate
        return None


    def deactivatePluginByName(self,name,category="Default"):
        """Deactivate a plugin corresponding to a given category + name."""
        if self.category_mapping.has_key(category):
            plugin_to_deactivate = None
            for item in self.category_mapping[category]:
                if item.name == name:
                    plugin_to_deactivate = item.plugin_object
                    break
            if plugin_to_deactivate is not None:
                logging.debug("Deactivating plugin: %s.%s"% (category,name))
                plugin_to_deactivate.deactivate()
                return plugin_to_deactivate
        return None


class PluginManagerDecorator(object):
    """Make it possible to add several responsibilities to a plugin manager.

    This can de done in a more flexible way than by mere
    subclassing. This is an implementation of the Decorator Design Patterns.

    There is also an additional mechanism that allows for the
    automatic creation of the object to be decorated when this object
    is an instance of PluginManager (and not an instance of its
    subclasses). This way we can keep the plugin managers creation
    simple when the user don't want to mix a lot of 'enhancements' on
    the base class.
    """

    def __init__(self,decorated_object=None,
                 # The following args will only be used if we need to
                 # create a default PluginManager
                 categories_filter={"Default":IPlugin},
                 directories_list=[os.path.dirname(__file__)],
                 plugin_info_ext="yapsy-plugin"):
        """Mimics the PluginManager's __init__ method and wraps an
	instance of this class into this decorator class.

	  - *If the decorated_object is not specified*, then we use the
	    PluginManager class to create the 'base' manager, and to do
	    so we will use the arguments: ``categories_filter``,
	    ``directories_list``, and ``plugin_info_ext`` or their
	    default value if they are not given.

	  - *If the decorated object is given*, these last arguments are
	    simply **ignored** !

	All classes (and especially subclasses of this one) that want
	to be a decorator must accept the decorated manager as an
	object passed to the init function under the exact keyword
	``decorated_object``.
	"""

        if decorated_object is None:
            logging.debug("Creating a default PluginManager instance to be decorated.")
            decorated_object = PluginManager(categories_filter,
                                             directories_list,
                                             plugin_info_ext)
        self._component = decorated_object

    def __getattr__(self,name):
        """Decorator trick copied from:
	http://www.pasteur.fr/formation/infobio/python/ch18s06.html
	"""
        return getattr(self._component,name)


    def collectPlugins(self):
        """This function will usually be a shortcut.

	Successively calls to ``self.locatePlugins`` and then
	``self.loadPlugins`` can be made, which are
	very likely to be redefined in each new decorator.

	So in order for this to keep on being a "shortcut" and not a
	real pain, I'm redefining it here.
	"""
        self.locatePlugins()
        self.loadPlugins()
