import numpy as np
from random import seed

def off():
    print("OFF")

def periodic_update():
    print("Periodic Update")

def event_driven():
    print("Event Driven")

def payload_exchange():
    print("Payload Exhchange")


state_table = {
    0: off,
    1: periodic_update,
    2: event_driven,
    3: payload_exchange,
}


def sim_multinomial(v):
    r = np.random.uniform(0.0, 1.0)
    CS = np.cumsum(v)
    CS = np.insert(CS, 0, 0)
    m = (np.where(CS<r))[0]
    next_state=m[len(m)-1]
    
    return next_state

def run(P, state):
    start = (np.where(state>0))[1]
    current_state = start[0]
    state_hist = state

    for x in range(100):
        current_row = np.ma.masked_values((P[current_state]), 0.0)
        next_state = sim_multinomial(current_row)

        state = np.array([[0, 0, 0, 0]])
        state[0, next_state] = 1.0

        s = state_table[next_state]
        s()

        state_hist = np.append(state_hist, state, axis=0)
        current_state = next_state

    print("Histogram\n", state_hist)

if __name__ == "__main__":
    seed(4)

    P = np.array([[0, 0.98, 0.02, 0],
                  [1, 0, 0, 0],
                  [0, 0, 0, 1],
                  [1, 0, 0, 0]])
    state = np.array([[1.0, 0, 0, 0]])

    run(P, state)
