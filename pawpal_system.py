"""Core classes for PawPal scheduling logic."""

from __future__ import annotations

from datetime import date, timedelta
from dataclasses import dataclass, field
import re


@dataclass
class Task:
	description: str
	time_minutes: int
	frequency: str
	due_date: date = field(default_factory=date.today)
	start_time : str = field(default="00:00")
	is_completed: bool = False
	_parent_pet: Pet | None = field(default=None, init=False, repr=False)

	@property
	def time(self) -> str:
		"""Return task duration in HH:MM format for string-based sorting/display."""
		hours, minutes = divmod(self.time_minutes, 60)
		return f"{hours:02d}:{minutes:02d}"

	def __post_init__(self) -> None:
		# Core behavior 1: validate and normalize task inputs.
		"""Validate and normalize task fields after initialization."""
		description = self.description.strip()
		if not description:
			raise ValueError("Task description cannot be empty.")
		if self.time_minutes <= 0:
			raise ValueError("Task time must be greater than 0 minutes.")
		frequency = self.frequency.strip().lower()
		if not frequency:
			raise ValueError("Task frequency cannot be empty.")
		start_time = self.start_time.strip()
		if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
			raise ValueError("Task start time must be in HH:MM format (24-hour).")

		self.description = description
		self.frequency = frequency
		self.start_time = start_time

	def mark_completed(self) -> None:
		# Core behavior 2: lifecycle updates plus recurring task rollover.
		"""Mark this task completed and enqueue the next recurring instance when relevant."""
		if self.is_completed:
			return
		self.is_completed = True

		normalized_frequency = self.frequency.strip().lower()
		next_due_date: date | None = None
		if normalized_frequency == "daily":
			next_due_date = date.today() + timedelta(days=1)
		elif normalized_frequency == "weekly":
			next_due_date = date.today() + timedelta(days=7)
		else:
			return

		if self._parent_pet is None:
			return

		already_pending = any(
			not existing_task.is_completed
			and existing_task is not self
			and existing_task.description.strip().lower() == self.description.strip().lower()
			and existing_task.frequency.strip().lower() == normalized_frequency
			for existing_task in self._parent_pet.tasks
		)
		if already_pending:
			return

		next_task = Task(
			description=self.description,
			time_minutes=self.time_minutes,
			frequency=self.frequency,
			due_date=next_due_date,
			start_time=self.start_time,
		)
		self._parent_pet.add_task(next_task)

	def mark_complition(self) -> None:
		"""Backward-compatible alias for marking a task completed."""
		self.mark_completed()

	def mark_incomplete(self) -> None:
		"""Mark this task as incomplete."""
		self.is_completed = False

	def get_info(self) -> dict[str, str | int | bool]:
		"""Return task details as a serializable dictionary."""
		return {
			"description": self.description,
			"time_minutes": self.time_minutes,
			"frequency": self.frequency,
			"due_date": self.due_date.isoformat(),
			"is_completed": self.is_completed,
		}


