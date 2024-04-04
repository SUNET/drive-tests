import math
import sys
from datetime import datetime
import time

sys.set_int_max_str_digits(2147483647)

for x in range(3,7):
    n = pow(10,x)
    for y in range(1,10):
        starttime = datetime.now()
        result = math.factorial(y*n)
        runtime = datetime.now() - starttime
        # print(f'Time to calculate {y*n}!:\t {runtime.total_seconds()}s\t The result has {int(math.log10(result))+1} digits')
        print(f'Result of {y*n}!: {result}')