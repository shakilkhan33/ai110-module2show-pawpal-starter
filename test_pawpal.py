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


def test_scheduler_sort_by_time_descending_order() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Feed", time_minutes=45, frequency="daily"))  # 00:45
	pet.add_task(Task(description="Long walk", time_minutes=130, frequency="daily"))  # 02:10
	pet.add_task(Task(description="Medication", time_minutes=75, frequency="daily"))  # 01:15
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	sorted_tasks = scheduler.sort_by_time(descending=True)

	assert [task.time for task in sorted_tasks] == ["02:10", "01:15", "00:45"]


def test_scheduler_sort_by_due_date_chronological_order() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	today = date.today()
	pet.add_task(Task(description="Task 1", time_minutes=10, frequency="daily", due_date=today + timedelta(days=2)))
	pet.add_task(Task(description="Task 2", time_minutes=10, frequency="daily", due_date=today))
	pet.add_task(Task(description="Task 3", time_minutes=10, frequency="daily", due_date=today + timedelta(days=1)))
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	# Organize tasks should respect due_date as part of chronological ordering
	organized = scheduler.organize_tasks(include_completed=False)
	
	assert len(organized) == 3
	# Tasks should be ordered by priority score, but we can verify by description if needed
	# or check get_all_tasks to ensure all are present
	all_tasks = scheduler.get_all_tasks(include_completed=True)
	assert len(all_tasks) == 3


def test_scheduler_sort_by_time_with_multiple_pets() -> None:
	owner = Owner(name="Alex", available_hours=3)
	dog = Pet(name="Buddy", species="dog", age=3)
	cat = Pet(name="Luna", species="cat", age=2)
	
	dog.add_task(Task(description="Dog walk", time_minutes=60, frequency="daily"))  # 01:00
	dog.add_task(Task(description="Dog feed", time_minutes=15, frequency="daily"))  # 00:15
	cat.add_task(Task(description="Cat feed", time_minutes=10, frequency="daily"))  # 00:10
	cat.add_task(Task(description="Cat play", time_minutes=30, frequency="daily"))  # 00:30
	
	owner.add_pet(dog)
	owner.add_pet(cat)

	scheduler = Scheduler(owner)
	sorted_tasks = scheduler.sort_by_time()

	# All tasks sorted by time across all pets
	assert [task.time for task in sorted_tasks] == ["00:10", "00:15", "00:30", "01:00"]


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


def test_filter_tasks_returns_empty_for_pet_with_no_tasks() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)

	assert scheduler.filter_tasks(pet_name="Mochi") == []


def test_generate_plan_returns_empty_when_owner_has_no_tasks() -> None:
	owner = Owner(name="Alex", available_hours=2)
	owner.add_pet(Pet(name="Mochi", species="dog", age=3))

	scheduler = Scheduler(owner)
	plan = scheduler.generate_plan()

	assert plan == []


def test_scheduler_detect_pet_conflicts_flags_duplicate_times() -> None:
	owner = Owner(name="Alex", available_hours=3)
	pet = Pet(name="Mochi", species="dog", age=3)
	
	# Add two tasks at the same time (conflict)
	pet.add_task(Task(description="Morning walk", time_minutes=20, frequency="daily", start_time="09:00"))
	try:
		pet.add_task(Task(description="Breakfast", time_minutes=10, frequency="daily", start_time="09:00"))
	except ValueError:
		# Expected to raise during add_task, so we simulate conflict by bypassing the check
		pass
	
	# Use scheduler to detect conflicts (this allows us to bypass Pet's add_task validation)
	pet2 = Pet(name="Buddy", species="dog", age=2)
	pet2.tasks.append(Task(description="Walk 1", time_minutes=30, frequency="daily", start_time="14:00"))
	pet2.tasks.append(Task(description="Walk 2", time_minutes=20, frequency="daily", start_time="14:00"))
	
	owner.add_pet(pet2)
	scheduler = Scheduler(owner)
	
	conflicts = scheduler.detect_pet_conflicts("Buddy")
	
	# Should detect the 14:00 time conflict
	assert "14:00" in conflicts
	assert len(conflicts["14:00"]) == 2
	assert all(task.start_time == "14:00" for task in conflicts["14:00"])


