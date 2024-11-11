ClassificationPipelineClass = None
CallibrationDataProviderClass = None

n_channels : int
n_class : int
n_stimulus : int

ivals : list[tuple[float]]
filter_order : int
filter_freq : tuple[float]
baseline : str|int|float
tmin : float
tmax : float

dynamic_stopping : bool 
dynamic_stopping_params : dict[str,float|int] 

adaptation : bool
adaptation_eta_cov : float 
adaptation_eta_mean : float

labels_binary_classification : dict[str,int] 