from collections import deque

q = deque()



for i in range(10):
    q.append(i)

print(q)



for i in range(15):
    q.append(i + 10)
    q.popleft()
    print(q)