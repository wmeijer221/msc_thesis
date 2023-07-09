

from collections import deque
import datetime
dt = datetime.datetime(2000, 3, 5, 12, 3, 35, 23)
print(dt.timestamp())


q = deque(range(15))

for e in q:
    print(e)

print(q)


q2 = deque()
r = q2.popleft()
print(r)