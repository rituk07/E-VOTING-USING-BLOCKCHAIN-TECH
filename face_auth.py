import cv2
import numpy as np
import os

# Path to the Haar Cascade for face detection
CASC_PATH = os.path.join(os.path.dirname(__file__), "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(CASC_PATH)

def get_face_roi(image_path):
    """Detects a face, resizes it to a standard size for better comparison, and returns grayscale ROI."""
    if not os.path.exists(image_path):
        return None
    
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    
    if len(faces) == 0:
        return None
    
    # Sort by area (take largest face)
    faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
    (x, y, w, h) = faces[0]
    
    face_roi = gray[y:y+h, x:x+w]
    # Resize to a fixed size to make LBPH smoother/more accurate
    return cv2.resize(face_roi, (200, 200))

def is_duplicate_face(new_face_path, stored_faces_dir):
    """
    Checks if the new face matches any already registered face.
    Excludes the new face itself from the check.
    """
    new_face_roi = get_face_roi(new_face_path)
    if new_face_roi is None:
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    new_face_filename = os.path.basename(new_face_path)
    
    for filename in os.listdir(stored_faces_dir):
        # SKIP the current file being checked (the temp file)
        if filename == new_face_filename or filename.startswith("temp_"):
            continue
            
        if filename.endswith((".png", ".jpg", ".jpeg")):
            stored_path = os.path.join(stored_faces_dir, filename)
            stored_face_roi = get_face_roi(stored_path)
            
            if stored_face_roi is not None:
                recognizer.train([stored_face_roi], np.array([1]))
                label, confidence = recognizer.predict(new_face_roi)
                
                # Confidence < 55 is a very strong match (likely same person)
                if confidence < 55:
                    print(f"DEBUG: Duplicate found with {filename} (Conf: {confidence})")
                    return True
                    
    return False

def verify_identity(stored_image_path, live_image_path):
    """
    Verifies live capture against stored profile.
    Optimized for smoothness and varied lighting.
    """
    live_face_roi = get_face_roi(live_image_path)
    stored_face_roi = get_face_roi(stored_image_path)

    if live_face_roi is None: return "NO FACE DETECTED"
    if stored_face_roi is None: return "ERROR: PROFILE DATA CORRUPT"

    # Multi-face check (Loosened as per user request to avoid accidental blocks)
    # We will still detect them but maybe just log it or allow it if a primary face is strong
    img = cv2.imread(live_image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    
    # Optional: Log multi-face but don't block UNLESS requested strictly
    # if len(faces) > 1: print("WARN: Multiple faces in frame")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train([stored_face_roi], np.array([1]))
    label, confidence = recognizer.predict(live_face_roi)
    
    print(f"DEBUG: Match confidence: {confidence}")
    
    # 85-90 is a good threshold for resized LBPH
    if confidence < 85:
        return "MATCH"
    else:
        return "NO MATCH"