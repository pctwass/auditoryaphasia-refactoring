import os
import pandas as pd


class PandasSaveUtility(object):
    def __init__(self, file_path : str, default_columns:list[str]=None):
        file_path_without_extension = self._get_file_path_without_extension(file_path)
        file_path = file_path_without_extension
        idx = 1

        while True:
            if os.path.exists(file_path_without_extension + '.pkl'):
                idx += 1
                file_path = f"{file_path_without_extension}_{idx}"
            else:
                break

        self._file_path = file_path + '.pkl'
        self.df = None
        self.default_columns=default_columns



    # 'columns' parameter is ignored when the dataframe already exists as a .pkl file.
    def add(
            self, 
            data : enumerate, 
            index : enumerate = None, 
            columns : enumerate[str] = None, 
            save_as_html : bool = False, 
            save_as_csv : bool = False
    ):
        if os.path.exists(self._file_path):
            df = pd.read_pickle(self._file_path)
            columns = df.columns
            df_add = pd.DataFrame(data=data, columns=columns, index=index)
            df = pd.concat([df, df_add])
        else:
            if columns is None:
                columns = self.default_columns
            df = pd.DataFrame(data=data, index=index, columns=columns)
            self.is_exists = True

        _ = df.to_pickle(self._file_path)
        self.df = df

        if save_as_html:
            self.save_html()

        if save_as_csv:
            self.save_csv()
    

    def save_csv(self):
        file_path_csv = self._get_file_path_without_extension(self._file_path) + ".csv"
        self.df.to_csv(file_path_csv)


    def save_html(self):
        file_path_html = self._get_file_path_without_extension(self._file_path) + ".html"
        self.df.to_csv(file_path_html)
    

    def print(self):
        import pandas as pd
        df = pd.read_pickle(self._file_path)
        print(df)


    def _get_file_path_without_extension(file_path : str) -> str:
        return os.splitext(file_path)[0]
