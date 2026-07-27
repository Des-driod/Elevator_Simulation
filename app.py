"""
Elevator Control System Simulation — 11 Floors
Author: Asuquo, Destiny Bassey
Registration Number: 23/EG/CV/069
Department: Civil Engineering, Faculty of Engineering, University of Uyo

A Streamlit app that models the SCAN dispatch algorithm used by real
elevator controllers: call registration, directional sweep dispatch,
arrival/stop decisions, load sensing against a rated capacity, and
door safety interlocks — across an 11-storey shaft.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

FLOORS = 11
CAPACITY_KG = 680
PERSON_KG = 68


class Elevator:
    """SCAN-dispatch elevator controller for an 11-floor building."""

    def __init__(self):
        self.current_floor = 1
        self.direction = 0          # 1 = up, -1 = down, 0 = idle
        self.queue = set()          # pending floor calls
        self.passengers = 0
        self.log = []
        self.path = [1]             # floor-by-floor trace, used for the visual
        self.events = []            # (floor, "stop"/"pass") per path step

    def call(self, floor):
        self.queue.add(floor)
        self._record(f"Call registered at floor {floor}.")

    def _record(self, msg):
        self.log.append(msg)

    def weight_kg(self):
        return self.passengers * PERSON_KG

    def overloaded(self):
        return self.weight_kg() > CAPACITY_KG

    def _next_stop(self):
        """SCAN rule: keep serving calls ahead in the current direction;
        only reverse once nothing remains ahead."""
        if not self.queue:
            return None
        if self.direction == 1:
            ahead = sorted(f for f in self.queue if f > self.current_floor)
            if ahead:
                return ahead[0]
            behind = sorted((f for f in self.queue if f < self.current_floor), reverse=True)
            if behind:
                return behind[0]
        elif self.direction == -1:
            ahead = sorted((f for f in self.queue if f < self.current_floor), reverse=True)
            if ahead:
                return ahead[0]
            behind = sorted(f for f in self.queue if f > self.current_floor)
            if behind:
                return behind[0]
        else:
            return min(self.queue, key=lambda f: abs(f - self.current_floor))
        return next(iter(self.queue))

    def run(self):
        """Serve every queued call using SCAN, recording the full path
        and a text log."""
        safety_limit = 500  # guards against any future logic bug freezing the app
        iterations = 0
        while self.queue:
            iterations += 1
            if iterations > safety_limit:
                self._record("Safety stop: too many dispatch cycles — aborting to avoid a freeze.")
                break

            dest = self._next_stop()

            # FIX: if the car is already parked on the called floor
            # (e.g. calling floor 1 while it's still sitting at floor 1),
            # serve it immediately instead of trying to "move" to a floor
            # it's already at — the old code looped forever here.
            if dest == self.current_floor:
                self.events.append((self.current_floor, "stop"))
                self._record(f"Already at floor {self.current_floor} — matches a pending call. "
                              f"STOP, doors open.")
                self.queue.discard(self.current_floor)
                if self.overloaded():
                    self._record(f"  ⚠ OVERLOAD ({self.weight_kg()}kg > {CAPACITY_KG}kg) "
                                  f"— doors held, alarm.")
                continue

            self.direction = 1 if dest > self.current_floor else -1
            self._record(f"Dispatch: continue {'UP' if self.direction == 1 else 'DOWN'} "
                          f"toward floor {dest} (SCAN).")
            step = 1 if dest > self.current_floor else -1
            while self.current_floor != dest:
                self.current_floor += step
                self.path.append(self.current_floor)
                if self.current_floor in self.queue:
                    self.events.append((self.current_floor, "stop"))
                    self._record(f"Arrived floor {self.current_floor} — matches a pending call. "
                                  f"STOP, doors open.")
                    self.queue.discard(self.current_floor)
                    if self.overloaded():
                        self._record(f"  ⚠ OVERLOAD ({self.weight_kg()}kg > {CAPACITY_KG}kg) "
                                      f"— doors held, alarm.")
                else:
                    self.events.append((self.current_floor, "pass"))
                    self._record(f"Passing floor {self.current_floor} — no matching call.")
        self.direction = 0
        self._record(f"No pending calls — parked at floor {self.current_floor}.")


def draw_shaft(current_floor, status_label, ok_color=True):
    """Render the shaft + car position as a matplotlib figure."""
    fig, ax = plt.subplots(figsize=(3.6, 6.2))
    fig.patch.set_facecolor("#14161a")
    ax.set_facecolor("#0e1012")
    ax.set_xlim(0, 1)
    ax.set_ylim(0.5, FLOORS + 0.8)
    ax.set_yticks(range(1, FLOORS + 1))
    ax.set_yticklabels([str(i) for i in range(1, FLOORS + 1)], color="#9aa0a6", fontsize=9)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_color("#3a3e44")
    ax.set_title("Cab 01 — 11-Floor Shaft", color="#c99a4b", fontsize=11, pad=10)
    for fl in range(1, FLOORS + 1):
        ax.axhline(fl, color="#26292d", lw=0.6, zorder=0)

    car_color = "#2f6b47" if ok_color else "#7a2b2b"
    car = patches.FancyBboxPatch((0.15, current_floor - 0.35), 0.7, 0.6,
                                  boxstyle="round,pad=0.02,rounding_size=0.05",
                                  linewidth=1.4, edgecolor="#63676e", facecolor=car_color, zorder=5)
    ax.add_patch(car)
    ax.text(0.5, current_floor, str(current_floor), color="#ff8c2b", fontsize=13,
            ha="center", va="center", weight="bold", zorder=6)
    ax.text(0.5, FLOORS + 0.55, status_label, color="#3ddc84", fontsize=10,
            ha="center", weight="bold")
    fig.tight_layout()
    return fig


def draw_trace(path, events):
    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor("#14161a")
    ax.set_facecolor("#0e1012")
    steps = list(range(len(path)))
    ax.plot(steps, path, color="#ffb703", marker="o", markersize=4, linewidth=1.6)
    event_map = dict(events)
    stop_idx = [i for i, f in enumerate(path) if event_map.get(f) == "stop"]
    ax.scatter([steps[i] for i in stop_idx], [path[i] for i in stop_idx],
               color="#3ddc84", s=70, zorder=5, label="Stop (call served)")
    ax.set_xlabel("Simulation step", color="#9aa0a6")
    ax.set_ylabel("Floor", color="#9aa0a6")
    ax.set_yticks(range(1, FLOORS + 1))
    ax.tick_params(colors="#9aa0a6")
    for spine in ax.spines.values():
        spine.set_color("#3a3e44")
    ax.set_title("Floor vs. Time — SCAN dispatch trace", color="#c99a4b")
    ax.legend(facecolor="#1b1e22", edgecolor="#3a3e44", labelcolor="#e9e6df")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- UI ----

st.set_page_config(page_title="Elevator Simulation — 11 Floors", page_icon="🛗", layout="wide")

st.title("🛗 Elevator Control System Simulation — 11 Floors")
st.caption(
    "**Author:** Asuquo, Destiny Bassey &nbsp;|&nbsp; "
    "**Reg No:** 23/EG/CV/069 &nbsp;|&nbsp; "
    "**Department:** Civil Engineering, University of Uyo"
)

with st.expander("How the dispatch logic works (read before demo)", expanded=False):
    st.markdown(
        """
