

import boto3

# Initialize the S3 client with your credentials (ensure they're configured)
s3 = boto3.client('s3')

def upload_audio_to_s3(file_path, bucket_name, object_name):
    """
    Uploads an audio file to an S3 bucket and sets the content type for direct playback.
    """
    
    try:
        # Upload the file to S3 with Content-Type set as audio/mpeg
        s3.upload_file(
            file_path, 
            bucket_name, 
            object_name, 
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        print(f"File {object_name} uploaded successfully to {bucket_name}.")
        
        # Construct the public URL for the uploaded file
        public_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        print(public_url)
        return public_url
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

