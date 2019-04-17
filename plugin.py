import os
import wx
import wx.aui
import time
import pcbnew
import threading
import subprocess
import configparser

#
# FreeRouting round trip invocation:
# * export board.dsn file from pcbnew
# * auto route by invoking FreeRouting.jar
# * import generated board.ses file into pcbnew
#
class FreeRoutingPlugin(pcbnew.ActionPlugin):
    
    # init in place of constructor
    def defaults(self):
        self.here_path = os.path.dirname(__file__)
        self.name = "Invoke FreeRouting"
        self.category = "PCB auto routing"
        self.description = "Invoke FreeRouting for PCB auto routing"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(self.here_path, 'icon.png') 
        
    # setup execution context
    def prepare(self):
        
        self.board = pcbnew.GetBoard()
        self.path_tuple = os.path.splitext(self.board.GetFileName())
        self.board_prefix = self.path_tuple[0]
        
        config = configparser.ConfigParser()
        config_path = os.path.join(self.here_path, 'plugin.ini')
        config.read(config_path)

        self.java_path = config['java']['path']
        self.module_timeout = float(config['module']['timeout'])
        
        self.module_file = config['artifact']['location']
        self.module_path = os.path.join(self.here_path, self.module_file)
        
        self.module_input = self.board_prefix + '.dsn'
        self.module_output = self.board_prefix + '.ses'
        
        if os.path.isfile(self.module_input):
            os.remove(self.module_input)
        if os.path.isfile(self.module_output):
            os.remove(self.module_output)

    # run inside gui-thread-safe context
    def invoke(self, runner):
        wx.CallAfter(runner)

    def RunExport(self):
        pcbnew.ExportSpecctraDSN(self.module_input)
        
    def RunRouter(self):
        command = [self.java_path, "-jar", self.module_path, "-de", self.module_input, "-s"]
        process = subprocess.Popen(command)
        process.wait(self.module_timeout)

    def RunImport(self):
        pcbnew.ImportSpecctraSES(self.module_output)

    def Run(self):
        self.prepare()
        self.invoke(self.RunExport)
        self.invoke(self.RunRouter)
        self.invoke(self.RunImport)


# provision gui-thread-safe execution context
if not wx.GetApp():
    theApp = wx.App()
else:
    theApp = wx.GetApp()

# register plugin with kicad backend
FreeRoutingPlugin().register()
