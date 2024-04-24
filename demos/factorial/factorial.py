import math
import sys
from datetime import datetime
import time

starttime = datetime.now()
for x in range(3,6):
    n = pow(10,x)
    for y in range(1,10):
        laptime = datetime.now()
        result = math.factorial(y*n)
        runtime = datetime.now() - laptime
        print(f'Lap time of factorial({y*n}): {runtime.total_seconds()}')
runtime = datetime.now() - starttime
print(f'Total runtime: {runtime.total_seconds()}')
print(f'Done...')
