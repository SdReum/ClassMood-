from fastapi import UploadFile

def process_files(files: list[UploadFile]):
    # Заглушка. Замени на свой алгоритм.
    return [{"filename": f.filename, "result": "processed"} for f in files]