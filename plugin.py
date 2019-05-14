import os
import wx
import wx.aui
import time
import pcbnew
import textwrap
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
        
        self.module_file = config['artifact']['location']
        self.module_path = os.path.join(self.here_path, self.module_file)
        
        self.module_input = self.board_prefix + '.' + config['module']['input_ext']
        self.module_output = self.board_prefix + '.' + config['module']['output_ext']
        
        self.module_command = [self.java_path, "-jar", self.module_path, "-de", self.module_input, "-s"]
        
        if os.path.isfile(self.module_input):
            os.remove(self.module_input)
        if os.path.isfile(self.module_output):
            os.remove(self.module_output)
        
    # export board.dsn file from pcbnew
    def RunExport(self):
        ok = pcbnew.ExportSpecctraDSN(self.module_input)
        if ok and os.path.isfile(self.module_input):
            return True
        else:
            wx_show_error("""
            Failed to invoke:
            * pcbnew.ExportSpecctraDSN
            """)
            return False

    # auto route by invoking FreeRouting.jar
    def RunRouter(self):
        
        dialog = ProcessDialog(None, """
        Complete or Terminate FreeRouting:
        * to complete, close Java window
        * to terminate, press Terminate here
        """)

        def on_complete():
            wx_safe_invoke(dialog.terminate)

        invoker = ProcessThread(self.module_command, on_complete)
        
        dialog.Show()  # dialog first
        invoker.start()  # run java process
        result = dialog.ShowModal()  # block pcbnew here
        dialog.Destroy()
        
        try:
            if result == dialog.result_button:  # return via terminate button
                invoker.terminate()
                return False
            elif result == dialog.result_terminate:  # return via dialog.terminate()
                if invoker.has_ok():
                    return True
                else:
                    invoker.show_error()
                    return False
            else:
                return False  # should not happen
        finally:
            invoker.join(10)  # prevent thread resource leak

    # import generated board.ses file into pcbnew
    def RunImport(self):
        ok = pcbnew.ImportSpecctraSES(self.module_output)
        if ok and os.path.isfile(self.module_output):
            return True
        else:
            wx_show_error("""
            Failed to invoke:
            * pcbnew.ImportSpecctraSES    
            """)
            return False
        
    # invoke chain of dependent methods
    def RunSteps(self):
        self.prepare()
        if not self.RunExport() :
            return 
        if not self.RunRouter() :
            return
        wx_safe_invoke(self.RunImport)

    # kicad plugin action entry
    def Run(self):
        if has_pcbnew_api():
            self.RunSteps()
        else:
            wx_show_error("""
            Missing required python API:
            * pcbnew.ExportSpecctraDSN
            * pcbnew.ImportSpecctraSES
            ---
            Try development nightly build:
            * http://kicad-pcb.org/download/
            """)


# provision gui-thread-safe execution context
# https://git.launchpad.net/kicad/tree/pcbnew/python/kicad_pyshell/__init__.py#n89
if 'phoenix' in wx.PlatformInfo:
    if not wx.GetApp():
        theApp = wx.App()
    else:
        theApp = wx.GetApp()


# run functon inside gui-thread-safe context, requires wx.App on phoenix
def wx_safe_invoke(function, *args, **kwargs):
    wx.CallAfter(function, *args, **kwargs)


# verify required pcbnew api is present
def has_pcbnew_api():
    return hasattr(pcbnew, 'ExportSpecctraDSN') and hasattr(pcbnew, 'ImportSpecctraSES')


# message dialog style
wx_caption = "KiCad FreeRouting Plugin"


# display error text to the user
def wx_show_error(text):
    message = textwrap.dedent(text)
    style = wx.OK | wx.ICON_ERROR
    dialog = wx.MessageDialog(None, message=message, caption=wx_caption, style=style)
    dialog.ShowModal()
    dialog.Destroy()


# prompt user to cancel pending action; allow to cancel programmatically
class ProcessDialog (wx.Dialog):

    def __init__(self, parent, text):
        
        message = textwrap.dedent(text)
        
        self.result_button = wx.NewId()
        self.result_terminate = wx.NewId()
        
        wx.Dialog.__init__ (self, parent, id=wx.ID_ANY, title=wx_caption, pos=wx.DefaultPosition, size=wx.Size(-1, -1), style=wx.CAPTION)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text = wx.StaticText(self, wx.ID_ANY, message, wx.DefaultPosition, wx.DefaultSize, 0)
        self.text.Wrap(-1)
        sizer.Add(self.text, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

        self.line = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        sizer.Add(self.line, 0, wx.EXPAND | wx.ALL, 5)
        
        self.bttn = wx.Button(self, wx.ID_ANY, "Terminate", wx.DefaultPosition, wx.DefaultSize, 0)
        self.bttn.SetDefault()
        sizer.Add(self.bttn, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        sizer.Fit(self)

        self.Centre(wx.BOTH)

        self.bttn.Bind(wx.EVT_BUTTON, self.bttn_on_click)

    def __del__(self):
        pass

    def bttn_on_click(self, event):
        self.EndModal(self.result_button)
    
    def terminate(self):
        self.EndModal(self.result_terminate)


# cancelable external process invoker with completion notification
class ProcessThread(threading.Thread):

    def __init__(self, command, on_complete=None):
        self.command = command
        self.on_complete = on_complete
        threading.Thread.__init__(self)
        self.setDaemon(True)

    # thread runner
    def run(self):
        try:
            self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.stdout, self.stderr = self.process.communicate()
        except Exception as error:
            self.error = error
        finally:
            if self.on_complete is not None:
                self.on_complete()

    def has_ok(self):
        return self.has_process() and self.process.returncode == 0

    def has_code(self):
        return self.has_process() and self.process.returncode != 0
            
    def has_error(self):
        return hasattr(self, "error")

    def has_process(self):
        return hasattr(self, "process")
    
    def terminate(self):
        if self.has_process():
            self.process.kill()
        else:
            pass
    
    def show_error(self):
        command = " ".join(self.command)
        if self.has_error() :
            wx_show_error("""
            Process failure:
            ---
            command:
            %s
            ---
            error:
            %s""" % (command, str(self.error)))
        elif self.has_code():
            wx_show_error("""
            Program failure:
            ---
            command:
            %s
            ---
            exit code: %d
            --- stdout ---
            %s
            --- stderr  ---
            %s
            """ % (command, self.process.returncode, self.stdout, self.stderr))
        else:
            pass


# register plugin with kicad backend
FreeRoutingPlugin().register()
