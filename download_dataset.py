
import kagglehub
import os

path = kagglehub.dataset_download("omenkj/customer-service-conversations-in-english-hindi")

print("Path to dataset files:", path)

print("\nFiles in dataset:")
for root, dirs, files in os.walk(path):
    for file in files:
        print(os.path.join(root, file))
