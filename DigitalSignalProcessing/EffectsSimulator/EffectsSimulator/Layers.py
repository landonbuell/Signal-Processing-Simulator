"""
Landon Buell
EffectsSimulator
LayersGeneric
5 Feb 2020
"""

            #### IMPORTS ####

import os
import sys

import numpy as np
import scipy.signal as signal
import scipy.fftpack as fftpack

import AudioTools

            #### LAYER DEFINITIONS ####

class AbstractLayer :
    """
    AbstractLayer Type
        Abstract Base Type for all Layer Classes
        Acts as node in double linked list
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    Abstract class - Make no instance
    """

    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for AbstractLayer Parent Class """
        self._name = name                       # name of this layer instance
        self._type = "AbstractParentLayer"      # type of this layer instance
        self._sampleRate = sampleRate           # sample rate of this layer
        self._chainIndex = None                 # index in layer chain
        self.CoupleToNext(next)                 # connect to next Layer
        self.CoupleToPrev(prev)                 # connect to Previous Layer
        self._shapeInput = inputShape           # input signal Shape
        self._shapeOutput = inputShape          # output signal shape
        self._initialized = False               # T/F is chain has been initialzed
        self._signal = np.array([])             # output Signal
                             
    # Methods

    def Initialize (self,inputShape=None,**kwargs):
        """ Initialize this layer for usage in chain """
        if inputShape:          # given input Shape
            self.SetInputShape(inputShape)
            self.SetOutputShape(inputShape)
        elif self._shapeInput:  # input shape already defined
            self.SetOutputShape(self.GetInputShape)
        else:
            self.SetInputShape((1,1))
            self.SetOutputShape((1,1))
        self._signal = np.empty(self._shapeOutput)
        return self

    def Call (self,X):
        """ Call this Layer with inputs X """
        if self._initialized == False:      # Not Initialized
            errMsg = self.__str__() + " has not been initialized\n\t" + "Call <Layer>.Initialize() before use"
            raise NotImplementedError(errMsg)
        if (X.shape == self.GetInputShape):  # same shape
            np.copyto(self._signal,X)
        else:                               # different shapes
            self._signal = np.copy(X);
        return X

    @property
    def Next(self):
        """ Return the next Layer in chain """
        return self._next

    @property
    def Prev(self):
        """ Return the previous Layer in chain """
        return self._prev

    def CoupleToNext(self,otherLayer):
        """ Couple to next Layer """
        if otherLayer:
            self._next = otherLayer
            otherLayer._prev = self
        else:
            self._next = None
        return self

    def CoupleToPrev(self,otherLayer):
        """ Couple to Previous Layer """
        if otherLayer:
            self._prev = otherLayer
            otherLayer._next = self
        else:
            self._prev = None
        return self

    @property
    def GetSampleRate(self):
        """ Get the Sample Rate for this Layer """
        return self._sampleRate

    def SetSampleRate(self,x):
        """ Set the Samplke Rate for this Layer """
        self._sampleRate = x
        return self

    @property
    def GetIndex(self):
        """ Get this Layer's chain index """
        return self._chainIndex
    
    def SetIndex(self,x):
        """ Set this Layer's chain index """
        self._chainIndex = x
        return self

    @property
    def InputShape(self):
        """ Get the input shape of this layer """
        return self._shapeInput

    def SetInputShape(self,x):
        """ Set the input shape of this layer """
        self._shapeInput = x
        return self

    @property
    def OutputShape(self):
        """ Get The output shape of this layer """
        return self._shapeOutput

    def SetOutputShape(self,x):
        """ Set the output shape of this layer """
        self._shapeOutput = x
        return self

    @property
    def GetSignal(self):
        """ Return the Output Signal of this Layer """
        return self._signal

    # Magic Methods

    def __str__(self):
        """ string-level representation of this instance """
        return self._type + " - " + self._name

    def __repr__(self):
        """ Programmer-level representation of this instance """
        return self._type + ": \'" + self._name + "\' @ " + str(self._chainIndex)

class IdentityLayer (AbstractLayer):
    """
    IdentityLayer Type - Provides no Transformation of input
        Serves as head/tail nodes of FX chain Graph
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    Return Instantiated identityLayer
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for AbstractLayer Parent Class """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "IdentityLayer"