@dataclass
class Pet:
	name: str
	species: str
	age: int
	tasks: list[Task] = field(default_factory=list)

	def __post_init__(self) -> None:
		"""Validate and normalize pet fields after initialization."""
		if self.age < 0:
			raise ValueError("Pet age cannot be negative.")
		self.name = self.name.strip()
		self.species = self.species.strip().lower()

	def get_info(self) -> dict[str, str | int]:
		"""Return pet details as a serializable dictionary."""
		return {
			"name": self.name,
			"species": self.species,
			"age": self.age,
		}

	def update_info(self, name: str, species: str, age: int) -> None:
		"""Update pet identity fields with normalized values."""
		if age < 0:
			raise ValueError("Pet age cannot be negative.")
		self.name = name.strip()
		self.species = species.strip().lower()
		self.age = age

	def add_task(self, task: Task) -> None:
		# Core behavior 3: prevent duplicate tasks and time conflicts for a pet.
		"""Attach a new task to this pet, preventing duplicate/conflicting pending tasks."""
		normalized_description = task.description.strip().lower()
		normalized_frequency = task.frequency.strip().lower()
		normalized_start_time = task.start_time.strip()
		for existing_task in self.tasks:
			if (
				not existing_task.is_completed
				and existing_task.description.strip().lower() == normalized_description
				and existing_task.frequency.strip().lower() == normalized_frequency
			):
				raise ValueError(
					f"Task '{task.description}' ({task.frequency}) already exists for pet '{self.name}'."
				)

			# Treat 00:00 as the default placeholder; enforce conflict checks for explicit times.
			if (
				not existing_task.is_completed
				and normalized_start_time != "00:00"
				and existing_task.start_time.strip() == normalized_start_time
				and existing_task.due_date == task.due_date
			):
				raise ValueError(
					f"Pet '{self.name}' already has an incomplete task at {task.start_time} on {task.due_date.isoformat()}."
				)
		task._parent_pet = self
		self.tasks.append(task)

	def remove_task(self, description: str) -> None:
		"""Remove the first task that matches the given description."""
		normalized = description.strip().lower()
		for index, task in enumerate(self.tasks):
			if task.description.lower() == normalized:
				del self.tasks[index]
				return
		raise ValueError(f"Task '{description}' was not found for pet '{self.name}'.")

	def get_tasks(self, include_completed: bool = True) -> list[Task]:
		"""Return this pet's tasks, optionally excluding completed ones."""
		if include_completed:
			return list(self.tasks)
		return [task for task in self.tasks if not task.is_completed]

	def mark_task_complete(self, description: str, frequency: str | None = None) -> Task:
		"""Mark a pending task complete by description and optional frequency.

		When frequency is omitted, the first pending description match is completed.
		If multiple pending tasks share a description and no frequency is provided,
		raise a ValueError so callers can disambiguate explicitly.
		"""
		normalized_description = description.strip().lower()
		normalized_frequency = frequency.strip().lower() if frequency is not None else None

		matching_pending = [
			task
			for task in self.tasks
			if not task.is_completed
			and task.description.strip().lower() == normalized_description
			and (
				normalized_frequency is None
				or task.frequency.strip().lower() == normalized_frequency
			)
		]

		if not matching_pending:
			if normalized_frequency is None:
				raise ValueError(f"No pending task '{description}' was found for pet '{self.name}'.")
			raise ValueError(
				f"No pending task '{description}' with frequency '{frequency}' was found for pet '{self.name}'."
			)

		if normalized_frequency is None and len(matching_pending) > 1:
			raise ValueError(
				f"Multiple pending tasks named '{description}' exist for pet '{self.name}'. "
				"Provide frequency to disambiguate."
			)

		task_to_complete = matching_pending[0]
		task_to_complete.mark_completed()
		return task_to_complete


class Owner:
	def __init__(self, name: str, available_hours: float = 0.0, preferences: dict[str, str] | None = None):
		"""Initialize an owner profile with optional availability and preferences."""
		if available_hours < 0:
			raise ValueError("Available hours cannot be negative.")
		self.name = name
		self.available_hours = available_hours
		self.preferences = dict(preferences or {})
		self.pets: list[Pet] = []

	def add_pet(self, pet: Pet) -> None:
		"""Add a pet to this owner, preventing duplicate pet names."""
		if any(existing_pet.name.lower() == pet.name.lower() for existing_pet in self.pets):
			raise ValueError(f"Pet '{pet.name}' already exists for owner '{self.name}'.")
		self.pets.append(pet)

	def remove_pet(self, pet_name: str) -> None:
		"""Remove a pet by name from this owner's list."""
		normalized = pet_name.strip().lower()
		for index, pet in enumerate(self.pets):
			if pet.name.lower() == normalized:
				del self.pets[index]
				return
		raise ValueError(f"Pet '{pet_name}' was not found.")

	def get_pet(self, pet_name: str) -> Pet:
		"""Return a pet by name, or raise if no match exists."""
		normalized = pet_name.strip().lower()
		for pet in self.pets:
			if pet.name.lower() == normalized:
				return pet
		raise ValueError(f"Pet '{pet_name}' was not found.")

	def set_preferences(self, preferences: dict[str, str]) -> None:
		"""Replace owner preferences with a new mapping."""
		self.preferences = dict(preferences)

	def check_availability(self, required_minutes: int) -> bool:
		"""Check whether required minutes fit within available owner time."""
		if required_minutes < 0:
			raise ValueError("Required minutes cannot be negative.")
		available_minutes = int(self.available_hours * 60)
		return required_minutes <= available_minutes

	def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
		"""Collect tasks from all pets, with optional completion filtering."""
		all_tasks: list[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.get_tasks(include_completed=include_completed))
		return all_tasks


