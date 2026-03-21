import requests
import json
import io

def test_resume_upload():
    # We will upload a standard text resume as a generic file to test the ML pipeline
    # The Backend routes it to ML automatically
    resume_content = b"""
    Alice Smith - Machine Learning Engineer
    I have 4 years of experience building scalable AI systems.
    Skills: Python, TensorFlow, PyTorch, Kubernetes, Docker, FastApi, SQL
    Domain: Artificial Intelligence
    """

    print("Uploading resume to the Resume API...")
    url = "http://localhost:8000/api/resume/upload"
    
    # We simulate a file upload using standard text
    files = {"file": ("resume.txt", io.BytesIO(resume_content), "text/plain")}
    data = {"user_id": "demo-user"}
    
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        print("\nSUCCESS! Here is what the ML model extracted:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"FAILED (Status {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    test_resume_upload()