class CustomCallable (AbstractLayer):
    """
    CustomCallable Type - Returns User defined transformation 
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform    

    _callable (callable) : User-denfined or desired function transformation
    _callArgs (list) : List of arguments to pass to callable function
    --------------------------------
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 callableFunction=None,callableArgs=[]):
        """ Constructor for CustomCallable Class """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "CustomCallable"
        if callableFunction:
            self._callable = callableFunction
        else:
            raise ValueError("Must Provide callable argument for CustomCallable")
        self._callArgs = callableArgs
    
    def Call(self,X):
        """ Call this Layer with inputs X """
        super().Call(X)
        np.copyto(self.signal,self._callable(X,self._callArgs))
        return self._signal

class PlotSignal1D(AbstractLayer):
    """
    CustomCallable Type - Returns User defined transformation 
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform   

    _savePath (str) : Local path where plot of 1D signal is exported to
    _figureName (str) : Name to save local plots
    _showFigure (bool) : If True, figures is displayed to console
    --------------------------------
    """

    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 figurePath=None,figureName=None,show=False):
        """ Constructor for AbstractLayer Parent Class """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "PlotSignal1"

        if figurePath:
            self._figurePath = figurePath           
        else:
            self._figurePath = os.getcwd()
        if figureName:
            self._figureName = figureName
        else:
            self._figureName = "Signal1D"
        self._showFigure = show

    def Call(self,X):
        """ Call current layer with inputs X """
        super().Call(X)
        figureExportPath = os.path.join(self._figurePath,self._figureName)
        cntr = 0
        while True:
            if os.path.isfile(figureExportPath):
                # the file already exists
                figureExportPath += str(cntr)
            else:
                figureExportPath += str(cntr)
        xData = np.arange(X.shape) / self._sampleRate
        AudioTools.Plotting.PlotGeneric(xData,X,
                                        save=figureExportPath,show=self._show)
        return X
    
    @property
    def GetShowStatus(self):
        """ Get if figure is shown to console """
        return self._showFigure

    def SetShowStatus(self,x):
        """ Set if figure is shown to console """
        self._showFigure = x
        return self

class InputLayer (AbstractLayer):
    """
    ModuleAnalysisFrames Type - 
        Deconstruct a 1D time-domain signal into a 2D array of overlapping analysis frames
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    Return instantiated AnalysisFrames Object 
    """

    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for AnalysisFames Instance """
        if not inputShape:
            raise ValueError("input shape must be provdied (cannot be \'None\')")
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "InputLayer"

    # Methods

    def Initialize (self,inputShape=None,**kwargs):
        """ Initialize this layer for usage in chain """
        super().Initialize(inputShape,**kwargs)
        # Initialize input Layer?
        return self

    def Call (self,X):
        """ Call this Layer with inputs X """
        return super().Call(X)
       
class AnalysisFramesConstructor (AbstractLayer):
    """
    AnalysisFramesConstructor Type - 
        Construct 2D array of analysis frames from 1D input waveform
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform   

    _samplesPerFrame (int) : Number of samples used in each analysisFrame
    _percentOverlap (float) : Indicates percentage overlap between adjacent frames [0,1)
    _overlapSamples (int) : Number of samples overlapping
    _maxFrames (int) : Maximum number of analysis frames to use
    _framesInUse (int) : Number of frames used by 
    _padTail (int) : Number of zeros to tail-pad each analysis frame
    _padHead (int) : Number of zeros to head-pad each analysis frame
    --------------------------------
    Return instantiated AnalysisFramesConstructor Object 
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 samplesPerFrame=1024,percentOverlap=0.75,maxFrames=256,tailPad=1024,headPad=0):
        """ Constructor for AnalysisFamesConstructor Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "AnalysisFrameConstructor"
        self._samplesPerFrame = samplesPerFrame
        self._percentOverlap = percentOverlap
        self._overlapSamples = int(samplesPerFrame*(1-percentOverlap))
        self._maxFrames = maxFrames
        self._framesInUse = 0
        self._padTail = tailPad
        self._padHead = headPad
        
    def Initialize (self,inputShape=None,**kwargs):
        """ Initialize this module for usage in chain """
        super().Initialize(inputShape,**kwargs)

        # format output shape
        self._shapeOutput = (self._maxFrames,
                             self._padHead + self._samplesPerFrame + self._padTail)
        self._signal = np.zeros(shape=self._shapeOutput,dtype=np.float32)
        self._framesInUse = 0
        self._initialized = True 
        return self

    def SignalToFrames(self,X):
        """ Convert signal X into analysis Frames """
        frameStartIndex = 0
        for i in range(self._maxFrames):
            frame = X[frameStartIndex:frameStartIndex+self._samplesPerFrame]
            try:
                self._signal[i + self._padHead ,0:self._samplesPerFrame] = frame
            except ValueError:
                self._signal[i + self._padHead ,0:len(frame)] = frame
                break           
            frameStartIndex += self._overlapSamples
            self._framesInUse += 1
        return self

    def Call(self, X):
        """ Call this Module with inputs X """
        X = super().Call(X)
        self.SignalToFrames(X)
        return self._signal

    @property
    def GetDeconstructionParams(self):
        """ Return a List of params to deconstruct Frames into Signal """
        params = [self._samplesPerFrame,self._percentOverlap,self._maxFrames,self._framesInUse,
                  self._padTail,self._padHead]
        return params

