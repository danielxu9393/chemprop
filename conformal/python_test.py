import numpy as np

a=np.array([[1,2,3,4],
            [5,6,7,8]],
            dtype=float
          )

b=np.array([1,2,3,4])

print(a[0].shape)
print(b.shape)
print(b.tolist())
b=b.reshape(4,1)
print(b.shape)
print(b.tolist())
a[0]=a[0]-0.5
print(a)