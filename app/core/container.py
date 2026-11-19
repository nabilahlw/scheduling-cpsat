"""Container dependency (dependency injection sederhana).

Semua objek dibuat malas (lazy) saat pertama dipakai, jadi `import app.main`
tidak membaca .env sampai ada request / skrip yang benar-benar butuh.
"""
from functools import cached_property

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.security import PasswordHasher, TokenService


class Container:
    @cached_property
    def settings(self) -> Settings:
        return get_settings()

    @cached_property
    def db(self) -> Database:
        return Database(self.settings.database_url)

    @cached_property
    def hasher(self) -> PasswordHasher:
        return PasswordHasher(self.settings.pbkdf2_iterations)

    @cached_property
    def tokens(self) -> TokenService:
        return TokenService(self.settings.secret_key, self.settings.token_expire_minutes)

    @cached_property
    def conflicts(self):
        from app.services.conflict_checker import ConflictChecker
        return ConflictChecker(self.settings.travel_buffer)

    @cached_property
    def solver(self):
        from app.solver.scheduler import ScheduleSolver
        return ScheduleSolver(self.settings.travel_buffer, self.settings.max_solve_seconds)

    @cached_property
    def auth(self):
        from app.services.auth_service import AuthService
        return AuthService(self.db, self.hasher, self.tokens)

    @cached_property
    def users(self):
        from app.services.user_service import UserService
        return UserService(self.db, self.hasher)

    @cached_property
    def teachers(self):
        from app.services.teacher_service import TeacherService
        return TeacherService(self.db)

    @cached_property
    def schools(self):
        from app.services.school_service import SchoolService
        return SchoolService(self.db)

    @cached_property
    def availability(self):
        from app.services.availability_service import AvailabilityService
        return AvailabilityService(self.db, self.conflicts)

    @cached_property
    def schedule(self):
        from app.services.schedule_service import ScheduleService
        return ScheduleService(self.db, self.conflicts)

    @cached_property
    def generation(self):
        from app.services.generation_service import GenerationService
        return GenerationService(self.teachers, self.availability, self.schedule, self.solver)

    @cached_property
    def invoices(self):
        from app.services.invoice_service import InvoiceService
        return InvoiceService(self.db)


container = Container()
