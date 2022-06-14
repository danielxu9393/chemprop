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
print(-a)
print(np.take(a, (1,), axis=1))
print(a[:,1]) # automatically squeezes because is taking index!
print(np.take(a, (1,), axis=1).squeeze(axis=1))


x = np.array([[[0, 3, 2, 0],
               [1, 3, 1, 1]],

              [[3, 2, 3, 3],
               [0, 3, 2, 0]],

              [[1, 0, 3, 1],
               [3, 2, 3, 3]],

              [[0, 3, 2, 0],
               [1, 3, 2, 2]],

              [[3, 0, 3, 1],
               [1, 0, 1, 1]],

              [[1, 3, 1, 1],
               [3, 1, 3, 3]]])


choices = np.array([[1, 1, 1, 1],
                    [0, 1, 1, 0],
                    [1, 1, 1, 1],
                    [1, 0, 0, 0],
                    [1, 0, 1, 1],
                    [0, 0, 0, 1]])

print(np.take_along_axis(x, choices[:,None], axis=1)) # choices[:,None] adds a dimension size 1 to axis=1!
print(np.take_along_axis(x, choices[:,None], axis=1).shape)

#for take_along_axis, values of choices array are the indices for axis=axis of x!

print(np.argsort(x, axis=2)) # since axis=-1, sorts each "pipe" independently!
sort_ind = np.argsort(x, axis=2)
print(sort_ind.shape)
print(x[sort_ind].shape)
sorted = np.take_along_axis(x, sort_ind, axis=2)
print(sorted)

#print(np.argsort(x, axis=0)) # idk what this does? sorts each pipe but along axis=0??? Viewing as nd thingy?

y = np.array([1,2,3,4,5,6])

y = np.append(y, np.Inf)
print(y)