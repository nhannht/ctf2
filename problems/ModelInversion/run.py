#!/usr/bin/env python3
import torch
from PIL import Image

image = Image.open("image.png").convert("L")
x = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8).float()
model = torch.load("model.pt", weights_only=False)
y = model(x)
print(float(y))
