import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
available_hours = st.number_input("Available hours today", min_value=0.0, max_value=24.0, value=2.0, step=0.5)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Pet age", min_value=0, max_value=100, value=2)

# Keep a single Owner object in session state so it persists across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_hours=float(available_hours))
else:
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_hours = float(available_hours)

# Keep a scheduler attached to the current owner.
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)
else:
    st.session_state.scheduler.owner = st.session_state.owner

if st.button("Add pet"):
    owner = st.session_state.owner
    try:
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        st.success(f"Added pet '{pet_name}'.")
    except ValueError as exc:
        st.info(str(exc))

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"], index=0)
with col4:
    start_time = st.text_input("Start time (HH:MM)", value="08:00")

if st.button("Add task"):
    owner = st.session_state.owner
    scheduler = st.session_state.scheduler

    try:
        owner.get_pet(pet_name)
    except ValueError:
        try:
            owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        except ValueError as exc:
            st.error(str(exc))
    try:
        scheduler.add_task_to_pet(
            pet_name,
            Task(description=task_title, time_minutes=int(duration), frequency=frequency, start_time=start_time),
        )
        st.success(f"Added task to '{pet_name}'.")
    except ValueError as exc:
        st.error(str(exc))

owner = st.session_state.owner
try:
    current_pet = owner.get_pet(pet_name)
    pet_tasks = current_pet.get_tasks(include_completed=True)
except ValueError:
    pet_tasks = []

if pet_tasks:
    st.write(f"Current tasks for {pet_name}:")
    st.table([task.get_info() for task in pet_tasks])
else:
    st.info("No tasks yet for this pet. Add one above.")

st.divider()

st.subheader("Build Schedule")
max_plan_minutes = st.number_input("Max minutes to schedule", min_value=1, max_value=24 * 60, value=90, step=5)
st.caption(
    "Schedule strategy: quick wins (short tasks), fairness across pets, then best-fit fill within your time budget."
)

if st.button("Generate schedule"):
    scheduler = st.session_state.scheduler
    organized_tasks = scheduler.organize_tasks(include_completed=False)
    if not organized_tasks:
        st.warning("No pending tasks to schedule.")
    else:
        st.markdown("### Organized Tasks")
        st.table([task.get_info() for task in organized_tasks])

        plan = scheduler.generate_plan(max_minutes=int(max_plan_minutes))
        st.markdown("### Today's Plan")
        st.table([task.get_info() for task in plan])

        total_minutes = sum(task.time_minutes for task in plan)
        st.caption(f"Total scheduled time: {total_minutes} minutes")