class AnalysisFramesDestructor (AbstractLayer):
    """
    AnalysisFramesDestructor Layer Type - 
        Destruct 2D array of analysis frames into 1D input waveform
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform   

    _samplesPerFrame (int) : Number of samples used in each analysisFrame
    _percentOverlap (float) : Indicates percentage overlap between adjacent frames [0,1)
    _overlapSamples (int) : Number of samples overlapping
    _maxFrames (int) : Maximum number of analysis frames to use
    _framesInUse (int) : Number of frames used by 
    _padTail (int) : Number of zeros to tail-pad each analysis frame
    _padHead (int) : Number of zeros to tail-pad each analysis frame   
    --------------------------------
    Return instantiated AnalysisFramesDestructor Object 
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 samplesPerFrame=1024,percentOverlap=0.75,maxFrames=256,tailPad=1024,headPad=0,
                 deconstructParams=None):
        """ Constructor for AnalysisFamesDestructor Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "AnalysisFrameConstructor"
        if deconstructParams:           # Parameters from AnalysisFramesConstructor
            self.SetDeconstructionParams(deconstructParams)
        else:
            self._samplesPerFrame = samplesPerFrame
            self._percentOverlap = percentOverlap
            self._overlapSamples = int(samplesPerFrame*(1-percentOverlap))
            self._maxFrames = maxFrames
            self._padTail = tailPad
            self._padHead = headPad
            self._framesInUse = 0

    def Initialize (self,inputShape=None,**kwargs):
        """ Initialize this module for usage in chain """
        super().Initialize(inputShape,**kwargs)

        # format output shape
        self._shapeOutput = (self._sample_samplesPerFrame * self._framesInUse,)
        self._signal = np.zeros(shape=self._shapeOutput,dtype=np.float32)
        self._framesInUse = 0
        self._initialized = True 
        return self

    def FramesToSignal(self,X):
        """ Convert signal X into analysis Frames """
        frameStartIndex = 0
        for i in range(self._framesInUse):
            frame = X[i,self._padHead:self._padHead + self._samplesPerFrame]
            self._signal[frameStartIndex : frameStartIndex + self._samplesPerFrame] = frame
            frameStartIndex += self._sample_samplesPerFrame
        return self

    def Call(self, X):
        """ Call this Module with inputs X """
        X = super().Call(X)
        self.FramesToSignal(X)
        return self._signal

    def SetDeconstructionParams(self,params):
        """ Return a List of params to deconstruct Frames into Signal """
        self._samplesPerFrame = params[0]
        self._percentOverlap = params[1]
        self._maxFrames = params[2]
        self._frameInUse = params[3]
        self._padTail = params[4]
        self._padHead = params[5]
        self._overlapSamples = int(samplesPerFrame*(1-percentOverlap))
        return self

