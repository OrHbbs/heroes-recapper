# vals = [6.8, 6.4, 5.7, 4.5, 4.4, 3.8, 3.7, 3.7]
vals = [2.5, 1.0, 7.6, 1.1, 2.3, 6.5]

variance = 0
mean = 0
length = len(vals)

for i in vals:
    mean += i

mean = mean / length

for i in vals:
    variance += ((i - mean) ** 2)

variance = variance / (length - 1)

print(f"mean: {mean}")
print(f"variance: {variance}")

print(f"")