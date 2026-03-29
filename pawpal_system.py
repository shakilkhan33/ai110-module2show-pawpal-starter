from dataclasses import dataclass
from typing import Any


VALID_PRIORITIES = {"low", "medium", "high"}
PRIORITY_WEIGHT = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Pet:
	name: str
	species: str
	age: int

	def get_info(self) -> dict[str, Any]:
		return {"name": self.name, "species": self.species, "age": self.age}

	def update_info(self, name: str, species: str, age: int) -> None:
		if age < 0:
			raise ValueError("Pet age cannot be negative")
		self.name = name
		self.species = species
		self.age = age


class Owner:
	def __init__(
		self,
		name: str,
		available_hours: float,
		preferences: dict[str, Any] | None = None,
	) -> None:
		if available_hours < 0:
			raise ValueError("available_hours cannot be negative")
		self.name = name
		self.available_hours = available_hours
		self.preferences = preferences or {}
		self.pets: list[Pet] = []
		self.tasks: list[Task] = []

	def add_pet(self, pet: Pet) -> None:
		self.pets.append(pet)

	def add_task(self, task: "Task") -> None:
		self.tasks.append(task)

	def set_preferences(self, preferences: dict[str, Any]) -> None:
		self.preferences = preferences.copy()

	def check_availability(self, required_minutes: int) -> bool:
		if required_minutes < 0:
			raise ValueError("required_minutes cannot be negative")
		available_minutes = int(self.available_hours * 60)
		return required_minutes <= available_minutes


@dataclass
class Task:
	title: str
	duration_minutes: int
	priority: str

	def __post_init__(self) -> None:
		if self.duration_minutes <= 0:
			raise ValueError("duration_minutes must be greater than 0")
		self.priority = self._normalize_priority(self.priority)

	@staticmethod
	def _normalize_priority(priority: str) -> str:
		normalized = priority.strip().lower()
		if normalized not in VALID_PRIORITIES:
			raise ValueError("priority must be one of: low, medium, high")
		return normalized

	def update_priority(self, priority: str) -> None:
		self.priority = self._normalize_priority(priority)

	def is_high_priority(self) -> bool:
		return self.priority == "high"


class Scheduler:
	def __init__(self, owner: Owner, pet: Pet, max_daily_minutes: int) -> None:
		if max_daily_minutes <= 0:
			raise ValueError("max_daily_minutes must be greater than 0")
		self.owner = owner
		self.pet = pet
		if pet not in self.owner.pets:
			self.owner.add_pet(pet)
		self.tasks = self.owner.tasks
		self.max_daily_minutes = max_daily_minutes

	def _effective_daily_minutes(self) -> int:
		owner_limit = int(self.owner.available_hours * 60)
		return min(owner_limit, self.max_daily_minutes)

	def add_task(self, task: Task) -> None:
		self.owner.add_task(task)

	def remove_task(self, task_title: str) -> None:
		for index, task in enumerate(self.tasks):
			if task.title == task_title:
				del self.tasks[index]
				return
		raise ValueError(f"Task '{task_title}' not found")

	def prioritize_tasks(self) -> list[Task]:
		def task_sort_key(task: Task) -> tuple[int, int, str]:
			return (
				PRIORITY_WEIGHT[task.priority],
				task.duration_minutes,
				task.title.lower(),
			)

		return sorted(self.tasks, key=task_sort_key)

	def generate_plan(self) -> list[Task]:
		daily_limit = self._effective_daily_minutes()
		selected_tasks: list[Task] = []
		used_minutes = 0

		for task in self.prioritize_tasks():
			candidate_total = used_minutes + task.duration_minutes
			if candidate_total <= daily_limit:
				selected_tasks.append(task)
				used_minutes = candidate_total

		return selected_tasks
