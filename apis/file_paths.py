from pathlib import Path

class FilePaths:
    def __init__(self):
        self.TMP_DIR = Path(__file__).resolve().parent.parent.joinpath('data', 'tmp')
        self.LOCAL_VECTOR_STORE_DIR = Path(__file__).resolve().parent.parent.joinpath('data', 'vector_store')
        self.OUTPUT_DIR = Path(__file__).resolve().parent.parent.joinpath('data', 'output')

    def get_doc_paths(self):
        return self.TMP_DIR, self.LOCAL_VECTOR_STORE_DIR, self.OUTPUT_DIR
