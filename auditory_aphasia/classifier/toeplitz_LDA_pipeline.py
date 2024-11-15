from sklearn.pipeline import Pipeline, make_pipeline
from pyclf.lda.classification import ToeplitzLDA

class ToeplitzLDAPipeline:
    def __init__(self, n_channels):
        self.model = make_pipeline(ToeplitzLDA(n_channels=n_channels, unit_w=True))

    def get_model(self) -> Pipeline:
        return self.model