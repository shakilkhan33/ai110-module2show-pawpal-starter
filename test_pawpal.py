from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


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


def test_scheduler_sort_by_time_uses_hhmm_lambda_order() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Long walk", time_minutes=130, frequency="daily"))  # 02:10
	pet.add_task(Task(description="Feed", time_minutes=45, frequency="daily"))  # 00:45
	pet.add_task(Task(description="Medication", time_minutes=75, frequency="daily"))  # 01:15
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	sorted_tasks = scheduler.sort_by_time()

	assert [task.time for task in sorted_tasks] == ["00:45", "01:15", "02:10"]


def test_scheduler_filter_tasks_by_completion_status() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	completed_task = Task(description="Brush", time_minutes=10, frequency="daily")
	pending_task = Task(description="Walk", time_minutes=20, frequency="daily")
	completed_task.mark_completed()
	pet.add_task(completed_task)
	pet.add_task(pending_task)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	completed_only = scheduler.filter_tasks(is_completed=True)
	pending_only = scheduler.filter_tasks(is_completed=False)

	assert [task.description for task in completed_only] == ["Brush"]
	assert [task.description for task in pending_only] == ["Walk"]


def test_scheduler_filter_tasks_by_pet_name() -> None:
	owner = Owner(name="Alex", available_hours=2)
	dog = Pet(name="Mochi", species="dog", age=3)
	cat = Pet(name="Luna", species="cat", age=2)
	dog.add_task(Task(description="Walk", time_minutes=20, frequency="daily"))
	cat.add_task(Task(description="Litter", time_minutes=5, frequency="daily"))
	owner.add_pet(dog)
	owner.add_pet(cat)

	scheduler = Scheduler(owner)
	mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")

	assert [task.description for task in mochi_tasks] == ["Walk"]


def test_scheduler_filter_tasks_by_completion_and_pet_name() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	done = Task(description="Feed", time_minutes=10, frequency="daily")
	pending = Task(description="Play", time_minutes=15, frequency="daily")
	done.mark_completed()
	pet.add_task(done)
	pet.add_task(pending)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	filtered = scheduler.filter_tasks(is_completed=True, pet_name="Mochi")

	assert [task.description for task in filtered] == ["Feed"]


def test_mark_completed_daily_creates_next_occurrence() -> None:
	pet = Pet(name="Mochi", species="dog", age=3)
	task = Task(description="Morning walk", time_minutes=20, frequency="daily")
	pet.add_task(task)

	task.mark_completed()

	assert len(pet.tasks) == 2
	assert task.is_completed is True
	new_task = pet.tasks[1]
	assert new_task.description == "Morning walk"
	assert new_task.frequency == "daily"
	assert new_task.is_completed is False
	assert new_task.due_date == date.today() + timedelta(days=1)


def test_mark_completed_weekly_creates_single_next_occurrence() -> None:
	pet = Pet(name="Mochi", species="dog", age=3)
	task = Task(description="Nail trim", time_minutes=15, frequency="weekly")
	pet.add_task(task)

	task.mark_completed()
	task.mark_completed()

	assert len(pet.tasks) == 2
	assert sum(1 for existing in pet.tasks if not existing.is_completed) == 1
	new_task = next(existing for existing in pet.tasks if not existing.is_completed)
	assert new_task.due_date == date.today() + timedelta(days=7)


def test_scheduler_mark_task_complete_with_frequency_creates_matching_recurrence() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Feed", time_minutes=10, frequency="daily"))
	pet.add_task(Task(description="Feed", time_minutes=10, frequency="weekly"))
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	completed = scheduler.mark_task_complete("Mochi", "Feed", frequency="weekly")

	assert completed.frequency == "weekly"
	assert completed.is_completed is True
	weekly_pending = [
		task for task in pet.tasks if task.description == "Feed" and task.frequency == "weekly" and not task.is_completed
	]
	daily_pending = [
		task for task in pet.tasks if task.description == "Feed" and task.frequency == "daily" and not task.is_completed
	]

	assert len(weekly_pending) == 1
	assert len(daily_pending) == 1


def test_scheduler_mark_task_complete_requires_frequency_when_ambiguous() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Feed", time_minutes=10, frequency="daily"))
	pet.add_task(Task(description="Feed", time_minutes=10, frequency="weekly"))
	owner.add_pet(pet)

	scheduler = Scheduler(owner)

	try:
		scheduler.mark_task_complete("Mochi", "Feed")
		raised = False
	except ValueError:
		raised = True

	assert raised is True


def test_add_task_raises_for_incomplete_task_at_same_time() -> None:
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Morning walk", time_minutes=20, frequency="daily", start_time="09:00"))

	try:
		pet.add_task(Task(description="Feed breakfast", time_minutes=10, frequency="daily", start_time="09:00"))
		raised = False
	except ValueError:
		raised = True

	assert raised is True


def test_add_task_allows_same_time_when_existing_is_completed() -> None:
	pet = Pet(name="Mochi", species="dog", age=3)
	first = Task(description="Morning walk", time_minutes=20, frequency="daily", start_time="09:00")
	pet.add_task(first)
	first.mark_completed()

	pet.add_task(Task(description="Feed breakfast", time_minutes=10, frequency="daily", start_time="09:00"))

	assert len(pet.tasks) >= 2
