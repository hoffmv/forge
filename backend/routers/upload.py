from fastapi import APIRouter, UploadFile, File, HTTPException
from docx import Document
import tempfile
import os

router = APIRouter()

@router.post("/spec")
async def upload_spec(file: UploadFile = File(...)):
    """
    Upload a specification file (txt, md, or docx) and extract its text content.
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    allowed_extensions = ['.txt', '.md', '.docx']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        content = await file.read()
        text = ""
        
        # Extract text based on file type
        if file_ext in ['.txt', '.md']:
            # Plain text files
            text = content.decode('utf-8')
        
        elif file_ext == '.docx':
            # Word document - save temporarily and parse
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                doc = Document(tmp_path)
                # Extract all paragraph text
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                text = '\n\n'.join(paragraphs)
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
        
        return {
            "filename": file.filename,
            "text": text,
            "length": len(text)
        }
    
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding not supported. Please use UTF-8 encoded text files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )
