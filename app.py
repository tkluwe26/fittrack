import streamlit as st
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="FitTrack Single-User", layout="wide")

# -------------------------------------------
# Initialize session state
# -------------------------------------------
if 'training_plans' not in st.session_state:
    st.session_state.training_plans = []  # List of dicts: name, days
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None
if 'last_workout_date' not in st.session_state:
    st.session_state.last_workout_date = None

# -------------------------------------------
# Helper functions
# -------------------------------------------
def save_to_json():
    data = {
        "training_plans": st.session_state.training_plans,
        "last_workout_date": st.session_state.last_workout_date
    }
    st.session_state.json_backup = json.dumps(data, indent=2)

def load_from_json(json_str):
    data = json.loads(json_str)
    st.session_state.training_plans = data.get("training_plans", [])
    st.session_state.last_workout_date = data.get("last_workout_date", None)

def add_plan(name):
    st.session_state.training_plans.append({
        "name": name,
        "days": []
    })

def add_day(plan_idx, day_name):
    st.session_state.training_plans[plan_idx]["days"].append({
        "name": day_name,
        "exercises": []
    })

def add_exercise(plan_idx, day_idx, exercise_name):
    st.session_state.training_plans[plan_idx]["days"][day_idx]["exercises"].append({
        "name": exercise_name,
        "sets": [
            {"weight": 0, "reps": 0, "rir": 0}
        ],
        "pr": None
    })

def add_set(plan_idx, day_idx, ex_idx):
    st.session_state.training_plans[plan_idx]["days"][day_idx]["exercises"][ex_idx]["sets"].append(
        {"weight": 0, "reps": 0, "rir": 0}
    )

def update_pr(exercise):
    best = None
    for s in exercise["sets"]:
        if best is None or s["weight"] > best["weight"]:
            best = s
    exercise["pr"] = best

# -------------------------------------------
# Sidebar: Plan Management
# -------------------------------------------
st.sidebar.header("Trainingspläne")
plan_names = [p["name"] for p in st.session_state.training_plans]
selected_plan = st.sidebar.selectbox("Plan auswählen", ["--Neu--"] + plan_names)

if selected_plan == "--Neu--":
    new_plan_name = st.sidebar.text_input("Name für neuen Plan")
    if st.sidebar.button("Plan erstellen") and new_plan_name:
        add_plan(new_plan_name)
        save_to_json()
        st.experimental_rerun()
else:
    plan_idx = plan_names.index(selected_plan)
    st.sidebar.write(f"**{selected_plan} verwalten**")
    if st.sidebar.button("Plan löschen"):
        st.session_state.training_plans.pop(plan_idx)
        save_to_json()
        st.experimental_rerun()

