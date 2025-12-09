# test

load('default')

a=10
b=20 # test

cycle_start(1)

for i in range(3):
    # modified
    delay(1)

def xx():
    delay(1)
    pass

c=30

# modified
cycle_end(1)
stop_robot()
xx()
# test