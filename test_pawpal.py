from pawpal_system import Pet, Task


def test_mark_complition_changes_task_status_to_true() -> None:
	task = Task(description="Evening walk", time_minutes=20, frequency="daily")

	assert task.is_completed is False

	task.mark_complition()

	assert task.is_completed is True


def test_adding_task_to_pet_increases_task_count() -> None:
	pet = Pet(name="Mochi", species="dog", age=3)
	initial_count = len(pet.tasks)

	task = Task(description="Feed dinner", time_minutes=10, frequency="daily")
	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1