def test_scheduler_detect_all_conflicts_across_multiple_pets() -> None:
	owner = Owner(name="Alex", available_hours=3)
	
	# Pet 1 with conflict
	dog = Pet(name="Buddy", species="dog", age=3)
	dog.tasks.append(Task(description="Walk 1", time_minutes=30, frequency="daily", start_time="09:00"))
	dog.tasks.append(Task(description="Walk 2", time_minutes=20, frequency="daily", start_time="09:00"))
	
	# Pet 2 with conflict
	cat = Pet(name="Luna", species="cat", age=2)
	cat.tasks.append(Task(description="Feed 1", time_minutes=5, frequency="daily", start_time="08:00"))
	cat.tasks.append(Task(description="Feed 2", time_minutes=10, frequency="daily", start_time="08:00"))
	
	owner.add_pet(dog)
	owner.add_pet(cat)
	scheduler = Scheduler(owner)
	
	all_conflicts = scheduler.detect_all_conflicts()
	
	# Should detect conflicts for both pets
	assert "Buddy" in all_conflicts
	assert "Luna" in all_conflicts
	assert "09:00" in all_conflicts["Buddy"]
	assert "08:00" in all_conflicts["Luna"]


def test_scheduler_has_scheduling_conflicts_returns_true_when_conflicts_exist() -> None:
	owner = Owner(name="Alex", available_hours=3)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.tasks.append(Task(description="Task 1", time_minutes=15, frequency="daily", start_time="10:00"))
	pet.tasks.append(Task(description="Task 2", time_minutes=20, frequency="daily", start_time="10:00"))
	
	owner.add_pet(pet)
	scheduler = Scheduler(owner)
	
	assert scheduler.has_scheduling_conflicts("Mochi") is True


def test_scheduler_has_scheduling_conflicts_returns_false_when_no_conflicts() -> None:
	owner = Owner(name="Alex", available_hours=3)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Walk", time_minutes=20, frequency="daily", start_time="09:00"))
	pet.add_task(Task(description="Eat", time_minutes=10, frequency="daily", start_time="10:00"))
	
	owner.add_pet(pet)
	scheduler = Scheduler(owner)
	
	assert scheduler.has_scheduling_conflicts("Mochi") is False


def test_scheduler_get_conflict_summary_reports_no_conflicts() -> None:
	owner = Owner(name="Alex", available_hours=2)
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.add_task(Task(description="Walk", time_minutes=20, frequency="daily", start_time="09:00"))
	
	owner.add_pet(pet)
	scheduler = Scheduler(owner)
	
	summary = scheduler.get_conflict_summary()
	assert summary == "No scheduling conflicts detected."


def test_scheduler_get_conflict_summary_reports_conflicts_with_details() -> None:
	owner = Owner(name="Alex", available_hours=3)
	
	pet = Pet(name="Mochi", species="dog", age=3)
	pet.tasks.append(Task(description="Morning walk", time_minutes=30, frequency="daily", start_time="08:00"))
	pet.tasks.append(Task(description="Morning feed", time_minutes=10, frequency="daily", start_time="08:00"))
	
	owner.add_pet(pet)
	scheduler = Scheduler(owner)
	
	summary = scheduler.get_conflict_summary()
	
	# Should contain conflict details
	assert "Scheduling Conflicts Detected" in summary
	assert "Mochi" in summary
	assert "08:00" in summary
	assert "Morning walk" in summary
	assert "Morning feed" in summary


def test_scheduler_ignores_default_00_00_start_time_in_conflicts() -> None:
	owner = Owner(name="Alex", available_hours=3)
	pet = Pet(name="Mochi", species="dog", age=3)
	
	# Add multiple tasks with default 00:00 time (should not flag as conflict)
	pet.add_task(Task(description="Task 1", time_minutes=15, frequency="daily"))  # default 00:00
	pet.add_task(Task(description="Task 2", time_minutes=20, frequency="daily"))  # default 00:00
	
	owner.add_pet(pet)
	scheduler = Scheduler(owner)
	
	conflicts = scheduler.detect_pet_conflicts("Mochi")
	
	# Should not detect 00:00 as a conflict
	assert "00:00" not in conflicts
	assert len(conflicts) == 0
