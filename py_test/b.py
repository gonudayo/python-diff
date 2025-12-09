# test

load('default')

a=10
b=20 # test

cycle_start(1)

for i in range(3):
    # modified
    delay(2)

def xx():
    delay(1)
    pass

c=30

# modified
stop_robot()
cycle_end(1)
xx()
# test