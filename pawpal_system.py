"""Core classes for PawPal scheduling logic."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
	description: str
	time_minutes: int
	frequency: str
	is_completed: bool = False

	def __post_init__(self) -> None:
		"""Validate and normalize task fields after initialization."""
		description = self.description.strip()
		if not description:
			raise ValueError("Task description cannot be empty.")
		if self.time_minutes <= 0:
			raise ValueError("Task time must be greater than 0 minutes.")
		frequency = self.frequency.strip().lower()
		if not frequency:
			raise ValueError("Task frequency cannot be empty.")

		self.description = description
		self.frequency = frequency

	def mark_completed(self) -> None:
		"""Mark this task as completed."""
		self.is_completed = True

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
		"""Attach a new task to this pet."""
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

	def get_all_tasks(self, include_completed: bool = True) -> list[Task]:
		"""Return all owner tasks, optionally excluding completed ones."""
		return self.owner.get_all_tasks(include_completed=include_completed)

	def get_tasks_by_pet(self) -> dict[str, list[Task]]:
		"""Return tasks grouped by pet name."""
		return {pet.name: pet.get_tasks(include_completed=True) for pet in self.owner.pets}

	def add_task_to_pet(self, pet_name: str, task: Task) -> None:
		"""Add a task to the named pet."""
		pet = self.owner.get_pet(pet_name)
		pet.add_task(task)

	def remove_task_from_pet(self, pet_name: str, task_description: str) -> None:
		"""Remove a task from the named pet by description."""
		pet = self.owner.get_pet(pet_name)
		pet.remove_task(task_description)

	def organize_tasks(self, include_completed: bool = False) -> list[Task]:
		"""Order tasks so pending tasks come first, then shorter tasks, then alphabetically."""
		all_tasks = self.get_all_tasks(include_completed=include_completed)
		return sorted(
			all_tasks,
			key=lambda task: (
				int(task.is_completed),
				task.time_minutes,
				task.frequency,
				task.description.lower(),
			),
		)

	def generate_plan(self, max_minutes: int | None = None) -> list[Task]:
		"""Build a simple daily plan across all pets within the allowed time budget."""
		if max_minutes is not None and max_minutes < 0:
			raise ValueError("Max minutes cannot be negative.")

		available_minutes = int(self.owner.available_hours * 60)
		effective_limit = available_minutes if max_minutes is None else min(available_minutes, max_minutes)

		plan: list[Task] = []
		total_minutes = 0
		for task in self.organize_tasks(include_completed=False):
			if total_minutes + task.time_minutes <= effective_limit:
				plan.append(task)
				total_minutes += task.time_minutes
		return plan

