# test_vertex.py
import os, vertexai
from vertexai.generative_models import GenerativeModel
project = os.environ["GCP_PROJECT_ID"]
location = os.environ.get("VERTEX_LOCATION","us-central1")
vertexai.init(project=project, location=location)
m = GenerativeModel(os.environ.get("VERTEX_CHAT_MODEL","gemini-1.5-flash-8b"))
print(m.generate_content("Say hello in 3 words").text)
