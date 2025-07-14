import base64
from fastapi import HTTPException, Path, UploadFile


class ImageManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        #self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, file: UploadFile) -> str:
        if not file.filename.endswith(".jpg"):
            raise HTTPException(status_code=400, detail="Only .jpg files are allowed")
        file_path = self.storage_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file.filename

    def get_image_path(self, filename: str) -> Path:
        file_path = f"{self.storage_dir}/{filename}"
        #if not file_path.exists():
        #    raise HTTPException(status_code=404, detail="Image not found")
        return file_path

    def delete_image(self, filename: str) -> bool:
        file_path = self.get_image_path(filename)
        file_path.unlink()
        return True
    
    def base64ConvertImage(self, filename: str):
        file_path = self.get_image_path(filename)
        with open(file_path, "rb") as image_file:
            encoded_bytes = base64.b64encode(image_file.read())
            encoded_string = encoded_bytes.decode("utf-8")

        return encoded_string