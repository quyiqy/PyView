import wx

try:
    from wx.lib.pubsub import Publisher as pub
except ImportError:
    from wx.lib.pubsub import pub

import matplotlib
matplotlib.use('WXAgg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar

import os, sys, importlib
import numpy as np
import pylab


class Button(wx.Button):
    """Extension of the Button Widget.
    Bind to function 'func' and run every time the button is pushed."""
    def __init__(self, func_name, label=''):
        self.func_name = func_name
        self.label = label
        self.name = ('button_'+self.label).replace(' ', '_')
        self.label_name = ('label_'+self.label).replace(' ', '_')

    def _inherit(self, parent):
        wx.Button.__init__(self, parent, label=self.label)

    def _bind(self, controller):
        self.Bind( wx.EVT_BUTTON, lambda event, obj=obj: controller.on_button(event, obj) )

    def _update(self, model):
        pass



class ComboBox(wx.ComboBox):
    """Extension of the ComboBox Widget.
    Bind to 'var' and update every time new option selected."""
    def __init__(self, var_name, item_list, label=''):
        self.var_name = var_name
        self.item_list = item_list
        self.label = label
        self.name = ('combo_'+self.label).replace(' ', '_')
        self.label_name = ('label_'+self.label).replace(' ', '_')

    def _inherit(self, parent):
        wx.ComboBox.__init__(self, parent, style=wx.CB_READONLY)

    def _bind(self, controller):
        self.Bind( wx.EVT_COMBOBOX, lambda event, obj=obj: self.on_combo(event, obj) )

    def _update(self, model):
        self.SetValue( str( getattr(model, self.var_name) ) )


class TextCtrl(wx.TextCtrl):
    """Extension of the TextCtrl.
    Bind to variable 'var' and update every time new value entered."""
    def __init__(self, var_name, label=''):
        self.var_name = var_name
        self.label = label
        self.name = ('textctrl_'+self.label).replace(' ', '_')
        self.label_name = ('label_'+self.label).replace(' ', '_')
       
    def _inherit(self, parent):
        wx.TextCtrl.__init__(self, parent, value='', style=wx.TE_PROCESS_ENTER)

    def _bind(self, controller):
        self.Bind( wx.EVT_TEXT, lambda event, obj=obj: self.on_textctrl(event, obj) )
        self.Bind( wx.EVT_TEXT_ENTER, lambda event, obj=obj: self.on_textctrl(event, obj) )

    def _update(self, model):
        self.SetValue( str( getattr(model, self.var_name) ) )



class Plot(object):
    def __init__(self, x_var='', y_var='', plot_type='plot', axes_params=None, dimensions=(6.0,5.0), dpi=100 ):
        """ Self updating plot """
        self.plot_type = plot_type
        self.name = 'plot_'+x_var+'_'+y_var
        self.x_var = x_var
        self.y_var = y_var

        self.fig = Figure(dimensions, dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        if axes_params is None:
            axes_params = dict(title='Awesome graph',
                               xlabel='X',
                               ylabel='Y')



        # self.canvas.mpl_connect('pick_event', self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        # pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        # pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference 
        # to the plotted line series
        #
        self.plot_data = getattr(self.axes, plot_type)(np.array([]), 'yo-')[0]

        # anecdote: axes.grid assumes b=True if any other flag is
        # given even if b is set to False.
        # so just passing the flag into the first statement won't
        # work.
        #
        if 'log' in self.plot_type:
            self.axes.yaxis.grid(b=True, which='minor', color=(.2,.2,.2), linestyle=':')
            self.axes.grid(b=True, which='major', color='gray', linestyle=':')
            self.axes.minorticks_on()
        else:
            self.axes.grid(b=True, which='major', color='gray')
        pylab.setp(self.axes, axis_bgcolor=[.05,.05,.05])

        # self.axes.grid(True, color='gray')
        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly 
        # iterate, and setp already handles this.
        #  
        pylab.setp(self.axes.get_xticklabels(), visible=True)
        pylab.setp(self.axes, **axes_params)
        # pylab.tight_layout()

    def _inherit(self, parent):
        self.parent = parent
        self.canvas = FigCanvas(self.parent, -1, self.fig)
        # self.toolbar = NavigationToolbar(self.canvas)

    def _bind(self, controller):
        pass

    def _update(self, model):
        self.draw( getattr(model, self.x_var), getattr(model, self.y_var))

    def draw(self, x, y):
        """ Redraws the plot
        """
        if x and y:
            if 'log' in self.plot_type:
                try:
                    ymin = round(min(y[y>0]), 0) - 1
                except ValueError:
                    ymin = 1
            else:
                ymin = round(min(y), 0) - 1

            ymax = round(max(y), 0) + 1
            xmin = round(min(x), 0) - 1
            xmax = round(max(x), 0) + 1


            self.axes.set_xbound(lower=xmin, upper=xmax)
            self.axes.set_ybound(lower=ymin, upper=ymax)
            
            self.plot_data.set_xdata(x)
            self.plot_data.set_ydata(y)
            
            try:
                self.canvas.draw()
            except ValueError:
                print 'Woops!\nSome drawing SNAFU happened.\n'




class View(wx.Frame):
    """An object to quickly construct a GUI view from a list of pyview objects"""
    def __init__(self, obj_list, title='Awesome Program'):
        self.app = wx.App(False)
        wx.Frame.__init__(self, None, -1, title)
        self.obj_list = np.array(obj_list)
        self.__create_main_panel()

    def __create_main_panel(self):
        self.panel = wx.Panel(self)

        self.buttons = []
        self.textctrls = []
        self.combos = []
        self.plots = []

        ### Create the elements ###

        for row in self.obj_list:
            for obj in row:
                obj._inherit(self.panel)
                setattr(self, obj.name, obj)

                if isinstance(obj, TextCtrl):
                    setattr(self, obj.label_name, wx.StaticText(self.panel, label=obj.label))
                    self.textctrls.append(obj)

                if isinstance(obj, ComboBox):
                    setattr(self, obj.label_name, wx.StaticText(self.panel, label=obj.label))
                    getattr(self, obj.name).AppendItems(obj.item_list)
                    self.combos.append(obj)

                if isinstance(obj, Button):
                    self.buttons.append(obj)

                if isinstance(obj, Plot):
                    self.plots.append(obj)

        
        ###### Arrange the elements #######
        
        #Add(parent, porportion, flags=...) 
        std_flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        
        for i, row in enumerate(self.obj_list):
            row_name = 'hbox_%d' % i
            setattr(self, row_name, wx.BoxSizer(wx.HORIZONTAL))

            for obj in row:
                if isinstance(obj, TextCtrl):
                    getattr(self, row_name).Add(getattr(self, obj.label_name), border=5, flag=std_flag)
                    getattr(self, row_name).Add(getattr(self, obj.name), border=5, flag=std_flag)

                if isinstance(obj, ComboBox):
                    getattr(self, row_name).Add(getattr(self, obj.label_name), border=5, flag=std_flag)
                    getattr(self, row_name).Add(getattr(self, obj.name), border=5, flag=std_flag)

                if isinstance(obj, Button):
                    getattr(self, row_name).Add(getattr(self, obj.name), border=5, flag=std_flag)

                if isinstance(obj, Plot):
                    # hbox_name = 'hbox_'+obj.name
                    # vbox_name = 'vbox_'+obj.name
                    # setattr(self, hbox_name, wx.BoxSizer(wx.HORIZONTAL))
                    # setattr(self, vbox_name, wx.BoxSizer(wx.VERTICAL))

                    getattr(self, row_name).Add(getattr(self, obj.name).canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
                    # getattr(self, vbox_name).Add(getattr(self, obj.name).toolbar, 1, flag=wx.CENTER | wx.EXPAND)
                    # getattr(self, hbox_name).Add(getattr(self, vbox_name))
                    # getattr(self, row_name).Add(getattr(self, hbox_name))


            self.vbox.Add(getattr(self, row_name), 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)

        # Make it Fit
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
    


    
class Controller(object):
    """An object made by run() that links the view to the methods and attributes 
    of the model"""
    def __init__(self, model, view):
        #Create objects
        self.model = model
        self.view = view
        self.worker = None

        pub.subscribe(self.update_view, 'UpdateView')
        pub.sendMessage('UpdateView')

        ### BINDINGS ###

        # Button Bindings
        for obj in self.view.buttons:
            getattr(self.view, obj.name).Bind( wx.EVT_BUTTON, lambda event, obj=obj: self.on_button(event, obj) )

        # Combobox Bindings
        for obj in self.view.combos:
            getattr(self.view, obj.name).Bind( wx.EVT_COMBOBOX, lambda event, obj=obj: self.on_combo(event, obj) )

        # Textctrl Bindings
        for obj in self.view.textctrls:
            getattr(self.view, obj.name).Bind( wx.EVT_TEXT, lambda event, obj=obj: self.on_textctrl(event, obj) )
            getattr(self.view, obj.name).Bind( wx.EVT_TEXT_ENTER, lambda event, obj=obj: self.on_textctrl(event, obj) )


        ### RUN ###

        # Display the main frame
        self.view.Show()
        print 'Program Finished Loading!'

    def on_button(self, event, obj):
        getattr(self.model, obj.func_name)()

    def on_combo(self, event, obj):
        setattr(self.model, obj.var_name, obj.GetValue())

    def on_textctrl(self, event, obj):
        setattr(self.model, obj.var_name, obj.GetValue())

    def update_view(self):
        # Combobox Bindings
        for obj in self.view.combos:
            getattr(self.view, obj.name).SetValue(str( getattr(self.model, obj.var_name) ))

        # Textctrl Bindings
        for obj in self.view.textctrls:
            # print obj.var_name, getattr(self.model, obj.var_name)
            getattr(self.view, obj.name).SetValue(str( getattr(self.model, obj.var_name) ))

        for obj in self.view.plots:
            obj.draw(getattr(self.model, obj.x_var), getattr(self.model, obj.y_var))




def run(model, view):
    '''Run the pyview program'''

    #Check if model is an instantiation of the class
    try:
        if not isinstance(model, model):
            model = model()
    except TypeError:
        print '\nModel must be a class instance\n'
        raise

    controller = Controller(model, view)
    view.app.MainLoop()


def update():
    pub.sendMessage('UpdateView')

