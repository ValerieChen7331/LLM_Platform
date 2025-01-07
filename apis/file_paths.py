from pathlib import Path

class FilePaths:
    def __init__(self, base_dir=None):
        # 設定 TMP_DIR、LOCAL_VECTOR_STORE_DIR 和 OUTPUT_DIR 的路徑
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.joinpath('data')
        else:
            base_dir = Path(base_dir)  # 確保 base_dir 是 Path 對象

        self.TMP_DIR = base_dir.joinpath('tmp')
        self.LOCAL_VECTOR_STORE_DIR = base_dir.joinpath('vector_store')
        self.OUTPUT_DIR = base_dir.joinpath('output')

    def get_tmp_dir(self):
        # 獲取 TMP_DIR
        return self.TMP_DIR

    def get_local_vector_store_dir(self):
        # 獲取 LOCAL_VECTOR_STORE_DIR
        return self.LOCAL_VECTOR_STORE_DIR

    def get_output_dir(self):
        # 獲取 OUTPUT_DIR
        return self.OUTPUT_DIR

    def get_doc_paths(self):
        # 獲取所有文件路徑
        return self.TMP_DIR, self.LOCAL_VECTOR_STORE_DIR, self.OUTPUT_DIR


