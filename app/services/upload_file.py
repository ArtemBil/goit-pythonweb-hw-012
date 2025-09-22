import cloudinary
import cloudinary.uploader

"""Service for uploading files to Cloudinary and returning resized URLs."""

class UploadFileService:
    def __init__(self, cloud_name, api_key, api_secret):
        """Initialize Cloudinary configuration using provided credentials."""
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name = self.cloud_name,
            api_key = self.api_key,
            api_secret = self.api_secret,
            secure  = True
        )

    @staticmethod
    def upload_file(file, username) -> str:
        """Upload a file to Cloudinary and return a 200x200 fill-cropped URL."""
        public_id = f"{username}/{file.filename}"

        r = cloudinary.uploader.upload(
            file.file,
            public_id = public_id,
            overwrite = True
        )

        src_url = cloudinary.CloudinaryImage(public_id).build_url(width = 200, height = 200, crop = "fill", version = r.get("version"))

        return src_url