class ResampleLayer (AbstractLayer):
    """
    Resample Layer -
        Resample layer to 
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    Abstract class - Make no instance
    """
    def __init__(self,name,sampleRateNew,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for ResampleLayer instance """
        super().__init__(name,ssampleRate,inputShape,next,prev)
        self._sampleRateNew = sampleRateNew

class WindowFunction (AbstractLayer):
    """
    WindowFunction Type - 
         Apply a window finction
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    
    _nSamples (int) : Number of samples that the window is applied to
    _padTail (int) : Number of zeros to tail pad the window with
    _padHead (int) : Number of zeros to head pad the window with
    _windowSize (int) : Total window size padding + sampels

    _function (call/arr) : ???
    _window (arr) : Array of window function and padding
    --------------------------------
    Return instantiated AnalysisFrames Object 
    """
    
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 function=None,nSamples=1024,tailPad=1024,headPad=0):
        """ Constructor for AnalysisFames Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "WindowFunctionLayer"
        
        self._nSamples = nSamples
        self._padTail = tailPad
        self._padHead = headPad
        self._windowSize = tailPad + nSamples + headPad

        self._function = function
        self._window = np.zeros(shape=(self._windowSize))

    def Initialize(self,inputShape=None,**kwargs):
        super().Initialize(inputShape,**kwargs)
        self._window = np
        return self

    def Call(self,X):
        """ Call this module with inputs X """
        X = super().Call(X)
        X = np.multiply(X,self._window,out=X)
        return X

class AmplitudeEnvelope(AbstractLayer):
    """

    """
    pass

class DiscreteFourierTransform(AbstractLayer):
    """
    DiscreteFourierTransform - 
        Apply Discrete Fourier Transform to input signal
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for NBandEquilizer Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)

    def Initialize(self,inputShape=None,**kwargs):
        """ Initialize Current Layer """
        super().Initialize(self,inputShape,**kwargs)
        return self

    def Transform(self,X):
        """ Execute Discrete Fourier Transform on Signal X """
        nSamples = X.shape[-1]
        X = fftpack.fft(X,n=nSamples,axis=-1,overwrite_x=True)
        np.copyto(self._signal,X)
        return self

    def Call(self,X):
        """ Call this Layer w/ Inputs X """
        super().Call(X)
        self.Transform(X)
        return self._signal

class InvDiscreteFourierTransform(AbstractLayer):
    """
    InvDiscreteFourierTransform - 
        Apply InverseDiscrete Fourier Transform to input signal
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  
    --------------------------------
    """
    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None):
        """ Constructor for NBandEquilizer Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)

    def Initialize(self,inputShape=None,**kwargs):
        """ Initialize Current Layer """
        super().Initialize(self,inputShape,**kwargs)
        return self

    def Transform(self,X):
        """ Execute Discrete Fourier Transform on Signal X """
        nSamples = X.shape[-1]
        X = fftpack.ifft(X,n=nSamples,axis=-1,overwrite_x=True)
        np.copyto(self._signal,X)
        return self

    def Call(self,X):
        """ Call this Layer w/ Inputs X """
        super().Call(X)
        self.Transform(X)
        return self._signal

class Equilizer(AbstractLayer) :
    """
    NBandEquilizer - 
        Parent Class of all N-band Equilizers
    --------------------------------
    _name (str) : Name for user-level identification
    _type (str) : Type of Layer Instance
    _sampleRate (int) : Number of samples per second  
    _chainIndex (int) : Location where Layer sits in chain 
    _next (AbstractParentLayer) : Next layer in the layer chain
    _prev (AbstractParentLayer) : Prev layer in the layer chain  
    _shapeInput (tup) : Indicates shape (and rank) of layer input
    _shapeOutput (tup) : Indicates shape (and rank) of layer output
    _initialized (bool) : Indicates if Layer has been initialized    
    _signal (arr) : Signal from Transform  

    _bands (list[bands]) : Bands to apply to this equilizer
    _nBands (int) : Number of filterbands to use in EQ
    --------------------------------
    """

    def __init__(self,name,sampleRate=44100,inputShape=None,next=None,prev=None,
                 bands=[]):
        """ Constructor for NBandEquilizer Instance """
        super().__init__(name,sampleRate,inputShape,next,prev)
        self._type = "Equilizier"

        self._bands = bands
        self._nBands = len(bands)

        self._frequencyResponse = self.BuildResponse()


    def BuildResponse(self):
        """ Build this module's frequency response curve """
        return self

    def ApplyResponse(self,X):
        """ Apply Frequency response curve to the signal """
        return X

    def Call(self,X):
        """ Call this Module with inputs X """
        super().Call(X)

        return X
