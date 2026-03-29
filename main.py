from pawpal_system import Task, Pet, Owner, Scheduler


def print_header(title: str, width: int = 76) -> None:
	line = "=" * width
	print(line)
	print(f"{title:^{width}}")
	print(line)


def print_kv(label: str, value: str, label_width: int = 18) -> None:
	print(f"{label:<{label_width}}: {value}")


def print_tasks_table(tasks: list[Task], title: str, width: int = 76) -> int:
	print(f"\n{title}")
	print("-" * width)
	print(f"{'#':<3} {'Task':<34} {'Min':>5} {'Frequency':<20} {'Status':<8}")
	print("-" * width)

	total_minutes = 0
	for index, task in enumerate(tasks, start=1):
		status = "Done" if task.is_completed else "Pending"
		print(f"{index:<3} {task.description[:34]:<34} {task.time_minutes:>5} {task.frequency[:20]:<20} {status:<8}")
		total_minutes += task.time_minutes

	if not tasks:
		print("(no tasks)")

	print("-" * width)
	return total_minutes

# Create an owner
owner = Owner("Alice", available_hours=5.0)

# Create pets
dog = Pet(name="Buddy", species="dog", age=3)
cat = Pet(name="Whiskers", species="cat", age=2)

# Add pets to owner
owner.add_pet(dog)
owner.add_pet(cat)

# Create tasks
walk_task = Task(description="Walk in the park", time_minutes=30, frequency="daily")
feed_task = Task(description="Feed the pet", time_minutes=10, frequency="twice daily")
play_task = Task(description="Play with toys", time_minutes=20, frequency="daily")
groom_task = Task(description="Brush fur", time_minutes=15, frequency="weekly")
medical_task = Task(description="Go to the medical treatment", time_minutes=45, frequency="monthly")

# Add tasks to Buddy (dog)
dog.add_task(walk_task)
dog.add_task(feed_task)
dog.add_task(play_task)
dog.add_task(medical_task)

# Add tasks to Whiskers (cat)
cat.add_task(feed_task)
cat.add_task(groom_task)
cat.add_task(play_task)
cat.add_task(medical_task)

# Create a scheduler and print today's schedule
scheduler = Scheduler(owner)

available_minutes = int(owner.available_hours * 60)
print_header(f"PAWPAL SCHEDULE FOR {owner.name.upper()}")
print_kv("Available Hours", f"{owner.available_hours:.1f} h ({available_minutes} min)")

# Print organized tasks
organized_tasks = scheduler.organize_tasks(include_completed=False)
pending_total = print_tasks_table(organized_tasks, "ALL PENDING TASKS (PRIORITY ORDER)")
print_kv("Total Needed", f"{pending_total} min ({pending_total / 60:.1f} h)")

# Print daily plan
plan = scheduler.generate_plan()
plan_minutes = print_tasks_table(plan, "TODAY'S PLAN (WITHIN AVAILABLE TIME)")
remaining_minutes = available_minutes - plan_minutes

print_kv("Total Scheduled", f"{plan_minutes} min ({plan_minutes / 60:.1f} h)")
print_kv("Remaining Time", f"{remaining_minutes} min")
print("=" * 76)

