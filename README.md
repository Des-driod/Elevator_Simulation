# Elevator_Simulation

# 🛗 Elevator Control System Simulation — 11 Floors

A working simulation of a passenger elevator serving an **11-storey building**, demonstrating the **SCAN dispatch algorithm** used by real elevator controllers — call registration, directional sweep dispatch, arrival/stop decisions, load sensing against a rated capacity, and door safety interlocks.

**Author:** Asuquo, Destiny Bassey
**Registration Number:** 23/EG/CV/069
**Department:** Civil Engineering, Faculty of Engineering, University of Uyo

---

## What this project shows

| # | Mechanism | What it does |
|---|---|---|
| 1 | **Call registration** | A landing button sets a flag in a request table rather than moving the car instantly |
| 2 | **SCAN dispatch** | The car sweeps in its current direction, serving every flagged floor along the way, and only reverses once nothing is left ahead |
| 3 | **Arrival check** | At every floor passed: is it flagged, and does it match the current direction? If so, stop and open doors |
| 4 | **Load sensing** | A simulated strain gauge tracks total cabin mass; the cab is rated **680 kg (~10 passengers)** and refuses to run overloaded |
| 5 | **Door interlocks** | Doors only unlock level with the floor sill, and hold open if the load sensor trips |
| 6 | **Idle parking** | With no pending calls the car holds its last position rather than always returning to floor 1 |

## Files in this repository

| File | Purpose |
|---|---|
| `app.py` | Streamlit app — live, clickable simulation with call buttons, a passenger-load slider, and a step-by-step shaft animation |
| `requirements.txt` | Python dependencies needed to run `app.py` |
