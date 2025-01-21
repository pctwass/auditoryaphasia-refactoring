from pyclf.lda.classification import ToeplitzLDA
from sklearn.pipeline import Pipeline, make_pipeline


def get_toeplitz_LDA_pipeline(n_channels: int, unit_w=True, **kwargs) -> Pipeline:
    return make_pipeline(ToeplitzLDA(n_channels=n_channels, unit_w=unit_w, **kwargs))