# -------------------------------------------
# Main Area: Plan Details
# -------------------------------------------
if selected_plan != "--Neu--" and selected_plan in plan_names:
    plan_idx = plan_names.index(selected_plan)
    plan = st.session_state.training_plans[plan_idx]
    st.header(f"Trainingsplan: {plan['name']}")

    # Add/Edit Days
    st.subheader("Trainingseinheiten")
    for day_idx, day in enumerate(plan["days"]):
        with st.expander(f"{day['name']}"):
            new_day_name = st.text_input(f"Name bearbeiten", value=day["name"], key=f"dayname{day_idx}")
            st.session_state.training_plans[plan_idx]["days"][day_idx]["name"] = new_day_name

            # Exercises
            st.markdown("**Übungen:**")
            for ex_idx, ex in enumerate(day["exercises"]):
                with st.expander(f"{ex['name']} (PR: {ex['pr']['weight'] if ex['pr'] else '-'})"):
                    new_ex_name = st.text_input("Übungsname", value=ex["name"], key=f"exname{day_idx}{ex_idx}")
                    st.session_state.training_plans[plan_idx]["days"][day_idx]["exercises"][ex_idx]["name"] = new_ex_name

                    for set_idx, s in enumerate(ex["sets"]):
                        cols = st.columns(4)
                        s["weight"] = cols[0].number_input("Gewicht", value=s["weight"], key=f"w{day_idx}{ex_idx}{set_idx}")
                        s["reps"] = cols[1].number_input("Reps", value=s["reps"], key=f"r{day_idx}{ex_idx}{set_idx}")
                        s["rir"] = cols[2].number_input("RIR", value=s["rir"], key=f"rir{day_idx}{ex_idx}{set_idx}")
                        if cols[3].button("Set löschen", key=f"delset{day_idx}{ex_idx}{set_idx}"):
                            ex["sets"].pop(set_idx)
                            st.experimental_rerun()

                    if st.button("Set hinzufügen", key=f"addset{day_idx}{ex_idx}"):
                        add_set(plan_idx, day_idx, ex_idx)
                        st.experimental_rerun()

            new_ex_name = st.text_input(f"Neue Übung hinzufügen", key=f"newex{day_idx}")
            if st.button("Übung hinzufügen", key=f"addex{day_idx}") and new_ex_name:
                add_exercise(plan_idx, day_idx, new_ex_name)
                st.experimental_rerun()

    # Add Day
    new_day_name = st.text_input("Neue Trainingseinheit hinzufügen", key="newday")
    if st.button("Einheit hinzufügen"):
        if new_day_name:
            add_day(plan_idx, new_day_name)
            st.experimental_rerun()

    # -------------------------------------------
    # Start Training / PR & Progress
    # -------------------------------------------
    st.subheader("Training durchführen / Fortschritt")
    if plan["days"]:
        next_day_idx = 0
        if st.session_state.last_workout_date:
            next_day_idx = (st.session_state.last_workout_date + 1) % len(plan["days"])
        next_day = plan["days"][next_day_idx]

        st.markdown(f"**Nächste Einheit:** {next_day['name']}")
        chosen_day = st.selectbox("Andere Einheit wählen", [d["name"] for d in plan["days"]], index=next_day_idx)
        chosen_day_idx = [d["name"] for d in plan["days"]].index(chosen_day)
        exercises = plan["days"][chosen_day_idx]["exercises"]

        for ex_idx, ex in enumerate(exercises):
            st.markdown(f"### {ex['name']}")
            for set_idx, s in enumerate(ex["sets"]):
                cols = st.columns(3)
                s["weight"] = cols[0].number_input("Gewicht", value=s["weight"], key=f"trw{chosen_day_idx}{ex_idx}{set_idx}")
                s["reps"] = cols[1].number_input("Reps", value=s["reps"], key=f"trr{chosen_day_idx}{ex_idx}{set_idx}")
                s["rir"] = cols[2].number_input("RIR", value=s["rir"], key=f"trrir{chosen_day_idx}{ex_idx}{set_idx}")

            # Update PR automatisch
            update_pr(ex)

        if st.button("Training speichern"):
            st.session_state.last_workout_date = chosen_day_idx
            save_to_json()
            st.success("Training gespeichert!")

    # -------------------------------------------
    # Fortschrittsgraphen
    # -------------------------------------------
    st.subheader("Fortschritt / Graphen")
    for day in plan["days"]:
        for ex in day["exercises"]:
            if ex["sets"]:
                orm_values = [s["weight"] for s in ex["sets"]]
                if orm_values:
                    plt.figure()
                    plt.plot(range(1, len(orm_values)+1), orm_values, marker='o')
                    plt.title(f"{ex['name']} - Verlauf")
                    plt.xlabel("Satz")
                    plt.ylabel("Gewicht (kg)")
                    st.pyplot(plt.gcf())
                    plt.clf()

    # -------------------------------------------
    # Export / Backup
    # -------------------------------------------
    st.subheader("Backup / Export")
    if st.button("Als JSON exportieren"):
        save_to_json()
        st.download_button("JSON herunterladen", st.session_state.json_backup, file_name="fittrack_backup.json")