class Scheduler:
	def __init__(self, owner: Owner):
		"""Create a scheduler bound to a specific owner."""
		self.owner = owner
		self._frequency_weights: dict[str, int] = {
			"daily": 3,
			"twice daily": 4,
			"weekly": 2,
			"monthly": 1,
		}

	def _get_frequency_weight(self, frequency: str) -> int:
		"""Return a weight for a frequency string, with safe fallbacks for custom values."""
		normalized = frequency.strip().lower()
		if normalized in self._frequency_weights:
			return self._frequency_weights[normalized]
		if "daily" in normalized:
			return 3
		if "weekly" in normalized:
			return 2
		if "monthly" in normalized:
			return 1
		return 1

	def _task_priority_score(self, task: Task) -> float:
		"""Compute a small heuristic score so urgent frequent tasks rank earlier."""
		if task.is_completed:
			return -1.0

		frequency_component = float(self._get_frequency_weight(task.frequency) * 10)
		duration_component = max(0.0, 15.0 - float(task.time_minutes)) / 10.0
		return frequency_component + duration_component

	def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
		"""Return all owner tasks, optionally excluding completed ones."""
		return self.owner.get_all_tasks(include_completed=include_completed)

	def get_tasks_by_pet(self) -> dict[str, list[Task]]:
		"""Return tasks grouped by pet name."""
		return {pet.name: pet.get_tasks(include_completed=True) for pet in self.owner.pets}

	def filter_tasks(self, is_completed: bool | None = None, pet_name: str | None = None) -> list[Task]:
		"""Filter tasks by optional completion status and/or pet name."""
		if pet_name is not None:
			base_tasks = self.owner.get_pet(pet_name).get_tasks(include_completed=True)
		else:
			base_tasks = self.get_all_tasks(include_completed=True)

		if is_completed is None:
			return list(base_tasks)

		return [task for task in base_tasks if task.is_completed is is_completed]

	def add_task_to_pet(self, pet_name: str, task: Task) -> None:
		"""Add a task to the named pet."""
		pet = self.owner.get_pet(pet_name)
		pet.add_task(task)

	def remove_task_from_pet(self, pet_name: str, task_description: str) -> None:
		"""Remove a task from the named pet by description."""
		pet = self.owner.get_pet(pet_name)
		pet.remove_task(task_description)

	def mark_task_complete(self, pet_name: str, task_description: str, frequency: str | None = None) -> Task:
		"""Mark one pending pet task complete, optionally filtered by frequency."""
		pet = self.owner.get_pet(pet_name)
		return pet.mark_task_complete(task_description, frequency=frequency)

	def organize_tasks(self, include_completed: bool = False) -> list[Task]:
		"""Order tasks by completion, then score, then shorter tasks, then alphabetically."""
		all_tasks = self.get_all_tasks(include_completed=include_completed)
		return sorted(
			all_tasks,
			key=lambda task: (
				int(task.is_completed),
				-self._task_priority_score(task),
				task.time_minutes,
				task.frequency,
				task.description.lower(),
			),
		)

	def sort_by_time(self, include_completed: bool = True, descending: bool = False) -> list[Task]:
		"""Return tasks sorted by HH:MM time using a lambda key."""
		tasks = self.get_all_tasks(include_completed=include_completed)
		return sorted(
			tasks,
			key=lambda task: tuple(map(int, task.time.split(":"))),
			reverse=descending,
		)

	def generate_plan(self, max_minutes: int | None = None) -> list[Task]:
		# Core behavior 4: build a practical schedule within available time.
		"""Build a balanced daily plan with quick wins and per-pet fairness."""
		if max_minutes is not None and max_minutes < 0:
			raise ValueError("Max minutes cannot be negative.")

		available_minutes = int(self.owner.available_hours * 60)
		effective_limit = available_minutes if max_minutes is None else min(available_minutes, max_minutes)
		if effective_limit <= 0:
			return []

		pending_sorted = self.organize_tasks(include_completed=False)
		plan: list[Task] = []
		selected_task_ids: set[int] = set()
		total_minutes = 0

		# Quick-win phase: reserve a small portion of budget for short tasks first.
		quick_win_limit = max(1, int(effective_limit * 0.2))
		short_candidates = [task for task in pending_sorted if task.time_minutes <= 10]
		for task in short_candidates:
			if total_minutes >= quick_win_limit:
				break
			if total_minutes + task.time_minutes <= effective_limit and id(task) not in selected_task_ids:
				self._add_to_plan(plan, selected_task_ids, task)
				total_minutes += task.time_minutes

		# Fairness phase: round-robin by pet so one pet does not consume the whole plan.
		pet_task_queues: dict[str, list[Task]] = {}
		for pet in self.owner.pets:
			pet_pending = [task for task in pet.get_tasks(include_completed=False) if id(task) not in selected_task_ids]
			pet_task_queues[pet.name] = sorted(
				pet_pending,
				key=lambda task: (
					-self._task_priority_score(task),
					task.time_minutes,
					task.description.lower(),
				),
			)

		pet_names = [pet.name for pet in self.owner.pets]
		made_progress = True
		while made_progress and total_minutes < effective_limit:
			made_progress = False
			for pet_name in pet_names:
				queue = pet_task_queues.get(pet_name, [])
				while queue and id(queue[0]) in selected_task_ids:
					queue.pop(0)
				if not queue:
					continue
				next_task = queue[0]
				if total_minutes + next_task.time_minutes <= effective_limit:
					self._add_to_plan(plan, selected_task_ids, next_task)
					total_minutes += next_task.time_minutes
					queue.pop(0)
					made_progress = True
				else:
					queue.pop(0)

		# Final fill: use remaining highest-value tasks that can still fit.
		if total_minutes < effective_limit:
			for task in pending_sorted:
				if id(task) in selected_task_ids:
					continue
				if total_minutes + task.time_minutes <= effective_limit:
					self._add_to_plan(plan, selected_task_ids, task)
					total_minutes += task.time_minutes
		return plan

	def _add_to_plan(self, plan: list[Task], selected: set[int], task: Task) -> None:
		"""Add task to plan and mark as selected to avoid duplicates."""
		plan.append(task)
		selected.add(id(task))

	def get_tasks_at_time(self, time: str) -> list[Task]:
		"""Return all tasks scheduled for a specific HH:MM time across all pets."""
		all_tasks = self.get_all_tasks(include_completed=True)
		return [task for task in all_tasks if task.start_time == time]

	def detect_pet_conflicts(self, pet_name: str) -> dict[str, list[Task]]:
		"""Find time conflicts within a single pet's pending tasks.
		
		Returns a dict mapping HH:MM times to lists of tasks scheduled at that time.
		Only includes times with multiple tasks (actual conflicts) and excludes the default 00:00.
		"""
		pet = self.owner.get_pet(pet_name)
		tasks = pet.get_tasks(include_completed=False)
		time_groups: dict[str, list[Task]] = {}
		for task in tasks:
			if task.start_time != "00:00":
				if task.start_time not in time_groups:
					time_groups[task.start_time] = []
				time_groups[task.start_time].append(task)
		return {time: tasks for time, tasks in time_groups.items() if len(tasks) > 1}

	def detect_all_conflicts(self) -> dict[str, dict[str, list[Task]]]:
		"""Find all scheduling conflicts across all pets.
		
		Returns a nested dict mapping pet names to their conflict dictionaries,
		where each conflict dict maps HH:MM times to lists of conflicting tasks.
		"""
		conflicts: dict[str, dict[str, list[Task]]] = {}
		for pet in self.owner.pets:
			pet_conflicts = self.detect_pet_conflicts(pet.name)
			if pet_conflicts:
				conflicts[pet.name] = pet_conflicts
		return conflicts

	def has_scheduling_conflicts(self, pet_name: str) -> bool:
		"""Return True if the named pet has any pending task time conflicts."""
		return bool(self.detect_pet_conflicts(pet_name))

	def get_conflict_summary(self) -> str:
		"""Generate a human-readable report of all scheduling conflicts, or a message if none exist."""
		conflicts = self.detect_all_conflicts()
		if not conflicts:
			return "No scheduling conflicts detected."
		summary = "Scheduling Conflicts Detected:\n"
		for pet_name, pet_conflicts in conflicts.items():
			summary += f"\n{pet_name}:\n"
			for time, tasks in pet_conflicts.items():
				summary += f"  {time}: {len(tasks)} tasks\n"
				for task in tasks:
					summary += f"    - {task.description}\n"
		return summary

