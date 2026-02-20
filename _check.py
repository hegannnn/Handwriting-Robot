import json

with open('normalized_library.json', 'r') as f:
    lib = json.load(f)

print("=== CHARACTER WIDTH ANALYSIS ===")
print("\nLOWERCASE:")
for c in sorted(lib.keys()):
    if lib[c] and c.islower():
        w = lib[c]['width']
        ratio = w / 100.0
        print(f"  {c}: width={w:.1f}  aspect={ratio:.2f}")

print("\nUPPERCASE:")
for c in sorted(lib.keys()):
    if lib[c] and c.isupper():
        w = lib[c]['width']
        ratio = w / 100.0
        print(f"  {c}: width={w:.1f}  aspect={ratio:.2f}")

print("\nSYMBOLS:")
for c in sorted(lib.keys()):
    if lib[c] and not c.isalpha():
        w = lib[c]['width']
        ratio = w / 100.0
        print(f"  '{c}': width={w:.1f}  aspect={ratio:.2f}")
