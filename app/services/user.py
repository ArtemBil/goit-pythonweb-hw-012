"""User domain service wrappers around repository operations."""

class UserService:
    def __init__(self, repository):
        """Initialize user service with a repository dependency."""
        self.repository = repository

    async def confirmed_email(self, email: str, db):
        """Mark user email as confirmed using repository.

        Args:
            email: User email address.
            db: Database session.
        """
        return await self.repository.confirm_email(email, db)
