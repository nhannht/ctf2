# Model Inversion Write-up

## Challenge Summary

The challenge provides two files:

- `run.py`: loads `image.png`, converts it to grayscale bytes, loads `model.pt`,
  and prints `model(x)`.
- `model.pt`: a PyTorch serialized model.

The prompt says the model always predicts zero. That is the hint: instead of
training or guessing inputs, invert the model and recover the image that makes
the final check pass.

## Safe Inspection

Do not start with `torch.load("model.pt", weights_only=False)` on an untrusted
CTF artifact. The model is a pickle-backed Torch archive, so inspect it as a zip
first:

```bash
unzip -l model.pt
python3 -m pickletools model/data.pkl
```

The pickle metadata shows only standard Torch classes:

```text
torch.nn.modules.container Sequential
torch.nn.modules.linear Linear
torch.nn.modules.activation ReLU
```

The model is a `Sequential` network with 100 alternating `Linear` and `ReLU`
layers. The tensor data is sparse and made mostly from small integer weights
such as `-2`, `-1`, `0`, `1`, and `2`, which is a strong sign that the network
implements Boolean logic rather than learned image detection.

## Model Structure

`run.py` converts the image into a flat grayscale vector:

```python
x = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8).float()
```

The first layers expect `1369` input pixels, so the image is `37x37`.

The first two linear layers convert each pixel into one bit:

```text
bit = 1 if pixel <= 127 else 0
```

The remaining layers operate on `1376` bits. This is the `37x37` image
(`1369` bits) plus seven padding bits. Layer patterns reveal a 32-round
bitwise Feistel transform over 43 blocks of 32 bits. Each round computes:

```text
new_left[i] = right[i] XOR left[(i+14) mod 16]
              XOR (left[(i+8) mod 16] AND left[(i+15) mod 16])
              XOR key[i]
new_right[i] = left[i]
```

The final layers compare the transformed state against one fixed 1376-bit
target, then sum all successful bit comparisons. The last bias is `-1375`, so
the output is positive only when every bit comparison passes.

## Inverting the Model

Extract the final target from the comparator layer:

```text
weight =  1, bias = 0  -> required bit is 1
weight = -1, bias = 1  -> required bit is 0
```

Then extract the per-round key bits from each round layer. The two observed
six-weight patterns encode the key bit:

```text
[ 1, -2,  1,  1, -2,  1], bias 0 -> key bit 0
[-1,  2, -1, -1,  2, -1], bias 1 -> key bit 1
```

Reverse the rounds from last to first. Since the round outputs
`new_right = old_left`, inversion is direct:

```python
old_left = new_right
old_right[i] = new_left[i] ^ old_left[(i+14) & 15] \
               ^ (old_left[(i+8) & 15] & old_left[(i+15) & 15]) \
               ^ key[i]
```

After reversing all 32 rounds, the first 1369 bits form the original `37x37`
binary image. Rendering `1` as black and `0` as white produces a QR code with a
valid quiet border.

## Decoding

Save the recovered bits as a scaled image and decode it:

```bash
zbarimg --raw recovered.png
```

Output:

```text
HCMUS-CTF{n0t_all_model5_4re_th3_s4me!}
```

## Flag

```text
HCMUS-CTF{n0t_all_model5_4re_th3_s4me!}
```