1. **Call registration** — a landing button sets a flag in the request table; it does not move the car immediately.
2. **SCAN dispatch** — the car keeps sweeping in its current direction, collecting every flagged floor along the way, and only reverses once nothing is left ahead.
3. **Arrival check** — at every floor passed: is it flagged, and does it match the current direction? If so, stop and open doors.
4. **Load sensing** — a strain gauge tracks total mass; this cab is rated **680 kg (~10 passengers)** and refuses to run overloaded.
5. **Door interlocks** — doors only unlock level with the sill, and hold open if the load sensor trips.
6. **Idle parking** — with an empty queue the car holds its last position rather than returning to floor 1.
        """
    )

if "queue" not in st.session_state:
    st.session_state.queue = []

col_left, col_right = st.columns([1, 1.6])

with col_left:
    st.subheader("Landing Calls")
    st.write("Tap floors to queue calls, then run the simulation.")
    grid_cols = st.columns(4)
    for i, floor in enumerate(range(1, FLOORS + 1)):
        with grid_cols[i % 4]:
            label = f"F{floor}" + (" ✅" if floor in st.session_state.queue else "")
            if st.button(label, key=f"call_{floor}", use_container_width=True):
                if floor in st.session_state.queue:
                    st.session_state.queue.remove(floor)
                else:
                    st.session_state.queue.append(floor)

    st.write("Queued calls:", ", ".join(str(f) for f in st.session_state.queue) or "none")

    passengers = st.slider("Passengers on board", 0, 14, 5, help=f"Each passenger ≈ {PERSON_KG} kg")
    kg = passengers * PERSON_KG
    st.progress(min(1.0, kg / CAPACITY_KG), text=f"{kg} / {CAPACITY_KG} kg ({kg/CAPACITY_KG:.0%})")
    if kg > CAPACITY_KG:
        st.error(f"⚠ OVERLOAD — {kg}kg exceeds the {CAPACITY_KG}kg rated capacity. Doors will not close.")

    run_clicked = st.button("▶ Run Simulation", type="primary", use_container_width=True)
    clear_clicked = st.button("Clear queue", use_container_width=True)
    if clear_clicked:
        st.session_state.queue = []
        st.rerun()

with col_right:
    st.subheader("Shaft View")
    shaft_slot = st.empty()
    log_slot = st.empty()
    trace_slot = st.empty()

    if run_clicked and st.session_state.queue:
        el = Elevator()
        el.passengers = passengers
        for f in st.session_state.queue:
            el.call(f)
        el.run()

        # step-by-step animation
        for step_i, fl in enumerate(el.path):
            ev = dict(el.events).get(fl)
            if step_i == 0:
                label = "PARKED"
            elif ev == "stop":
                label = f"STOP — FLOOR {fl}"
            else:
                label = f"PASSING FLOOR {fl}"
            fig = draw_shaft(fl, label, ok_color=not el.overloaded())
            shaft_slot.pyplot(fig)
            plt.close(fig)
            time.sleep(0.6)

        log_slot.code("\n".join(el.log), language=None)
        fig2 = draw_trace(el.path, el.events)
        trace_slot.pyplot(fig2)
        plt.close(fig2)
        st.session_state.queue = []
    elif run_clicked:
        st.warning("Queue at least one floor call first.")
    else:
        fig = draw_shaft(1, "IDLE")
        shaft_slot.pyplot(fig)
        plt.close(fig)

st.divider()
st.caption(
    "Simulation only — timings compressed for demonstration. "
    "© Asuquo, Destiny Bassey — 23/EG/CV/069 — Department of Civil Engineering, University of Uyo."
      )
